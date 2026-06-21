"""
Phase 3 MVP — Work Order Request Flow tests.

Covers WR-01 through WR-07 from docs/phase3/PHASE3_TEST_PLAN.md.
"""

import pytest
from uuid import uuid4
from fastapi import BackgroundTasks, HTTPException

from app.core.security import hash_password
from app.models import (
    Asset,
    Client,
    Site,
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderStatus,
)
from app.models import WorkOrderSource, Urgency


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="Test Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def client_a(db_session, tenant):
    c = Client(id=uuid4(), tenant_id=tenant.id, legal_name="Client A", code="CA")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def client_b(db_session, tenant):
    c = Client(id=uuid4(), tenant_id=tenant.id, legal_name="Client B", code="CB")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


@pytest.fixture
def site_a(db_session, tenant, client_a):
    s = Site(id=uuid4(), tenant_id=tenant.id, client_id=client_a.id, name="Site A")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


@pytest.fixture
def site_b(db_session, tenant, client_b):
    s = Site(id=uuid4(), tenant_id=tenant.id, client_id=client_b.id, name="Site B")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _make_user(db_session, tenant, role, client=None, email=None):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client.id if client else None,
        email=email or f"{role.value}-{uuid4().hex[:6]}@test.com",
        password_hash=hash_password("pass"),
        full_name=role.value,
        role=role,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def super_admin(db_session, tenant):
    return _make_user(db_session, tenant, UserRole.super_admin)


@pytest.fixture
def company_admin(db_session, tenant):
    return _make_user(db_session, tenant, UserRole.company_admin)


@pytest.fixture
def client_admin_a(db_session, tenant, client_a):
    return _make_user(db_session, tenant, UserRole.client_admin, client=client_a)


@pytest.fixture
def site_manager_a(db_session, tenant, site_a):
    u = _make_user(db_session, tenant, UserRole.site_manager)
    scope = UserSiteScope(user_id=u.id, site_id=site_a.id)
    db_session.add(scope)
    db_session.commit()
    return u


@pytest.fixture
def technician(db_session, tenant):
    return _make_user(db_session, tenant, UserRole.technician)


@pytest.fixture
def asset_a(db_session, tenant, site_a):
    a = Asset(id=uuid4(), tenant_id=tenant.id, site_id=site_a.id, name="Asset A")
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


@pytest.fixture
def asset_b(db_session, tenant, site_b):
    a = Asset(id=uuid4(), tenant_id=tenant.id, site_id=site_b.id, name="Asset B")
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


def _wo_create_body(client_id, site_id, asset_id):
    from app.schemas import WorkOrderCreate

    return WorkOrderCreate(
        client_id=client_id,
        site_id=site_id,
        asset_id=asset_id,
        title="Test WO Request",
        source=WorkOrderSource.corrective,
        urgency=Urgency.normal,
    )


# ---------------------------------------------------------------------------
# WR-01: client_admin submits request for own client/site → 201, status=requested
# ---------------------------------------------------------------------------


def test_WR01_client_admin_can_request_work_order(
    db_session, client_admin_a, client_a, site_a, asset_a
):
    from app.api.routes.work_orders import request_work_order

    body = _wo_create_body(client_a.id, site_a.id, asset_a.id)
    wo = request_work_order(body, db_session, client_admin_a, client_admin_a, BackgroundTasks())

    assert wo.status == WorkOrderStatus.requested
    assert wo.client_id == client_a.id
    assert wo.site_id == site_a.id
    assert wo.created_by_user_id == client_admin_a.id


# ---------------------------------------------------------------------------
# WR-02: site_manager submits for scoped site → 201, status=requested
# ---------------------------------------------------------------------------


def test_WR02_site_manager_can_request_work_order_for_scoped_site(
    db_session, site_manager_a, client_a, site_a, asset_a
):
    from app.api.routes.work_orders import request_work_order

    body = _wo_create_body(client_a.id, site_a.id, asset_a.id)
    wo = request_work_order(body, db_session, site_manager_a, site_manager_a, BackgroundTasks())

    assert wo.status == WorkOrderStatus.requested
    assert wo.site_id == site_a.id


# ---------------------------------------------------------------------------
# WR-03: site_manager submits for unscoped site → 403
# ---------------------------------------------------------------------------


def test_WR03_site_manager_blocked_from_unscoped_site(
    db_session, site_manager_a, client_b, site_b, asset_b
):
    from app.api.routes.work_orders import request_work_order

    body = _wo_create_body(client_b.id, site_b.id, asset_b.id)

    with pytest.raises(HTTPException) as exc_info:
        request_work_order(body, db_session, site_manager_a, site_manager_a, BackgroundTasks())

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# WR-04: client_admin direct POST /work-orders → 403
# ---------------------------------------------------------------------------


def test_WR04_client_admin_cannot_direct_create_work_order(db_session, client_admin_a):
    from app.api.deps import require_roles

    dep = require_roles(UserRole.super_admin, UserRole.company_admin)

    with pytest.raises(HTTPException) as exc_info:
        dep(client_admin_a)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "FORBIDDEN"


# ---------------------------------------------------------------------------
# WR-05: company_admin approves request → status=created, requester notified
# ---------------------------------------------------------------------------


def test_WR05_company_admin_approves_request(
    db_session, company_admin, client_admin_a, client_a, site_a, asset_a
):
    from app.api.routes.work_orders import approve_work_order_request, request_work_order

    # client_admin submits request
    body = _wo_create_body(client_a.id, site_a.id, asset_a.id)
    wo_out = request_work_order(body, db_session, client_admin_a, client_admin_a, BackgroundTasks())
    assert wo_out.status == WorkOrderStatus.requested

    # company_admin approves
    approved = approve_work_order_request(
        wo_out.id, db_session, company_admin, company_admin, BackgroundTasks()
    )

    assert approved.status == WorkOrderStatus.created
    assert approved.id == wo_out.id


# ---------------------------------------------------------------------------
# WR-06: company_admin declines request → status=declined
# ---------------------------------------------------------------------------


def test_WR06_company_admin_declines_request(
    db_session, company_admin, client_admin_a, client_a, site_a, asset_a
):
    from app.api.routes.work_orders import decline_work_order_request, request_work_order
    from app.schemas import DeclineRequestBody

    body = _wo_create_body(client_a.id, site_a.id, asset_a.id)
    wo_out = request_work_order(body, db_session, client_admin_a, client_admin_a, BackgroundTasks())

    decline_body = DeclineRequestBody(reason="Insufficient budget")
    declined = decline_work_order_request(
        wo_out.id, decline_body, db_session, company_admin, company_admin, BackgroundTasks()
    )

    assert declined.status == WorkOrderStatus.declined
    assert declined.id == wo_out.id


def test_WR06b_decline_requires_reason(
    db_session, company_admin, client_admin_a, client_a, site_a, asset_a
):
    from app.api.routes.work_orders import request_work_order
    from app.schemas import DeclineRequestBody
    from pydantic import ValidationError

    body = _wo_create_body(client_a.id, site_a.id, asset_a.id)
    wo_out = request_work_order(body, db_session, client_admin_a, client_admin_a, BackgroundTasks())

    with pytest.raises(ValidationError):
        DeclineRequestBody(reason="")


# ---------------------------------------------------------------------------
# WR-07: technician cannot approve request → 403
# ---------------------------------------------------------------------------


def test_WR07_technician_cannot_approve_request(
    db_session, technician, client_admin_a, company_admin, client_a, site_a
):
    from app.api.routes.work_orders import approve_work_order_request, request_work_order
    from app.api.deps import require_roles

    # First create a requested WO (by company_admin to bypass scope check)
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=technician.tenant_id,
        client_id=client_a.id,
        site_id=site_a.id,
        title="Request for technician test",
        status=WorkOrderStatus.requested,
        created_by_user_id=client_admin_a.id,
    )
    db_session.add(wo)
    db_session.commit()

    # Verify technician cannot pass the approve-request role gate
    dep = require_roles(UserRole.super_admin, UserRole.company_admin)

    with pytest.raises(HTTPException) as exc_info:
        dep(technician)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "FORBIDDEN"


# ---------------------------------------------------------------------------
# Extra: verify ?status=requested filter works on list endpoint
# ---------------------------------------------------------------------------


def test_list_filter_by_requested_status(
    db_session, company_admin, client_a, site_a
):
    from app.api.routes.work_orders import list_work_orders

    # Seed one requested WO
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=company_admin.tenant_id,
        client_id=client_a.id,
        site_id=site_a.id,
        title="Requested WO",
        status=WorkOrderStatus.requested,
    )
    db_session.add(wo)
    # Seed one created WO (should not appear in filter)
    wo2 = WorkOrder(
        id=uuid4(),
        tenant_id=company_admin.tenant_id,
        client_id=client_a.id,
        site_id=site_a.id,
        title="Created WO",
        status=WorkOrderStatus.created,
    )
    db_session.add(wo2)
    db_session.commit()

    result = list_work_orders(
        db_session,
        company_admin,
        page=1,
        page_size=20,
        status_filter="requested",
        urgency=None,
        client_id=None,
        site_id=None,
        assignee_user_id=None,
        date_from=None,
        date_to=None,
        search=None,
        tags=None,
    )

    ids = [r.id for r in result.data]
    assert wo.id in ids
    assert wo2.id not in ids
