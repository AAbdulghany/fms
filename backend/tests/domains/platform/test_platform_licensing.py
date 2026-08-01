"""Wave 1 platform API + licensing tests (NT-105–NT-111)."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.models import SubscriptionPackage, TenantSubscription, User, UserRole
from app.services.platform_bootstrap import ensure_default_packages
from app.services.subscription import has_feature, is_subscription_active
from tests.api_helpers import auth_header, assert_api_error


@pytest.fixture
def platform_admin(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="platform@demo.com",
        password_hash=hash_password("pass123"),
        role=UserRole.super_admin,
        is_platform_admin=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def regular_admin(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="admin2@demo.com",
        password_hash=hash_password("pass123"),
        role=UserRole.company_admin,
        is_platform_admin=False,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_list_packages_platform_admin(api_client, db_session, platform_admin):
    ensure_default_packages(db_session)
    db_session.commit()
    res = api_client.get("/api/v1/platform/packages", headers=auth_header(platform_admin))
    assert res.status_code == 200
    assert len(res.json()) >= 4


def test_create_package_nt105(api_client, db_session, platform_admin):
    res = api_client.post(
        "/api/v1/platform/packages",
        headers=auth_header(platform_admin),
        json={
            "code": "pitch",
            "name": "Pitch Package",
            "features_json": ["assets", "invoices"],
            "limits_json": {"max_users": 5},
        },
    )
    assert res.status_code == 201
    assert res.json()["code"] == "pitch"


def test_non_platform_forbidden_nt105(api_client, db_session, regular_admin):
    res = api_client.get("/api/v1/platform/packages", headers=auth_header(regular_admin))
    assert res.status_code == 403


def test_assign_tenant_license_nt106(api_client, db_session, platform_admin, sample_tenant):
    packages = ensure_default_packages(db_session)
    db_session.commit()
    res = api_client.put(
        f"/api/v1/platform/tenants/{sample_tenant.id}/license",
        headers=auth_header(platform_admin),
        json={
            "package_id": str(packages["starter"].id),
            "status": "active",
            "valid_until": (date.today() + timedelta(days=30)).isoformat(),
        },
    )
    assert res.status_code == 200
    assert res.json()["plan"] == "starter"


def test_login_blocked_when_suspended_nt107(api_client, db_session, sample_tenant, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    user = User(
        tenant_id=sample_tenant.id,
        email="frozen@demo.com",
        password_hash=hash_password("frozen123"),
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=packages["trial"].id,
            status="suspended",
        )
    )
    db_session.commit()

    res = api_client.post(
        "/api/v1/auth/login",
        json={"identifier": "frozen@demo.com", "password": "frozen123"},
    )
    assert_api_error(res, status=403, code="SUBSCRIPTION_SUSPENDED")
    get_settings.cache_clear()


def test_feature_gate_assets_nt108(api_client, db_session, sample_tenant, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    starter = packages["starter"]
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=starter.id,
            status="active",
        )
    )
    user = User(
        tenant_id=sample_tenant.id,
        email="starter@demo.com",
        password_hash=hash_password("pass123"),
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    assert has_feature(db_session, sample_tenant, "assets") is True
    assert has_feature(db_session, sample_tenant, "csv_import") is False

    res = api_client.get("/api/v1/assets", headers=auth_header(user))
    assert res.status_code == 200
    get_settings.cache_clear()


def test_deactivate_package(api_client, db_session, platform_admin):
    pkg = SubscriptionPackage(code="temp", name="Temp", features_json=[], limits_json={})
    db_session.add(pkg)
    db_session.commit()
    res = api_client.delete(
        f"/api/v1/platform/packages/{pkg.id}",
        headers=auth_header(platform_admin),
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False
