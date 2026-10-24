"""Automation Plan #1 — read-side queue for later triggers / reminders.

Does not create dummy reminder rows. Consumers (cron, notify worker) pull
schedules whose ``ai_meta_json.automation_ready`` is true and act on the
live ``next_due_at`` + ``next_action_wo_id`` only.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Asset, MaintenanceSchedule


def list_pm_automation_candidates(
    db: Session,
    *,
    tenant_id: UUID | None = None,
    within_days: int = 7,
) -> list[dict[str, Any]]:
    """Return schedules due within ``within_days`` (including overdue).

    Shape is stable for future notifiers — extend fields carefully.
    """
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=max(0, within_days))
    q = (
        select(MaintenanceSchedule)
        .where(MaintenanceSchedule.is_active.is_(True))
        .where(MaintenanceSchedule.next_due_at <= horizon)
        .options(joinedload(MaintenanceSchedule.asset).joinedload(Asset.site))
    )
    if tenant_id is not None:
        q = q.where(MaintenanceSchedule.tenant_id == tenant_id)

    rows: list[dict[str, Any]] = []
    for sched in db.scalars(q).unique().all():
        meta = dict(sched.ai_meta_json or {})
        if meta.get("dummy_reminders") is True:
            continue
        asset = sched.asset
        due = sched.next_due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        rows.append(
            {
                "schedule_id": str(sched.id),
                "tenant_id": str(sched.tenant_id),
                "asset_id": str(sched.asset_id),
                "asset_name": asset.name if asset else None,
                "site_id": str(asset.site_id) if asset else None,
                "frequency": sched.frequency,
                "next_due_at": due.isoformat(),
                "days_until_next": (due.date() - now.date()).days,
                "overdue": due <= now,
                "next_action_wo_id": meta.get("next_action_wo_id"),
                "automation_ready": bool(meta.get("automation_ready", True)),
                "projected_occurrence_count": meta.get("projected_occurrence_count"),
                "eol_at": meta.get("eol_at"),
            }
        )
    rows.sort(key=lambda r: r["next_due_at"])
    return rows
