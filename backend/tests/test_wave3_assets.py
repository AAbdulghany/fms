"""Wave 3 backend tests: NT-116 (AI scheduling stub) and NT-120 (feature gate).

Covers:
- GET /assets/maintenance-calendar quarterly/yearly scoping
- GET /assets 403 when tenant lacks 'assets' feature (env=production)
- POST /assets/{asset_id}/ai-scheduling/stub returns 501 (with and without feature)
- client_admin scoping on calendar
- GET /users/me includes features list
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import (
    Asset,
    MaintenanceSchedule,
    ReportTemplate,
    Site,
    Client,
    SubscriptionPackage,
    Tenant,
    TenantSubscription,
    User,
    UserRole,
    UserSiteScope,
)
from app.services.platform_bootstrap import ensure_default_packages
from tests.api_helpers import auth_header


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
        email="admin_w3@test.com",
        password_hash=hash_password("pass123"),
        full_name="Admin Wave3",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def enterprise_subscription(db_session, sample_tenant, packages):
    """Give sample_tenant an enterprise subscription (includes ai_maintenance)."""
    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=packages["enterprise"].id,
        status="active",
    )
    db_session.add(sub)
    db_session.commit()
    return sub


@pytest.fixture
def starter_subscription(db_session, sample_tenant, packages):
    """Give sample_tenant a starter subscription (no ai_maintenance)."""
    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=packages["starter"].id,
        status="active",
    )
    db_session.add(sub)
    db_session.commit()
    return sub


@pytest.fixture
def report_template(db_session, sample_tenant):
    tmpl = ReportTemplate(
        tenant_id=sample_tenant.id,
        name="Test Template",
        code="TEST-TMPL",
        schema_json={"fields": []},
        version=1,
        is_active=True,
    )
    db_session.add(tmpl)
    db_session.commit()
    return tmpl


@pytest.fixture
def site_with_asset(db_session, sample_tenant, sample_client, report_template):
    """Create a site with an asset that has a maintenance schedule due this year."""
    site = Site(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        name="Test Site W3",
    )
    db_session.add(site)
    db_session.flush()

    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=site.id,
        name="Test HVAC Unit",
        category="HVAC",
    )
    db_session.add(asset)
    db_session.flush()

    # Schedule due in current year Q1
    now = datetime.now(timezone.utc)
    due = now.replace(month=2, day=15)  # Feb (Q1)
    if due < now:
        due = now + timedelta(days=30)

    sched = MaintenanceSchedule(
        tenant_id=sample_tenant.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="monthly",
        next_due_at=due,
        is_active=True,
    )
    db_session.add(sched)
    db_session.commit()

    return {"site": site, "asset": asset, "schedule": sched}


# ---------------------------------------------------------------------------
# NT-120: /users/me includes features
# ---------------------------------------------------------------------------


def test_users_me_includes_features(api_client, db_session, admin_user, starter_subscription):
    """GET /users/me should return features list from subscription."""
    res = api_client.get("/api/v1/users/me", headers=auth_header(admin_user))
    assert res.status_code == 200
    data = res.json()
    assert "features" in data
    assert isinstance(data["features"], list)
    assert "assets" in data["features"]


def test_users_me_enterprise_features(api_client, db_session, admin_user, enterprise_subscription):
    """Enterprise subscription exposes ai_maintenance feature in /users/me."""
    res = api_client.get("/api/v1/users/me", headers=auth_header(admin_user))
    assert res.status_code == 200
    data = res.json()
    assert "ai_maintenance" in data["features"]


# ---------------------------------------------------------------------------
# NT-120: Feature gate for assets (env=production)
# ---------------------------------------------------------------------------


def test_assets_feature_gate_production(api_client, db_session, sample_tenant, packages, monkeypatch):
    """When in production and tenant has no subscription, assets endpoint returns 403."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings
    get_settings.cache_clear()

    # Tenant with no_features package (manual — no subscription row)
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="nofeature@test.com",
        password_hash=hash_password("pass123"),
        full_name="No Feature",
        role=UserRole.company_admin,
        is_active=True,
    )
    # Assign a package that has no 'assets' feature
    empty_pkg = SubscriptionPackage(
        code="empty_test",
        name="Empty",
        features_json=[],
        limits_json={"max_users": 5},
        is_active=True,
    )
    db_session.add(empty_pkg)
    db_session.add(user)
    db_session.flush()

    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=empty_pkg.id,
        status="active",
    )
    db_session.add(sub)
    db_session.commit()

    res = api_client.get("/api/v1/assets", headers=auth_header(user))
    assert res.status_code == 403
    assert res.json()["detail"] == "FEATURE_NOT_AVAILABLE"

    get_settings.cache_clear()


def test_assets_feature_gate_bypassed_in_dev(api_client, db_session, admin_user, monkeypatch):
    """In dev env, feature gate is bypassed even without subscription."""
    monkeypatch.setenv("APP_ENV", "development")
    from app.config import get_settings
    get_settings.cache_clear()

    res = api_client.get("/api/v1/assets", headers=auth_header(admin_user))
    # Should succeed (bypass license check in dev)
    assert res.status_code == 200

    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Maintenance calendar endpoint
# ---------------------------------------------------------------------------


def test_calendar_quarterly_returns_events(
    api_client, db_session, admin_user, site_with_asset, starter_subscription
):
    """GET /assets/maintenance-calendar (quarterly) returns schedule events for current year."""
    year = datetime.now(timezone.utc).year
    res = api_client.get(
        f"/api/v1/assets/maintenance-calendar?view=quarterly&year={year}",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    event = events[0]
    assert "asset_id" in event
    assert "schedule_id" in event
    assert "frequency" in event
    assert "due_at" in event
    assert "bucket" in event


def test_calendar_yearly_returns_month_bucket(
    api_client, db_session, admin_user, site_with_asset, starter_subscription
):
    """Yearly view returns month-based buckets (1-12)."""
    year = datetime.now(timezone.utc).year
    res = api_client.get(
        f"/api/v1/assets/maintenance-calendar?view=yearly&year={year}",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 200
    events = res.json()
    if events:
        bucket = events[0]["bucket"]
        # bucket is either int (month 1-12) or string representation
        bucket_val = int(str(bucket).lstrip("Q")) if isinstance(bucket, str) else int(bucket)
        assert 1 <= bucket_val <= 12


def test_calendar_wrong_year_returns_empty(
    api_client, db_session, admin_user, site_with_asset, starter_subscription
):
    """Requesting a different year returns no events (all schedules are current year)."""
    res = api_client.get(
        "/api/v1/assets/maintenance-calendar?view=quarterly&year=1990",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 200
    assert res.json() == []


def test_calendar_client_admin_scoping(
    api_client, db_session, sample_tenant, sample_client, site_with_asset, packages
):
    """client_admin only sees events for their own client."""
    sub = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=packages["starter"].id,
        status="active",
    )
    db_session.add(sub)

    # client_admin for sample_client
    client_admin = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="client_admin_w3@test.com",
        password_hash=hash_password("pass123"),
        full_name="Client Admin W3",
        role=UserRole.client_admin,
        client_id=sample_client.id,
        is_active=True,
    )
    db_session.add(client_admin)
    db_session.commit()

    year = datetime.now(timezone.utc).year
    res = api_client.get(
        f"/api/v1/assets/maintenance-calendar?view=quarterly&year={year}",
        headers=auth_header(client_admin),
    )
    assert res.status_code == 200
    events = res.json()
    # Events should all belong to sample_client
    for event in events:
        assert event["client_id"] == str(sample_client.id)


def test_calendar_client_filter_param(
    api_client, db_session, admin_user, sample_client, site_with_asset, starter_subscription
):
    """client_id query param filters calendar to that client only."""
    year = datetime.now(timezone.utc).year
    res = api_client.get(
        f"/api/v1/assets/maintenance-calendar?view=quarterly&year={year}&client_id={sample_client.id}",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 200
    events = res.json()
    for event in events:
        assert event["client_id"] == str(sample_client.id)


# ---------------------------------------------------------------------------
# NT-116: AI scheduling stub
# ---------------------------------------------------------------------------


def test_ai_stub_without_feature_returns_403(
    api_client, db_session, admin_user, sample_tenant, site_with_asset, monkeypatch
):
    """AI stub endpoint returns 403 when tenant lacks ai_maintenance feature."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings
    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=packages["starter"].id,
            status="active",
        )
    )
    db_session.commit()

    asset_id = site_with_asset["asset"].id
    res = api_client.post(
        f"/api/v1/assets/{asset_id}/ai-scheduling/stub",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "FEATURE_NOT_AVAILABLE"

    get_settings.cache_clear()


def test_ai_stub_with_feature_returns_501(
    api_client, db_session, admin_user, sample_tenant, site_with_asset, monkeypatch
):
    """AI stub returns 501 even with ai_maintenance feature enabled (never succeeds)."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings
    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=packages["enterprise"].id,
            status="active",
        )
    )
    db_session.commit()

    asset_id = site_with_asset["asset"].id
    res = api_client.post(
        f"/api/v1/assets/{asset_id}/ai-scheduling/stub",
        headers=auth_header(admin_user),
    )
    assert res.status_code == 501
    assert res.json()["detail"] == "AI_SCHEDULING_NOT_AVAILABLE"

    get_settings.cache_clear()


def test_ai_stub_dev_env_returns_501(
    api_client, db_session, admin_user, site_with_asset
):
    """In dev env (license bypassed), stub still returns 501 (feature always bypassed in dev)."""
    asset_id = site_with_asset["asset"].id
    res = api_client.post(
        f"/api/v1/assets/{asset_id}/ai-scheduling/stub",
        headers=auth_header(admin_user),
    )
    # In dev, require_feature is bypassed, so stub returns 501
    assert res.status_code == 501
    assert res.json()["detail"] == "AI_SCHEDULING_NOT_AVAILABLE"
