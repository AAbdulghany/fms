"""Phase 3 role model — super_user, sw_dev, company_engineer."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.models import Tenant, User, UserRole


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="RBAC Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def platform_super(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="super@platform.test",
        password_hash=hash_password("pass"),
        full_name="Super User",
        role=UserRole.super_user,
        is_active=True,
        is_platform_admin=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def platform_sw_dev(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="swdev@platform.test",
        password_hash=hash_password("pass"),
        full_name="SW Dev",
        role=UserRole.sw_dev,
        is_active=True,
        is_platform_admin=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def company_admin(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="ca@tenant.test",
        password_hash=hash_password("pass"),
        full_name="Company Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def company_engineer(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="eng@tenant.test",
        password_hash=hash_password("pass"),
        full_name="Company Engineer",
        role=UserRole.company_engineer,
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
        email="tech@tenant.test",
        password_hash=hash_password("pass"),
        full_name="Technician",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


def test_sw_dev_can_list_maintenance_companies(db_session, platform_sw_dev, tenant):
    from app.api.routes.platform import list_maintenance_companies

    rows = list_maintenance_companies(db_session, platform_sw_dev)
    assert any(r.id == tenant.id for r in rows)


def test_sw_dev_cannot_deactivate_user(db_session, platform_sw_dev, technician):
    from app.api.routes.users import patch_user
    from app.schemas import UserPatchBody

    with pytest.raises(HTTPException) as exc:
        patch_user(
            technician.id,
            UserPatchBody(is_active=False),
            db_session,
            platform_sw_dev,
            platform_sw_dev,
        )
    assert exc.value.status_code == 403
    assert exc.value.detail == "CANNOT_REMOVE_MEMBERS"


def test_company_admin_can_create_company_engineer(db_session, company_admin):
    from app.api.routes.users import create_user
    from app.schemas import UserCreateBody

    result = create_user(
        UserCreateBody(
            email="neweng@tenant.test",
            full_name="New Engineer",
            role=UserRole.company_engineer,
            password="secure123",
        ),
        db_session,
        company_admin,
        company_admin,
    )
    assert result.user.role == UserRole.company_engineer


def test_company_engineer_cannot_create_peer_engineer(db_session, company_engineer):
    from app.api.routes.users import create_user
    from app.schemas import UserCreateBody

    with pytest.raises(HTTPException) as exc:
        create_user(
            UserCreateBody(
                email="peer@tenant.test",
                full_name="Peer Engineer",
                role=UserRole.company_engineer,
                password="secure123",
            ),
            db_session,
            company_engineer,
            company_engineer,
        )
    assert exc.value.status_code == 403


def test_company_engineer_can_create_technician(db_session, company_engineer):
    from app.api.routes.users import create_user
    from app.schemas import UserCreateBody

    result = create_user(
        UserCreateBody(
            email="newtech@tenant.test",
            full_name="New Tech",
            role=UserRole.technician,
            password="secure123",
        ),
        db_session,
        company_engineer,
        company_engineer,
    )
    assert result.user.role == UserRole.technician


def test_company_engineer_cannot_demote_company_admin(db_session, company_engineer, company_admin):
    from app.api.routes.users import patch_user
    from app.schemas import UserPatchBody

    with pytest.raises(HTTPException) as exc:
        patch_user(
            company_admin.id,
            UserPatchBody(role=UserRole.technician),
            db_session,
            company_engineer,
            company_engineer,
        )
    assert exc.value.status_code == 403


def test_rbac_module_can_remove_members():
    from app.rbac import can_remove_members

    sw = User(role=UserRole.sw_dev, is_platform_admin=True)
    su = User(role=UserRole.super_user, is_platform_admin=True)
    assert can_remove_members(su) is True
    assert can_remove_members(sw) is False
