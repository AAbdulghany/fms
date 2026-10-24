"""A3 — WorkOrderPart catalog lines (U-PART-01..03)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.models import Part, WorkOrder, WorkOrderPart, WorkOrderSource, WorkOrderStatus
from app.services.billing import _parts_lines
from app.services.work_order_parts import add_wo_part, list_wo_parts


def _make_wo(db, tenant_id, client_id, site_id):
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant_id,
        client_id=client_id,
        site_id=site_id,
        title="Fix pump",
        description="leak",
        status=WorkOrderStatus.assigned,
        source=WorkOrderSource.request,
    )
    db.add(wo)
    db.flush()
    return wo


def test_u_part_01_create_part_unique(db_session, sample_tenant):
    p = Part(
        tenant_id=sample_tenant.id,
        sku="FILT-01",
        name="Filter",
        unit_cost_sar=Decimal("100"),
    )
    db_session.add(p)
    db_session.commit()
    assert p.id is not None


def test_u_part_02_attach_and_list(db_session, sample_tenant, sample_client, sample_site):
    part = Part(
        tenant_id=sample_tenant.id,
        sku="BELT-1",
        name="Belt",
        unit_cost_sar=Decimal("50"),
    )
    db_session.add(part)
    wo = _make_wo(db_session, sample_tenant.id, sample_client.id, sample_site.id)
    db_session.commit()
    row = add_wo_part(
        db_session,
        tenant_id=sample_tenant.id,
        work_order=wo,
        part_id=part.id,
        quantity=Decimal("2"),
    )
    db_session.commit()
    listed = list_wo_parts(db_session, sample_tenant.id, wo.id)
    assert len(listed) == 1
    assert listed[0].id == row.id
    assert listed[0].quantity == Decimal("2")


def test_u_part_03_invoice_prefers_wo_parts(db_session, sample_tenant, sample_client, sample_site):
    part = Part(
        tenant_id=sample_tenant.id,
        sku="SEAL",
        name="Seal",
        unit_cost_sar=Decimal("40"),
    )
    db_session.add(part)
    wo = _make_wo(db_session, sample_tenant.id, sample_client.id, sample_site.id)
    db_session.flush()
    db_session.add(
        WorkOrderPart(
            tenant_id=sample_tenant.id,
            work_order_id=wo.id,
            part_id=part.id,
            quantity=Decimal("3"),
            unit_cost_sar=Decimal("40"),
        )
    )
    db_session.commit()
    lines = _parts_lines(
        db_session,
        sample_tenant.id,
        answers={"parts_used": [{"sku": "OTHER", "quantity": 99}]},
        markup_percent=Decimal("0"),
        work_order_id=wo.id,
    )
    assert len(lines) == 1
    assert lines[0]["amount_sar"] == Decimal("120.00")
    assert lines[0]["source_ref"]["field"] == "work_order_parts"
