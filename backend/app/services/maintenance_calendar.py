"""Maintenance calendar query service (Wave 3 / NT-117)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Asset, MaintenanceSchedule, Site, User, UserRole, UserSiteScope


def _quarter_of(dt: datetime) -> int:
    return (dt.month - 1) // 3 + 1


def get_calendar_events(
    db: Session,
    *,
    tenant_id: UUID,
    current_user: User,
    view: str = "quarterly",
    year: int | None = None,
    month: int | None = None,
    client_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """Return maintenance calendar events scoped by RBAC and filtered by year."""
    if year is None:
        year = datetime.now(timezone.utc).year

    q = (
        select(MaintenanceSchedule)
        .join(MaintenanceSchedule.asset)
        .join(Asset.site)
        .where(MaintenanceSchedule.tenant_id == tenant_id)
        .where(MaintenanceSchedule.is_active.is_(True))
        .options(joinedload(MaintenanceSchedule.asset).joinedload(Asset.site))
    )

    # RBAC scoping
    if current_user.role == UserRole.site_manager:
        scoped_site_ids = list(
            db.scalars(
                select(UserSiteScope.site_id).where(UserSiteScope.user_id == current_user.id)
            ).all()
        )
        if not scoped_site_ids:
            return []
        q = q.where(Asset.site_id.in_(scoped_site_ids))
    elif current_user.role == UserRole.client_admin and current_user.client_id:
        q = q.where(Site.client_id == current_user.client_id)

    if client_id is not None:
        q = q.where(Site.client_id == client_id)

    schedules = db.scalars(q).unique().all()

    events: list[dict[str, Any]] = []
    for sched in schedules:
        asset = sched.asset
        if not asset:
            continue
        site = asset.site
        if not site:
            continue
        due = sched.next_due_at
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if due.year != year:
            continue
        if view == "monthly":
            if month is not None and due.month != month:
                continue
            bucket = due.day
        elif view == "quarterly":
            bucket = _quarter_of(due)
        else:
            bucket = due.month
        events.append(
            {
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "site_id": str(asset.site_id),
                "client_id": str(site.client_id),
                "schedule_id": str(sched.id),
                "frequency": sched.frequency,
                "due_at": due.isoformat(),
                "bucket": bucket,
            }
        )

    return events
