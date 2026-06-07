"""Provisioning username pattern tests — Phase 3 MVP.

Test plan IDs: PR-01 … PR-04
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import Client, Tenant, User, UserRole
from app.services.provisioning import (
    build_manager_username,
    company_slug,
    ensure_unique_username,
    next_client_code,
)


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
def client_giza(db_session, tenant):
    c = Client(
        id=uuid4(),
        tenant_id=tenant.id,
        legal_name="Giza Systems",
        code="GIZA-2026-XXXX",
        status="active",
    )
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


# ---------------------------------------------------------------------------
# PR-01: company_slug + next_client_code includes slug
# ---------------------------------------------------------------------------


def test_pr01_company_slug_derived_from_legal_name():
    """Slug is lowercase alphanumeric, max 32 chars."""
    assert company_slug("Giza Systems") == "gizasystems"
    assert company_slug("Al-Futtaim Group LLC") == "alfuttaimgroupllc"
    assert company_slug("  Hello  World!!  ") == "helloworld"
    long_name = "A" * 40
    assert len(company_slug(long_name)) <= 32


def test_pr01_client_code_contains_slug(db_session, tenant):
    """next_client_code returns a code containing the company name slug."""
    code = next_client_code(db_session, tenant.id, "Giza Systems")
    # Should contain 'GIZASYST' (first 8 chars of slug uppercased)
    assert "GIZASYST" in code
    assert str(2026) in code or str(2025) in code  # year-based


def test_pr01_client_code_is_unique(db_session, tenant):
    """next_client_code never returns an already-used code."""
    codes = {next_client_code(db_session, tenant.id, "Giza Systems") for _ in range(10)}
    assert len(codes) == 10, "All generated codes should be unique"


# ---------------------------------------------------------------------------
# PR-02: client manager username format
# ---------------------------------------------------------------------------


def test_pr02_manager_username_cmgr_format():
    """build_manager_username produces abdullah-cmgr@gizasystems."""
    username = build_manager_username("Abdullah", "cmgr", "gizasystems")
    assert username == "abdullah-cmgr@gizasystems"


def test_pr02_first_name_only_used():
    """Only the first token of a multi-word first_name is used."""
    username = build_manager_username("Abdullah Al-Rashid", "cmgr", "gizasystems")
    assert username == "abdullah-cmgr@gizasystems"


def test_pr02_special_chars_stripped_from_name():
    """Non-alphanumeric chars in first name are stripped."""
    username = build_manager_username("O'Brien", "cmgr", "acme")
    assert username == "obrien-cmgr@acme"


def test_pr02_ensure_unique_username_new(db_session, tenant):
    """ensure_unique_username returns base when no collision exists."""
    base = "abdullah-cmgr@gizasystems"
    result = ensure_unique_username(db_session, tenant.id, base)
    assert result == base


# ---------------------------------------------------------------------------
# PR-03: site manager username format
# ---------------------------------------------------------------------------


def test_pr03_site_manager_username_smgr_format():
    """build_manager_username produces <name>-smgr@<slug>."""
    username = build_manager_username("Abdullah", "smgr", "gizasystems")
    assert username == "abdullah-smgr@gizasystems"


def test_pr03_smgr_unique_in_tenant(db_session, tenant):
    """ensure_unique_username for smgr: no collision → same base returned."""
    base = "abdullah-smgr@gizasystems"
    result = ensure_unique_username(db_session, tenant.id, base)
    assert result == base


# ---------------------------------------------------------------------------
# PR-04: collision → suffix appended
# ---------------------------------------------------------------------------


def _make_user(db_session, tenant, username: str) -> User:
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email=f"{username.replace('@', '_').replace('-', '_')}@test.com",
        username=username,
        password_hash=hash_password("secret"),
        full_name="Test User",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


def test_pr04_collision_appends_suffix(db_session, tenant):
    """When base username exists, -2 is appended."""
    base = "ahmed-cmgr@acme"
    _make_user(db_session, tenant, base)

    result = ensure_unique_username(db_session, tenant.id, base)
    assert result == f"{base}-2"


def test_pr04_double_collision_appends_higher_suffix(db_session, tenant):
    """When base and -2 exist, -3 is returned."""
    base = "fatima-smgr@corp"
    _make_user(db_session, tenant, base)
    _make_user(db_session, tenant, f"{base}-2")

    result = ensure_unique_username(db_session, tenant.id, base)
    assert result == f"{base}-3"


def test_pr04_provision_client_endpoint_uses_new_format(db_session, tenant):
    """End-to-end: provision_client_with_manager creates username in new format."""
    from app.api.routes.clients import provision_client_with_manager
    from app.schemas import ClientProvisionRequest

    # Create a super_admin actor
    actor = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="superadmin@test.com",
        password_hash=hash_password("password"),
        full_name="Super Admin",
        role=UserRole.super_admin,
        is_active=True,
        is_platform_admin=False,
    )
    db_session.add(actor)
    db_session.commit()

    body = ClientProvisionRequest(
        legal_name="Giza Systems",
        manager_full_name="Abdullah Hassan",
    )

    response = provision_client_with_manager(body, db_session, actor, actor)
    # Username must contain cmgr and gizasystems
    assert "cmgr" in response.manager_username
    assert "gizasystems" in response.manager_username
    # Client code must reference the slug
    assert "GIZASYST" in response.company_code
