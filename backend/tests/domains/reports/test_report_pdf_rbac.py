"""Report PDF endpoint must enforce same WO RBAC as work order routes."""

from uuid import uuid4

from app.core.security import hash_password
from app.models import (
    Client,
    MaintenanceReport,
    ReportStatus,
    ReportTemplate,
    Site,
    User,
    UserRole,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from tests.api_helpers import auth_header


def _seed_report_chain(db_session, sample_tenant, assignee: User, other_tech: User | None = None):
    client = Client(id=uuid4(), tenant_id=sample_tenant.id, legal_name="C", code="C1")
    site = Site(id=uuid4(), tenant_id=sample_tenant.id, client_id=client.id, name="S1")
    tmpl = ReportTemplate(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        name="R",
        code="r",
        version=1,
        schema_json={"sections": []},
        maintenance_types=[],
    )
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=client.id,
        site_id=site.id,
        title="WO",
        status=WorkOrderStatus.in_progress,
        source=WorkOrderSource.corrective,
        assignee_user_id=assignee.id,
        template_id=tmpl.id,
    )
    report = MaintenanceReport(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        work_order_id=wo.id,
        template_id=tmpl.id,
        template_version=1,
        status=ReportStatus.submitted,
        answers_json={"tests_performed": "ok"},
        template_snapshot_json={"sections": []},
    )
    rows = [client, site, assignee, tmpl, wo, report]
    if other_tech:
        rows.insert(2, other_tech)
    db_session.add_all(rows)
    db_session.commit()
    return report


def test_report_pdf_forbidden_for_non_assignee_technician(api_client, db_session, sample_tenant):
    assignee = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="assignee@test.com",
        password_hash=hash_password("x"),
        full_name="Assignee",
        role=UserRole.technician,
        is_active=True,
    )
    other_tech = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="other@test.com",
        password_hash=hash_password("x"),
        full_name="Other",
        role=UserRole.technician,
        is_active=True,
    )
    report = _seed_report_chain(db_session, sample_tenant, assignee, other_tech)

    res = api_client.get(
        f"/api/v1/reports/{report.id}/pdf",
        headers=auth_header(other_tech),
    )
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "FORBIDDEN"


def test_report_pdf_allowed_for_assignee_technician(api_client, db_session, sample_tenant):
    assignee = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="assignee2@test.com",
        password_hash=hash_password("x"),
        full_name="Assignee2",
        role=UserRole.technician,
        is_active=True,
    )
    report = _seed_report_chain(db_session, sample_tenant, assignee)

    res = api_client.get(
        f"/api/v1/reports/{report.id}/pdf",
        headers=auth_header(assignee),
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
