"""Unit tests for test_seed — verifies users-only, comprehensive role coverage."""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app.cli.test_seed import SEED_USER_SPECS, TENANT_NAME, _seed
from app.models import Asset, Client, Site, Tenant, User, UserRole, WorkOrder
from app.services.platform_bootstrap import ensure_default_packages


def test_test_seed_users_only(db_session):
    """test_seed creates users and tenant only — no clients, sites, assets, or WOs."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    assert db_session.scalar(select(func.count()).select_from(Client)) == 0
    assert db_session.scalar(select(func.count()).select_from(Site)) == 0
    assert db_session.scalar(select(func.count()).select_from(Asset)) == 0
    assert db_session.scalar(select(func.count()).select_from(WorkOrder)) == 0


def test_test_seed_user_count(db_session):
    """Exactly one tenant and exactly SEED_USER_SPECS users are created."""
    ensure_default_packages(db_session)
    info = _seed(db_session)
    db_session.commit()

    assert int(info["users_created"]) == len(SEED_USER_SPECS)
    assert db_session.scalar(select(func.count()).select_from(User)) == len(SEED_USER_SPECS)
    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1


def test_test_seed_tenant_name(db_session):
    """Tenant uses the canonical TENANT_NAME."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    tenant = db_session.scalar(select(Tenant))
    assert tenant is not None
    assert tenant.name == TENANT_NAME


def test_test_seed_role_coverage(db_session):
    """All required roles are represented in the seed."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    roles_present = {
        r for (r,) in db_session.execute(select(User.role)).all()
    }
    required_roles = {
        UserRole.super_user,
        UserRole.sw_dev,
        UserRole.company_admin,
        UserRole.company_engineer,
        UserRole.manager,
        UserRole.client_admin,
        UserRole.site_manager,
        UserRole.technician,
    }
    missing = required_roles - roles_present
    assert not missing, f"Missing roles: {missing}"


def test_test_seed_platform_admins(db_session):
    """super@demo.com and swdev@demo.com are platform admins."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    for email in ("super@demo.com", "swdev@demo.com"):
        user = db_session.scalar(select(User).where(User.email == email))
        assert user is not None, f"{email} not found"
        assert user.is_platform_admin, f"{email} should be platform admin"


def test_test_seed_no_client_id_on_client_user(db_session):
    """client@demo.com has no client_id in test seed (no clients exist)."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    user = db_session.scalar(select(User).where(User.email == "client@demo.com"))
    assert user is not None
    assert user.client_id is None


def test_test_seed_metadata_seed_profile(db_session):
    """All seeded users have metadata_json.seed_profile == 'test'."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    users = db_session.scalars(select(User)).all()
    for user in users:
        assert user.metadata_json.get("seed_profile") == "test", (
            f"{user.email} missing seed_profile=test"
        )


def test_test_seed_idempotent(db_session):
    """Running _seed twice keeps exactly one tenant."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()
    _seed(db_session)
    db_session.commit()

    assert db_session.scalar(select(func.count()).select_from(Tenant)) == 1


def test_test_seed_users_have_usernames(db_session):
    """All test-seed users have a username set."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    users = db_session.scalars(select(User)).all()
    for user in users:
        assert user.username, f"{user.email} has no username"


def test_test_seed_locale_mix(db_session):
    """Platform users are locale=en; tenant users are locale=ar."""
    ensure_default_packages(db_session)
    _seed(db_session)
    db_session.commit()

    for email, expected_locale in [
        ("super@demo.com", "en"),
        ("swdev@demo.com", "en"),
        ("admin@demo.com", "ar"),
        ("tech@demo.com", "ar"),
    ]:
        user = db_session.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.locale == expected_locale, (
            f"{email}: expected locale={expected_locale}, got {user.locale}"
        )
