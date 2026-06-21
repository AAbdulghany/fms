"""Platform subscription packages, settings seed, and legacy migration (Wave 0)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PlatformSettings, SubscriptionPackage, Tenant, TenantSubscription

DEFAULT_PACKAGES: list[dict[str, Any]] = [
    {
        "code": "trial",
        "name": "Trial",
        "features_json": ["assets", "invoices"],
        "limits_json": {"max_users": 5, "max_sites": 2, "max_assets": 50},
    },
    {
        "code": "starter",
        "name": "Starter",
        "features_json": ["assets", "invoices"],
        "limits_json": {"max_users": 10, "max_sites": 5, "max_assets": 200},
    },
    {
        "code": "pro",
        "name": "Pro",
        "features_json": ["assets", "invoices", "csv_import", "advanced_scheduling"],
        "limits_json": {"max_users": 25, "max_sites": 15, "max_assets": 1000},
    },
    {
        "code": "enterprise",
        "name": "Enterprise",
        "features_json": [
            "assets",
            "invoices",
            "csv_import",
            "advanced_scheduling",
            "ai_maintenance",
        ],
        "limits_json": {"max_users": 100, "max_sites": 50, "max_assets": 10000},
    },
]

DEFAULT_BRANDING = {
    "company_name": "Orbit Software",
    "copyright_watermark": "© Orbit Software. All rights reserved.",
}


def ensure_default_packages(db: Session) -> dict[str, SubscriptionPackage]:
    """Insert catalog packages if missing; return code → row map."""
    by_code: dict[str, SubscriptionPackage] = {}
    for spec in DEFAULT_PACKAGES:
        row = db.scalar(select(SubscriptionPackage).where(SubscriptionPackage.code == spec["code"]))
        if not row:
            row = SubscriptionPackage(
                code=spec["code"],
                name=spec["name"],
                features_json=list(spec["features_json"]),
                limits_json=dict(spec["limits_json"]),
                is_active=True,
            )
            db.add(row)
            db.flush()
        by_code[spec["code"]] = row
    return by_code


def ensure_platform_settings(db: Session) -> PlatformSettings:
    row = db.get(PlatformSettings, "global")
    if not row:
        row = PlatformSettings(
            key="global",
            branding_json=dict(DEFAULT_BRANDING),
            config_json={},
        )
        db.add(row)
        db.flush()
    return row


def _parse_valid_until(raw: Any) -> date | None:
    if not raw:
        return None
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    return None


def migrate_tenant_subscription_from_settings(
    db: Session,
    tenant: Tenant,
    packages_by_code: dict[str, SubscriptionPackage],
) -> TenantSubscription | None:
    """Create tenant_subscriptions row from legacy settings_json.subscription if absent."""
    existing = db.scalar(
        select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id)
    )
    if existing:
        return existing

    settings = tenant.settings_json or {}
    legacy = settings.get("subscription") or {}
    plan_code = str(legacy.get("plan") or "trial").lower()
    package = packages_by_code.get(plan_code) or packages_by_code["trial"]

    row = TenantSubscription(
        tenant_id=tenant.id,
        package_id=package.id,
        status=str(legacy.get("status") or "active"),
        valid_until=_parse_valid_until(legacy.get("valid_until")),
        overrides_json={
            k: legacy[k]
            for k in ("max_users", "max_sites", "features")
            if k in legacy and legacy[k] is not None
        },
    )
    db.add(row)
    db.flush()
    return row


def run_wave0_platform_bootstrap(db: Session) -> dict[str, int]:
    """Idempotent Wave 0 bootstrap: packages, platform settings, tenant migration."""
    packages = ensure_default_packages(db)
    ensure_platform_settings(db)
    migrated = 0
    for tenant in db.scalars(select(Tenant)).all():
        before = db.scalar(
            select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id)
        )
        if not before:
            migrate_tenant_subscription_from_settings(db, tenant, packages)
            migrated += 1
    db.flush()
    return {"packages": len(packages), "tenants_migrated": migrated}
