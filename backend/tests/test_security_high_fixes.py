"""Security review High fixes — H1 (default password) and H2 (WO patch assign bypass)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.core.security import hash_password, verify_password
from app.models import (
    Client,
    Site,
    Tenant,
    User,
    UserRole,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.schemas import UserCreateBody, WorkOrderUpdate


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="Sec Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def company_admin(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="ca@sec.test",
        password_hash=hash_password("adminpass"),
        full_name="CA",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def technician(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="tech@sec.test",
        password_hash=hash_password("techpass"),
        full_name="Tech",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def other_tenant_user(db_session):
    t = Tenant(id=uuid4(), name="Other", status="active")
    db_session.add(t)
    db_session.flush()
    u = User(
        id=uuid4(),
        tenant_id=t.id,
        email="other@sec.test",
        password_hash=hash_password("x"),
        full_name="Other",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def work_order(db_session, tenant, company_admin, technician):
    c = Client(tenant_id=tenant.id, legal_name="C", code="C1")
    db_session.add(c)
    db_session.flush()
    s = Site(tenant_id=tenant.id, client_id=c.id, name="S1")
    db_session.add(s)
    db_session.flush()
    wo = WorkOrder(
        tenant_id=tenant.id,
        client_id=c.id,
        site_id=s.id,
        title="WO",
        status=WorkOrderStatus.assigned,
        source=WorkOrderSource.corrective,
        assignee_user_id=technician.id,
        created_by_user_id=company_admin.id,
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo


def test_h1_create_user_without_password_never_uses_changeme(db_session, company_admin):
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="auto@sec.test",
        full_name="Auto User",
        role=UserRole.technician,
    )
    result = create_user(body, db_session, company_admin, company_admin)

    assert result.initial_password is not None
    assert len(result.initial_password) >= 12
    assert not verify_password("changeme", db_session.get(User, result.user.id).password_hash)
    assert verify_password(result.initial_password, db_session.get(User, result.user.id).password_hash)
    assert db_session.get(User, result.user.id).metadata_json.get("must_change_password") is True


def test_h1_login_returns_must_change_password_flag(db_session, company_admin):
    from app.api.routes.auth import login
    from app.schemas import LoginRequest

    company_admin.metadata_json = {"must_change_password": True}
    db_session.commit()

    tok = login(LoginRequest(identifier=company_admin.email, password="adminpass"), db_session)
    assert tok.must_change_password is True


def test_h2_technician_cannot_patch_assignee(db_session, work_order, technician, company_admin):
    from app.api.routes.work_orders import patch_work_order

    with pytest.raises(HTTPException) as exc:
        patch_work_order(
            work_order.id,
            WorkOrderUpdate(assignee_user_id=company_admin.id),
            db_session,
            technician,
            BackgroundTasks(),
        )
    assert exc.value.status_code == 403


def test_h2_technician_can_patch_status_only(db_session, work_order, technician):
    from app.api.routes.work_orders import patch_work_order

    wo = patch_work_order(
        work_order.id,
        WorkOrderUpdate(status=WorkOrderStatus.in_progress),
        db_session,
        technician,
        BackgroundTasks(),
    )
    assert wo.status == WorkOrderStatus.in_progress


def test_h2_assign_rejects_cross_tenant_user(db_session, work_order, company_admin, other_tenant_user):
    from app.api.routes.work_orders import assign_work_order
    from app.schemas import AssignBody

    with pytest.raises(HTTPException) as exc:
        assign_work_order(
            work_order.id,
            AssignBody(assignee_user_id=other_tenant_user.id),
            db_session,
            company_admin,
            BackgroundTasks(),
            company_admin,  # satisfies require_roles dep when called directly
        )
    assert exc.value.status_code == 400
    assert exc.value.detail == "INVALID_ASSIGNEE"
