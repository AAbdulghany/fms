"""Invoice line computation from merged work-order + report data."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from sqlalchemy import select

from app.core.security import hash_password
from app.models import (
    Asset,
    Client,
    Contract,
    MaintenanceReport,
    Part,
    PricingProfile,
    ReportStatus,
    ReportTemplate,
    Site,
    Tenant,
    User,
    UserRole,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.services.billing import (
    _compute_invoice_lines,
    apply_invoice_charge_edits,
    build_invoice_for_work_order,
    preview_invoice_for_work_order,
)
from app.services.billing_setup import ensure_client_active_contract


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="Invoice Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def client_a(db_session, tenant):
    c = Client(id=uuid4(), tenant_id=tenant.id, legal_name="Acme FM", code="ACME")
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture
def site_a(db_session, tenant, client_a):
    s = Site(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client_a.id,
        name="Tower A",
        address_json={"address": "123 Main", "city": "Riyadh", "country": "SA"},
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture
def asset_a(db_session, tenant, site_a):
    a = Asset(
        id=uuid4(),
        tenant_id=tenant.id,
        site_id=site_a.id,
        name="Chiller-01",
        label_code="CH-01",
        category="hvac",
    )
    db_session.add(a)
    db_session.commit()
    return a


@pytest.fixture
def technician(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="tech@invoice.test",
        password_hash=hash_password("x"),
        full_name="Sara Tech",
        role=UserRole.technician,
        is_active=True,
        phone="+966500000000",
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def template(db_session, tenant):
    tmpl = ReportTemplate(
        id=uuid4(),
        tenant_id=tenant.id,
        name="STD",
        code="STD",
        version=2,
        schema_json={"sections": []},
        maintenance_types=[],
    )
    db_session.add(tmpl)
    db_session.commit()
    return tmpl


@pytest.fixture
def pricing(db_session, tenant):
    p = PricingProfile(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Default",
        hourly_rate_sar=Decimal("150"),
        parts_markup_percent=Decimal("10"),
        default_service_fee_sar=Decimal("75"),
        emergency_surcharge_percent=Decimal("25"),
    )
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture
def contract(db_session, tenant, client_a, pricing):
    ensure_client_active_contract(db_session, tenant.id, client_a.id)
    return db_session.scalar(select(Contract).where(Contract.client_id == client_a.id))


@pytest.fixture
def verified_wo(db_session, tenant, client_a, site_a, asset_a, technician, template, contract):
    opened = datetime(2026, 6, 22, 9, 0, tzinfo=timezone.utc)
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client_a.id,
        site_id=site_a.id,
        asset_id=asset_a.id,
        template_id=template.id,
        assignee_user_id=technician.id,
        status=WorkOrderStatus.verified,
        source=WorkOrderSource.corrective,
        title="Corrective HVAC check",
        description="Fallback description",
        opened_at=opened,
    )
    db_session.add(wo)
    db_session.flush()
    report = MaintenanceReport(
        id=uuid4(),
        tenant_id=tenant.id,
        work_order_id=wo.id,
        template_id=template.id,
        template_version=2,
        status=ReportStatus.approved,
        answers_json={
            "inspection_end_time": "11:30",
            "findings_defects": "Filter clogged; replaced gasket.",
            "parts_used": [{"sku": "FLT-100", "quantity": 2}],
        },
        template_snapshot_json={},
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(wo)
    return wo


def test_invoice_uses_elapsed_hours_and_findings(db_session, verified_wo, pricing):
    from sqlalchemy.orm import joinedload

    wo = db_session.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == verified_wo.id)
        .options(
            joinedload(WorkOrder.assignee_user),
            joinedload(WorkOrder.site),
            joinedload(WorkOrder.asset),
        )
    ).first()
    part = Part(
        id=uuid4(),
        tenant_id=verified_wo.tenant_id,
        sku="FLT-100",
        name="Air filter",
        unit_cost_sar=Decimal("20"),
    )
    db_session.add(part)
    db_session.commit()

    computed = _compute_invoice_lines(db_session, wo, wo.report)

    assert computed["labor_hours"] == Decimal("2.50")
    assert computed["work_summary"] == "Filter clogged; replaced gasket."

    labor_line = next(p for p in computed["line_payloads"] if p["line_type"] == "labor")
    assert "Corrective HVAC check" in labor_line["description"]
    assert "Chiller-01" in labor_line["description"]
    assert "Tower A" in labor_line["description"]

    fee_line = next(p for p in computed["line_payloads"] if p["line_type"] == "fee")
    assert "Corrective" in fee_line["description"]

    parts_line = next(p for p in computed["line_payloads"] if p["line_type"] == "parts")
    assert "Air filter" in parts_line["description"]


def test_preview_invoice_for_work_order(db_session, verified_wo):
    from sqlalchemy.orm import joinedload

    wo = db_session.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == verified_wo.id)
        .options(joinedload(WorkOrder.assignee_user), joinedload(WorkOrder.report))
    ).first()
    preview = preview_invoice_for_work_order(db_session, wo)
    assert preview["labor_hours"] > 0
    assert preview["labor_rate_sar"] > 0
    assert preview["total_sar"] == preview["subtotal_sar"]
    assert preview["work_summary"]


def test_apply_invoice_charge_edits(db_session, verified_wo):
    from sqlalchemy.orm import joinedload

    wo = db_session.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == verified_wo.id)
        .options(joinedload(WorkOrder.assignee_user), joinedload(WorkOrder.report))
    ).first()
    inv = build_invoice_for_work_order(db_session, wo)
    db_session.commit()
    db_session.refresh(inv)
    _ = inv.line_items

    apply_invoice_charge_edits(
        inv,
        labor_hours=Decimal("4"),
        labor_rate_sar=Decimal("200"),
        service_fee_sar=Decimal("50"),
    )
    db_session.commit()
    db_session.refresh(inv)

    labor_li = next(li for li in inv.line_items if li.line_type == "labor")
    fee_li = next(li for li in inv.line_items if li.line_type == "fee")
    assert labor_li.quantity == Decimal("4")
    assert labor_li.unit_price_sar == Decimal("200")
    assert labor_li.amount_sar == Decimal("800.00")
    assert fee_li.amount_sar == Decimal("50.00")
    assert inv.subtotal_sar >= Decimal("850.00")
    assert inv.total_sar == inv.subtotal_sar + inv.tax_sar
