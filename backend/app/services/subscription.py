"""Subscription resolution — table-first with legacy JSON fallback (Wave 0+)."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import SubscriptionPackage, Tenant, TenantSubscription, User

DEFAULT_SUBSCRIPTION: dict[str, Any] = {
    "plan": "trial",
    "status": "active",
    "valid_until": None,
    "max_sites": 10,
    "max_users": 25,
    "features": ["assets", "invoices", "csv_import"],
}


def _env_bypasses_license() -> bool:
    env = get_settings().app_env.lower()
    return env in ("development", "demo")


def _tenant_subscription_row(db: Session, tenant_id) -> TenantSubscription | None:
    return db.scalar(
        select(TenantSubscription)
        .where(TenantSubscription.tenant_id == tenant_id)
        .options(joinedload(TenantSubscription.package))
    )


def get_subscription(db: Session, tenant: Tenant) -> dict[str, Any]:
    row = _tenant_subscription_row(db, tenant.id)
    if row and row.package:
        pkg = row.package
        limits = pkg.limits_json or {}
        overrides = row.overrides_json or {}
        features = overrides.get("features") or pkg.features_json or []
        return {
            "plan": pkg.code,
            "package_id": pkg.id,
            "status": row.status,
            "valid_until": row.valid_until,
            "max_sites": overrides.get("max_sites", limits.get("max_sites", 10)),
            "max_users": overrides.get("max_users", limits.get("max_users", 25)),
            "features": list(features),
        }

    settings = tenant.settings_json or {}
    sub = settings.get("subscription") or {}
    return {**DEFAULT_SUBSCRIPTION, **sub}


def assign_tenant_subscription(
    db: Session,
    tenant: Tenant,
    *,
    package_id,
    status: str = "active",
    valid_until: date | None = None,
    overrides_json: dict[str, Any] | None = None,
) -> TenantSubscription:
    pkg = db.get(SubscriptionPackage, package_id)
    if not pkg or not pkg.is_active:
        raise ValueError("INVALID_PACKAGE")
    row = _tenant_subscription_row(db, tenant.id)
    if row:
        row.package_id = pkg.id
        row.status = status
        row.valid_until = valid_until
        if overrides_json is not None:
            row.overrides_json = overrides_json
    else:
        row = TenantSubscription(
            tenant_id=tenant.id,
            package_id=pkg.id,
            status=status,
            valid_until=valid_until,
            overrides_json=overrides_json or {},
        )
        db.add(row)
    db.flush()
    return row


def update_subscription(db: Session, tenant: Tenant, patch: dict[str, Any]) -> dict[str, Any]:
    """Update tenant license — table-first when package_id or plan provided."""
    if patch.get("package_id"):
        assign_tenant_subscription(
            db,
            tenant,
            package_id=patch["package_id"],
            status=patch.get("status") or "active",
            valid_until=patch.get("valid_until"),
            overrides_json={
                k: patch[k]
                for k in ("max_users", "max_sites", "features")
                if k in patch and patch[k] is not None
            }
            or None,
        )
        if patch.get("features") is not None:
            row = _tenant_subscription_row(db, tenant.id)
            if row:
                row.overrides_json = {**(row.overrides_json or {}), "features": patch["features"]}
        return get_subscription(db, tenant)

    if patch.get("plan"):
        pkg = get_package_by_code(db, str(patch["plan"]).lower())
        if pkg:
            assign_tenant_subscription(
                db,
                tenant,
                package_id=pkg.id,
                status=patch.get("status") or "active",
                valid_until=patch.get("valid_until"),
            )
            return get_subscription(db, tenant)

    # Legacy JSON fallback for partial patches without package
    settings = dict(tenant.settings_json or {})
    current_settings = settings.get("subscription") or {}
    merged = {**DEFAULT_SUBSCRIPTION, **current_settings, **{k: v for k, v in patch.items() if v is not None}}
    settings["subscription"] = merged
    tenant.settings_json = settings
    row = _tenant_subscription_row(db, tenant.id)
    if row and patch.get("status"):
        row.status = patch["status"]
    if row and patch.get("valid_until") is not None:
        row.valid_until = patch["valid_until"]
    return get_subscription(db, tenant)


def is_subscription_active(db: Session, tenant: Tenant) -> bool:
    if _env_bypasses_license():
        return True
    sub = get_subscription(db, tenant)
    st = sub.get("status", "active")
    if st in ("suspended", "expired"):
        return False
    valid_until = sub.get("valid_until")
    if valid_until:
        try:
            until = date.fromisoformat(str(valid_until)[:10])
            if until < date.today():
                return False
        except ValueError:
            pass
    return True


def has_feature(db: Session, tenant: Tenant, feature: str) -> bool:
    if _env_bypasses_license():
        return True
    sub = get_subscription(db, tenant)
    features = sub.get("features") or []
    return feature in features


def ensure_active_subscription(db: Session, user: User, tenant: Tenant) -> None:
    if user.is_platform_admin:
        return
    if not is_subscription_active(db, tenant):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="SUBSCRIPTION_SUSPENDED",
        )


def get_package_by_code(db: Session, code: str) -> SubscriptionPackage | None:
    return db.scalar(select(SubscriptionPackage).where(SubscriptionPackage.code == code))
