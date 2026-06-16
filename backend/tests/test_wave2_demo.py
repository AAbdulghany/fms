"""Wave 2 demo environment tests (NT-112–NT-114)."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import Client, Invoice, Tenant, User, UserRole
from app.pitch_seed import seed_pitch_demo
from app.services.platform_bootstrap import ensure_default_packages
from tests.api_helpers import auth_header


def test_pitch_seed_two_clients(db_session):
    ensure_default_packages(db_session)
    info = seed_pitch_demo(db_session)
    db_session.commit()
    assert int(info["clients"]) == 2
    assert int(info["assets"]) >= 4
    assert int(info["invoices"]) >= 2


def test_pitch_seed_idempotent_structure(db_session):
    ensure_default_packages(db_session)
    seed_pitch_demo(db_session)
    db_session.commit()
    tenants = db_session.scalars(select(Tenant)).all()
    assert len(tenants) == 1
    clients = db_session.scalars(select(Client)).all()
    assert len(clients) == 2
    invoices = db_session.scalars(select(Invoice)).all()
    assert len(invoices) >= 2


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
