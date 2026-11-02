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


def test_provision_tenant_returns_temp_password(api_client, db_session, platform_admin):
    packages = ensure_default_packages(db_session)
    db_session.commit()
    pkg_id = str(packages["starter"].id)
    res = api_client.post(
        "/api/v1/platform/tenants",
        headers=auth_header(platform_admin),
        json={
            "tenant_name": "Smoke Maintenance Co",
            "admin_email": "new.admin@smoke.co",
            "admin_full_name": "New Admin",
            "package_id": pkg_id,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["tenant_id"]
    assert body["initial_password"]
    login = api_client.post(
        "/api/v1/auth/login",
        json={"identifier": "new.admin@smoke.co", "password": body["initial_password"]},
    )
    assert login.status_code == 200, login.text
    assert login.json().get("access_token")


def test_provision_tenant_duplicate_email_conflict(api_client, db_session, platform_admin):
    packages = ensure_default_packages(db_session)
    db_session.commit()
    pkg_id = str(packages["starter"].id)
    payload = {
        "tenant_name": "First Co",
        "admin_email": "dup.admin@smoke.co",
        "admin_full_name": "Dup Admin",
        "admin_password": "Password123!",
        "package_id": pkg_id,
    }
    first = api_client.post(
        "/api/v1/platform/tenants",
        headers=auth_header(platform_admin),
        json=payload,
    )
    assert first.status_code == 201, first.text
    second = api_client.post(
        "/api/v1/platform/tenants",
        headers=auth_header(platform_admin),
        json={**payload, "tenant_name": "Second Co"},
    )
    assert_api_error(second, status=409, code="EMAIL_ALREADY_EXISTS")


def test_delete_tenant_soft_deletes_and_hides_from_list(api_client, db_session, platform_admin):
    packages = ensure_default_packages(db_session)
    db_session.commit()
    created = api_client.post(
        "/api/v1/platform/tenants",
        headers=auth_header(platform_admin),
        json={
            "tenant_name": "Delete Me Co",
            "admin_email": "delete.me@smoke.co",
            "admin_full_name": "Delete Me",
            "package_id": str(packages["starter"].id),
            "valid_until": "2030-01-15",
        },
    )
    assert created.status_code == 201, created.text
    tenant_id = created.json()["tenant_id"]

    deleted = api_client.delete(
        f"/api/v1/platform/tenants/{tenant_id}",
        headers=auth_header(platform_admin),
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["status"] == "deleted"

    listed = api_client.get(
        "/api/v1/platform/maintenance-companies",
        headers=auth_header(platform_admin),
    )
    assert listed.status_code == 200
    assert all(row["id"] != tenant_id for row in listed.json())


def test_update_package_and_tenant_license(api_client, db_session, platform_admin):
    packages = ensure_default_packages(db_session)
    db_session.commit()
    starter = packages["starter"]
    patched = api_client.patch(
        f"/api/v1/platform/packages/{starter.id}",
        headers=auth_header(platform_admin),
        json={"name": "Starter Plus", "limits_json": {"max_users": 42, "max_sites": 7}},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["name"] == "Starter Plus"
    assert patched.json()["limits_json"]["max_users"] == 42

    created = api_client.post(
        "/api/v1/platform/tenants",
        headers=auth_header(platform_admin),
        json={
            "tenant_name": "License Co",
            "admin_email": "license.co@smoke.co",
            "admin_full_name": "License Admin",
            "package_id": str(starter.id),
        },
    )
    assert created.status_code == 201, created.text
    tenant_id = created.json()["tenant_id"]
    pro = packages["pro"]
    license_res = api_client.put(
        f"/api/v1/platform/tenants/{tenant_id}/license",
        headers=auth_header(platform_admin),
        json={"package_id": str(pro.id), "status": "trial", "valid_until": "2031-06-01"},
    )
    assert license_res.status_code == 200, license_res.text
    body = license_res.json()
    assert body["plan"] == "pro"
    assert body["status"] == "trial"
    assert body["valid_until"] == "2031-06-01"
