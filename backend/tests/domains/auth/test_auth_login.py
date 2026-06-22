"""Login identifier resolution (no static passwords — avoids secret scanners)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.api.routes.auth import login
from app.core.security import hash_password
from app.models import Tenant, User, UserRole
from app.schemas import LoginRequest


def _random_password() -> str:
    return uuid.uuid4().hex + "Aa1!"


def test_login_email_case_insensitive(db_session, sample_tenant):
    plain = _random_password()
    db_session.add(
        User(
            tenant_id=sample_tenant.id,
            email="User@Test.Local",
            password_hash=hash_password(plain),
            full_name="Case Test",
            role=UserRole.company_admin,
            is_active=True,
        )
    )
    db_session.commit()

    tok = login(
        LoginRequest(identifier="user@test.local", password=plain),
        db_session,
    )
    assert tok.access_token


def test_login_username_case_insensitive(db_session, sample_tenant):
    plain = _random_password()
    db_session.add(
        User(
            tenant_id=sample_tenant.id,
            email="u1@placeholder.fms",
            username="site-mgr-01",
            password_hash=hash_password(plain),
            full_name="U Test",
            role=UserRole.site_manager,
            is_active=True,
        )
    )
    db_session.commit()

    tok = login(LoginRequest(identifier="SITE-MGR-01", password=plain), db_session)
    assert tok.access_token


def test_login_rejects_ambiguous_same_identifier_different_tenants(db_session):
    """Same email in two tenants: only succeeds if exactly one password matches."""
    t1 = Tenant(name="T1", status="active")
    t2 = Tenant(name="T2", status="active")
    db_session.add_all([t1, t2])
    db_session.flush()

    plain_a = _random_password()
    plain_b = _random_password()
    shared_email = f"dup-{uuid.uuid4().hex[:8]}@shared.test"

    db_session.add_all(
        [
            User(
                tenant_id=t1.id,
                email=shared_email,
                password_hash=hash_password(plain_a),
                full_name="A",
                role=UserRole.company_admin,
                is_active=True,
            ),
            User(
                tenant_id=t2.id,
                email=shared_email,
                password_hash=hash_password(plain_b),
                full_name="B",
                role=UserRole.company_admin,
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    tok = login(LoginRequest(identifier=shared_email, password=plain_a), db_session)
    assert tok.user.email == shared_email

    with pytest.raises(HTTPException) as exc:
        login(LoginRequest(identifier=shared_email, password="wrong"), db_session)
    assert exc.value.status_code == 401


def test_login_legacy_email_field_still_works(db_session, sample_tenant):
    plain = _random_password()
    db_session.add(
        User(
            tenant_id=sample_tenant.id,
            email="legacy@test.local",
            password_hash=hash_password(plain),
            full_name="L",
            role=UserRole.technician,
            is_active=True,
        )
    )
    db_session.commit()

    tok = login(LoginRequest(email="legacy@test.local", password=plain), db_session)
    assert tok.access_token
