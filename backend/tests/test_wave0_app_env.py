"""Wave 0 APP_ENV tests (NT-104)."""

from datetime import date, timedelta

import pytest

from app.models import SubscriptionPackage, TenantSubscription
from app.services.platform_bootstrap import ensure_default_packages
from app.services.subscription import is_subscription_active


def test_development_bypasses_suspended(monkeypatch, db_session, sample_tenant):
    monkeypatch.setenv("APP_ENV", "development")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    pkg = packages["trial"]
    row = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=pkg.id,
        status="suspended",
    )
    db_session.add(row)
    db_session.commit()

    assert is_subscription_active(db_session, sample_tenant) is True

    get_settings.cache_clear()


def test_production_enforces_suspended(monkeypatch, db_session, sample_tenant):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    pkg = packages["trial"]
    row = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=pkg.id,
        status="suspended",
    )
    db_session.add(row)
    db_session.commit()

    assert is_subscription_active(db_session, sample_tenant) is False

    get_settings.cache_clear()


def test_production_expired_valid_until(monkeypatch, db_session, sample_tenant):
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    pkg = packages["trial"]
    row = TenantSubscription(
        tenant_id=sample_tenant.id,
        package_id=pkg.id,
        status="active",
        valid_until=date.today() - timedelta(days=1),
    )
    db_session.add(row)
    db_session.commit()

    assert is_subscription_active(db_session, sample_tenant) is False

    get_settings.cache_clear()


def test_demo_bypasses_freeze(monkeypatch, db_session, sample_tenant):
    monkeypatch.setenv("APP_ENV", "demo")
    from app.config import get_settings

    get_settings.cache_clear()

    packages = ensure_default_packages(db_session)
    pkg = packages["trial"]
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=pkg.id,
            status="expired",
        )
    )
    db_session.commit()

    assert is_subscription_active(db_session, sample_tenant) is True

    get_settings.cache_clear()
