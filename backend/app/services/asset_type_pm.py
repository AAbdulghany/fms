"""A1/A3 — Propagate AssetType default PM frequency to linked assets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, MaintenanceSchedule, ReportTemplate
from app.models.asset_types import AssetType
from app.services.maintenance_schedules import (
    compute_next_due,
    create_schedule,
    ensure_next_preventive_wo,
    normalize_frequency,
)


def apply_type_pm_to_assets(
    db: Session,
    *,
    tenant_id: UUID,
    asset_type: AssetType,
    only_missing: bool = False,
) -> dict[str, Any]:
    """Create or update active MaintenanceSchedule rows for assets of this type.

    Requires ``default_frequency`` and ``default_report_template_id`` on the type.
    When *only_missing* is True, assets that already have an active schedule are skipped.
    """
    freq = (asset_type.default_frequency or "").strip()
    tmpl_id = asset_type.default_report_template_id
    if not freq or not tmpl_id:
        return {
            "ok": False,
            "reason": "TYPE_MISSING_PM_DEFAULTS",
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

    tmpl = db.get(ReportTemplate, tmpl_id)
    if not tmpl or tmpl.tenant_id != tenant_id:
        return {
            "ok": False,
            "reason": "INVALID_TEMPLATE",
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

    assets = list(
        db.scalars(
            select(Asset).where(
                Asset.tenant_id == tenant_id,
                Asset.asset_type_id == asset_type.id,
            )
        ).all()
    )
    created = updated = skipped = 0
    for asset in assets:
        active = list(
            db.scalars(
                select(MaintenanceSchedule).where(
                    MaintenanceSchedule.asset_id == asset.id,
                    MaintenanceSchedule.is_active.is_(True),
                )
            ).all()
        )
        if active:
            if only_missing:
                skipped += 1
                continue
            # Update first active schedule to match type defaults
            sched = active[0]
            sched.template_id = tmpl_id
            sched.frequency = normalize_frequency(freq)
            sched.next_due_at = compute_next_due(freq, None, datetime.now(timezone.utc))
            ensure_next_preventive_wo(db, sched)
            updated += 1
            continue
        create_schedule(
            db,
            tenant_id=tenant_id,
            asset_id=asset.id,
            template_id=tmpl_id,
            frequency=freq,
            installed_on=getattr(asset, "installed_on", None),
        )
        created += 1

    db.flush()
    return {
        "ok": True,
        "reason": None,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "asset_count": len(assets),
    }
