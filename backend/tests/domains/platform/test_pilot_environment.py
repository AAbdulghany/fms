"""Pilot environment tests — pilot_seed produces rich multi-client dataset.

NT-P1-03 / pilot profile: 2 clients, 3 sites, ~15 assets, ~50 WOs, 2 invoices.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.security import hash_password
from app.models import Asset, Client, Invoice, Site, Tenant, User, UserRole, WorkOrder
from app.cli.pilot_seed import seed_pilot, SEED_USERS, TENANT_NAME
from app.services.platform_bootstrap import ensure_default_packages
from tests.api_helpers import auth_header


def test_pilot_seed_rich_dataset(db_session):
    """pilot_seed creates 2 clients, 3 sites, ≥12 assets, ≥40 WOs, 2 invoices."""
    ensure_default_packages(db_session)
    info = seed_pilot(db_session)
    db_session.commit()

    assert int(info["users_created"]) == len(SEED_USERS)
    assert info["clients"] == 2
    assert info["sites"] == 3
    assert info["assets"] >= 12
    assert info["work_orders"] >= 40
    assert info["invoices"] == 2


def test_pilot_seed_client_structure(db_session):
    """Two clients GE-001 and RR-002 are created with correct codes."""
    ensure_default_packages(db_session)
    seed_pilot(db_session)
    db_session.commit()

    clients = db_session.scalars(select(Client).order_by(Client.code)).all()
    assert len(clients) == 2
    codes = {c.code for c in clients}
    assert "GE-001" in codes
    assert "RR-002" in codes


def test_pilot_seed_work_order_distribution(db_session):
    """WOs are distributed across multiple statuses (no single-status dominance)."""
    ensure_default_packages(db_session)
    info = seed_pilot(db_session)
    db_session.commit()

    by_status = info["wo_by_status"]
    # All key status buckets must be populated
    for status in ("created", "assigned", "in_progress", "on_hold",
                   "completed", "verified", "closed", "cancelled"):
        assert by_status.get(status, 0) > 0, f"No WOs in status '{status}'"


def test_pilot_seed_invoices_on_verified_wos(db_session):
    """Draft invoices exist and are linked to verified work orders."""
    ensure_default_packages(db_session)
    seed_pilot(db_session)
    db_session.commit()

    invoices = db_session.scalars(select(Invoice)).all()
    assert len(invoices) == 2
    for inv in invoices:
        wo = db_session.get(WorkOrder, inv.work_order_id)
        assert wo is not None
        assert wo.status.value == "verified"


def test_pilot_seed_user_client_wiring(db_session):
    """client@demo.com and client2@demo.com are wired to distinct clients."""
    ensure_default_packages(db_session)
    seed_pilot(db_session)
    db_session.commit()

    u1 = db_session.scalar(select(User).where(User.email == "client@demo.com"))
    u2 = db_session.scalar(select(User).where(User.email == "client2@demo.com"))
    assert u1 is not None and u1.client_id is not None
    assert u2 is not None and u2.client_id is not None
    assert u1.client_id != u2.client_id


def test_pilot_seed_idempotent(db_session):
    """Running pilot_seed twice stays idempotent (one tenant, correct counts)."""
    ensure_default_packages(db_session)
    seed_pilot(db_session)
    db_session.commit()
    seed_pilot(db_session)
    db_session.commit()

    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1
    assert db_session.scalar(select(func.count()).select_from(Client)) == 2


def test_pilot_seed_tenant_name(db_session):
    """Tenant is created with the canonical TENANT_NAME."""
    ensure_default_packages(db_session)
    seed_pilot(db_session)
    db_session.commit()

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None
    assert tenant.name == TENANT_NAME


def _platform_admin(db_session, email: str) -> User:
    tenant = Tenant(id=uuid4(), name="T", status="active")
    db_session.add(tenant)
    admin = User(
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("pass"),
        role=UserRole.super_admin,
        is_platform_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.mark.parametrize(
    ("app_env", "path"),
    [
        ("pilot", "/api/v1/platform/pilot/reset"),
        ("demo", "/api/v1/platform/pilot/reset"),
        ("pilot", "/api/v1/platform/demo/reset"),
    ],
)
def test_pilot_reset_allowed_in_pilot_env(api_client, db_session, monkeypatch, app_env, path):
    monkeypatch.setenv("APP_ENV", app_env)
    from app.config import get_settings

    get_settings.cache_clear()
    ensure_default_packages(db_session)
    admin = _platform_admin(db_session, "p@demo.com")

    res = api_client.post(path, headers=auth_header(admin))
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1
    get_settings.cache_clear()


@pytest.mark.parametrize("app_env", ["production", "development"])
@pytest.mark.parametrize("path", ["/api/v1/platform/pilot/reset", "/api/v1/platform/demo/reset"])
def test_pilot_reset_blocked_outside_pilot(api_client, db_session, monkeypatch, app_env, path):
    monkeypatch.setenv("APP_ENV", app_env)
    from app.config import get_settings

    get_settings.cache_clear()
    admin = _platform_admin(db_session, "p2@demo.com")

    res = api_client.post(path, headers=auth_header(admin))
    assert res.status_code == 403
    assert res.json()["detail"] == "PILOT_ENV_ONLY"
    get_settings.cache_clear()
