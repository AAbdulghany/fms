"""Report can be started and submitted while WO is in_progress (before completed)."""

from uuid import uuid4

import pytest
from fastapi import BackgroundTasks

from app.core.security import hash_password
from app.models import (
    Client,
    ReportTemplate,
    Site,
    Tenant,
    User,
    UserRole,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.schemas import ReportAnswersUpdate


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="T", status="active")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def client_a(db_session, tenant):
    c = Client(id=uuid4(), tenant_id=tenant.id, legal_name="C", code="C1")
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture
def site_a(db_session, tenant, client_a):
    s = Site(id=uuid4(), tenant_id=tenant.id, client_id=client_a.id, name="S1")
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture
def technician(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="tech@test.com",
        password_hash=hash_password("x"),
        full_name="Tech",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def template(db_session, tenant):
    tmpl = ReportTemplate(
        id=uuid4(),
        tenant_id=tenant.id,
        name="Inspect",
        code="insp",
        version=1,
        schema_json={"sections": []},
        maintenance_types=[],
    )
    db_session.add(tmpl)
    db_session.commit()
    return tmpl


@pytest.fixture
def wo_in_progress(db_session, tenant, client_a, site_a, technician, template):
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client_a.id,
        site_id=site_a.id,
        template_id=template.id,
        assignee_user_id=technician.id,
        status=WorkOrderStatus.in_progress,
        source=WorkOrderSource.corrective,
        title="Inspect",
    )
    db_session.add(wo)
    db_session.commit()
    return wo


def test_start_report_draft_while_in_progress(db_session, technician, wo_in_progress):
    from app.api.routes.work_orders import upsert_report_draft

    r = upsert_report_draft(
        wo_in_progress.id,
        ReportAnswersUpdate(answers={"note": "ok"}),
        db_session,
        technician,
    )
    assert r.status.value == "draft"
    assert r.answers_json == {"note": "ok"}


def test_cannot_start_report_while_assigned(db_session, technician, wo_in_progress):
    from app.api.routes.work_orders import upsert_report_draft

    wo_in_progress.status = WorkOrderStatus.assigned
    db_session.commit()

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        upsert_report_draft(
            wo_in_progress.id,
            ReportAnswersUpdate(answers={}),
            db_session,
            technician,
        )
    assert exc.value.detail == "REPORT_NOT_ALLOWED_AT_THIS_STATUS"


def test_start_report_assigns_default_template_when_missing(db_session, technician, tenant, client_a, site_a, template):
    from app.api.routes.work_orders import upsert_report_draft

    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client_a.id,
        site_id=site_a.id,
        template_id=None,
        assignee_user_id=technician.id,
        status=WorkOrderStatus.in_progress,
        source=WorkOrderSource.corrective,
        title="No template yet",
    )
    db_session.add(wo)
    db_session.commit()

    r = upsert_report_draft(
        wo.id,
        ReportAnswersUpdate(answers={"note": "started"}),
        db_session,
        technician,
    )
    db_session.refresh(wo)
    assert wo.template_id == template.id
    assert r.status.value == "draft"


def test_report_auto_fill_from_work_order(db_session, technician, wo_in_progress, site_a, client_a):
    from app.models import Asset
    from app.services.report_context import build_report_auto_fill, merge_report_answers

    asset = Asset(
        id=uuid4(),
        tenant_id=wo_in_progress.tenant_id,
        site_id=site_a.id,
        name="Chiller A",
        category="HVAC",
        label_code="HVAC-001",
        serial="SN-99",
    )
    db_session.add(asset)
    wo_in_progress.asset_id = asset.id
    technician.metadata_json = {"job_title": "Lead Tech", "accreditation": "LIC-42"}
    technician.phone = "+966500000000"
    db_session.commit()

    db_session.refresh(wo_in_progress)
    wo = db_session.get(WorkOrder, wo_in_progress.id)
    auto = build_report_auto_fill(db_session, wo, technician)
    assert auto["inspector_full_name"] == "Tech"
    assert auto["inspector_title"] == "Lead Tech"
    assert auto["inspector_license"] == "LIC-42"
    assert auto["property_site_name"] == "S1"
    assert auto["asset_unit_identification"] == "HVAC-001"
    assert auto["scope_systems_list"] == "HVAC — general"

    merged = merge_report_answers(
        db_session,
        wo,
        technician,
        {"inspection_end_time": "14:30", "tests_performed": "Visual check"},
    )
    assert merged["tests_performed"] == "Visual check"
    assert merged["time_elapsed_hours"] is not None


def test_work_order_out_includes_asset_context(db_session, wo_in_progress, site_a):
    from app.api.routes.work_orders import _reload_wo_with_users, _work_order_to_out
    from app.models import Asset

    asset = Asset(
        id=uuid4(),
        tenant_id=wo_in_progress.tenant_id,
        site_id=site_a.id,
        name="Pump 1",
        category="Mechanical",
        serial="P-1",
        label_code="PUMP-01",
    )
    db_session.add(asset)
    wo_in_progress.asset_id = asset.id
    site_a.address_json = {"address": "123 Main", "city": "Riyadh", "country": "SA"}
    db_session.commit()

    wo = _reload_wo_with_users(db_session, wo_in_progress.id)
    out = _work_order_to_out(wo)
    assert out.asset_name == "Pump 1"
    assert out.asset_category == "Mechanical"
    assert out.site_address == "123 Main"
    assert out.site_city == "Riyadh"
