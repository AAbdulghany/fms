"""Wave 2 demo environment tests (NT-112–NT-114).

NT-P1-03 / NT-P2-U02 (A5): pitch_seed is now users-only, matching seed.py.
No default clients/assets/WOs are created on a fresh DB.
"""

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import Asset, Client, Invoice, Tenant, User, UserRole
from app.pitch_seed import seed_pitch_demo, SEED_USERS
from app.services.platform_bootstrap import ensure_default_packages
from tests.api_helpers import auth_header


def test_pitch_seed_users_only(db_session):
    """A5: pitch_seed creates only users; no clients, assets, or invoices."""
    ensure_default_packages(db_session)
    info = seed_pitch_demo(db_session)
    db_session.commit()
    assert int(info["users_created"]) == len(SEED_USERS)
    assert db_session.scalar(select(func.count()).select_from(Client)) == 0
    assert db_session.scalar(select(func.count()).select_from(Asset)) == 0
    assert db_session.scalar(select(func.count()).select_from(Invoice)) == 0


def test_pitch_seed_idempotent_structure(db_session):
    """A5: exactly 1 tenant and the seeded users after running pitch_seed."""
    ensure_default_packages(db_session)
    seed_pitch_demo(db_session)
    db_session.commit()
    tenants = db_session.scalars(select(Tenant)).all()
    assert len(tenants) == 1
    users = db_session.scalars(select(User)).all()
    assert len(users) == len(SEED_USERS)
    # No demo data
    assert db_session.scalar(select(func.count()).select_from(Client)) == 0


def test_demo_reset_endpoint_demo_env(api_client, db_session, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    from app.config import get_settings

    get_settings.cache_clear()

    ensure_default_packages(db_session)
    tenant = Tenant(id=uuid4(), name="T", status="active")
    db_session.add(tenant)
    admin = User(
        tenant_id=tenant.id,
        email="p@demo.com",
        password_hash=hash_password("pass"),
        role=UserRole.super_admin,
        is_platform_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    res = api_client.post("/api/v1/platform/demo/reset", headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1
    get_settings.cache_clear()


def test_demo_reset_blocked_in_production(api_client, db_session, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()
    tenant = Tenant(id=uuid4(), name="T", status="active")
    db_session.add(tenant)
    admin = User(
        tenant_id=tenant.id,
        email="p2@demo.com",
        password_hash=hash_password("pass"),
        role=UserRole.super_admin,
        is_platform_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    res = api_client.post("/api/v1/platform/demo/reset", headers=auth_header(admin))
    assert res.status_code == 403
    get_settings.cache_clear()
