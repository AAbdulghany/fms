from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.routes.auth import login
from app.core.security import hash_password
from app.models import Tenant, User, UserRole
from app.schemas import LoginRequest


def _create_tenant(db_session, name: str) -> Tenant:
    tenant = Tenant(id=uuid4(), name=name, status="active")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


def _create_user(
    db_session,
    tenant_id,
    *,
    email: str,
    username: str,
    password: str,
    is_active: bool = True,
) -> User:
    user = User(
        id=uuid4(),
        tenant_id=tenant_id,
        email=email,
        username=username,
        password_hash=hash_password(password),
        full_name="Test User",
        role=UserRole.super_admin,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_accepts_case_insensitive_username(db_session):
    tenant = _create_tenant(db_session, "Tenant A")
    user = _create_user(
        db_session,
        tenant.id,
        email="manager@example.com",
        username="ManagerOne",
        password="secret123",
    )

    result = login(LoginRequest(identifier="managerone", password="secret123"), db_session)

    assert result.user.id == user.id


def test_login_selects_correct_user_when_identifier_exists_in_multiple_tenants(db_session):
    tenant_a = _create_tenant(db_session, "Tenant A")
    tenant_b = _create_tenant(db_session, "Tenant B")

    _create_user(
        db_session,
        tenant_a.id,
        email="a@example.com",
        username="sharedmgr",
        password="pass-a",
    )
    user_b = _create_user(
        db_session,
        tenant_b.id,
        email="b@example.com",
        username="sharedmgr",
        password="pass-b",
    )

    result = login(LoginRequest(identifier="SHAREDMGR", password="pass-b"), db_session)

    assert result.user.id == user_b.id


def test_login_rejects_ambiguous_identifier_with_multiple_password_matches(db_session):
    tenant_a = _create_tenant(db_session, "Tenant A")
    tenant_b = _create_tenant(db_session, "Tenant B")

    _create_user(
        db_session,
        tenant_a.id,
        email="a@example.com",
        username="sharedmgr",
        password="same-password",
    )
    _create_user(
        db_session,
        tenant_b.id,
        email="b@example.com",
        username="sharedmgr",
        password="same-password",
    )

    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(identifier="sharedmgr", password="same-password"), db_session)

    assert exc.value.status_code == 401
    assert exc.value.detail == "INVALID_CREDENTIALS"
