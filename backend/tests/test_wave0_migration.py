"""Wave 0 migration tests (NT-103)."""

from uuid import uuid4

from app.models import SubscriptionPackage, Tenant, TenantSubscription
from app.services.platform_bootstrap import (
    ensure_default_packages,
    migrate_tenant_subscription_from_settings,
    run_wave0_platform_bootstrap,
)
from app.services.subscription import get_subscription


def test_bootstrap_seeds_packages(db_session):
    stats = run_wave0_platform_bootstrap(db_session)
    db_session.commit()
    assert stats["packages"] >= 4
    rows = db_session.query(SubscriptionPackage).all()
    codes = {r.code for r in rows}
    assert {"trial", "starter", "pro", "enterprise"}.issubset(codes)


def test_migrate_legacy_settings_json(db_session, sample_tenant):
    sample_tenant.settings_json = {
        "subscription": {
            "plan": "pro",
            "status": "active",
            "valid_until": "2027-01-01",
            "features": ["assets", "invoices", "csv_import"],
        }
    }
    db_session.commit()

    packages = ensure_default_packages(db_session)
    row = migrate_tenant_subscription_from_settings(db_session, sample_tenant, packages)
    db_session.commit()

    assert row is not None
    assert row.package.code == "pro"
    sub = get_subscription(db_session, sample_tenant)
    assert sub["plan"] == "pro"
    assert "csv_import" in sub["features"]


def test_migration_idempotent(db_session):
    tenant = Tenant(id=uuid4(), name="T2", status="active", settings_json={})
    db_session.add(tenant)
    db_session.commit()
    run_wave0_platform_bootstrap(db_session)
    db_session.commit()
    count1 = db_session.query(TenantSubscription).filter_by(tenant_id=tenant.id).count()
    run_wave0_platform_bootstrap(db_session)
    db_session.commit()
    count2 = db_session.query(TenantSubscription).filter_by(tenant_id=tenant.id).count()
    assert count1 == 1
    assert count2 == 1
