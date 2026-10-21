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


def test_pilot_bypasses_freeze(monkeypatch, db_session, sample_tenant):
    monkeypatch.setenv("APP_ENV", "pilot")
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


def test_demo_alias_bypasses_freeze(monkeypatch, db_session, sample_tenant):
    """`demo` remains accepted as deprecated alias of `pilot` (ENV_REORG wave 1)."""
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


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("development", "development"),
        ("pilot", "pilot"),
        ("production", "production"),
        ("demo", "pilot"),
        ("DEMO", "pilot"),
        (" Pilot ", "pilot"),
        ("dev", "development"),
        ("prod", "production"),
    ],
)
def test_app_env_normalized(raw, expected):
    from app.config import Settings

    assert Settings(app_env=raw).app_env == expected


def test_app_env_rejects_unknown_value():
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(app_env="staging")


@pytest.mark.parametrize(
    ("raw", "is_pilot", "bypasses"),
    [("development", False, True), ("pilot", True, True), ("demo", True, True), ("production", False, False)],
)
def test_app_env_flags(raw, is_pilot, bypasses):
    from app.config import Settings

    settings = Settings(app_env=raw)
    assert settings.is_pilot is is_pilot
    assert settings.bypasses_license is bypasses
