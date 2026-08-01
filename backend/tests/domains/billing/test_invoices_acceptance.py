"""Wave 4 backend tests: NT-126 (invoices feature gate) and NT-123 (generate validation)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import (
    SubscriptionPackage,
    Tenant,
    TenantSubscription,
    User,
    UserRole,
)
from app.services.platform_bootstrap import ensure_default_packages
from tests.api_helpers import auth_header, assert_api_error


@pytest.fixture
def packages(db_session):
    pkgs = ensure_default_packages(db_session)
    db_session.commit()
    return pkgs


@pytest.fixture
def admin_user(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="admin_w4@test.com",
        password_hash=hash_password("pass123"),
        full_name="Admin Wave4",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_invoices_feature_gate_production(
    api_client, db_session, sample_tenant, packages, admin_user, monkeypatch
):
    """Package without invoices → 403 on invoice list (production)."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    empty_pkg = SubscriptionPackage(
        code="no_invoices_test",
        name="No Invoices",
        features_json=["assets"],
        limits_json={"max_users": 5},
        is_active=True,
    )
    db_session.add(empty_pkg)
    db_session.flush()
    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=empty_pkg.id,
        status="active",
    )
    db_session.add(sub)
    db_session.commit()

    res = api_client.get("/api/v1/invoices", headers=auth_header(admin_user))
    assert_api_error(res, status=403, code="FEATURE_NOT_AVAILABLE")

    get_settings.cache_clear()


def test_invoices_allowed_with_pro_package(
    api_client, db_session, sample_tenant, packages, admin_user, monkeypatch
):
    """Pro/enterprise packages include invoices feature."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=packages["pro"].id,
        status="active",
    )
    db_session.add(sub)
    db_session.commit()

    res = api_client.get("/api/v1/invoices", headers=auth_header(admin_user))
    assert res.status_code == 200

    get_settings.cache_clear()


def test_invoices_feature_gate_bypassed_in_dev(api_client, db_session, admin_user, monkeypatch):
    """Dev env bypasses subscription feature gate."""
    monkeypatch.setenv("APP_ENV", "development")
    from app.config import get_settings

    get_settings.cache_clear()

    res = api_client.get("/api/v1/invoices", headers=auth_header(admin_user))
    assert res.status_code == 200

    get_settings.cache_clear()
