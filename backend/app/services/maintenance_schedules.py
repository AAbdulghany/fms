"""Maintenance schedule helpers (Phase 3.1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import MaintenanceSchedule, ReportTemplate, WorkOrder, WorkOrderSource, WorkOrderStatus


FREQUENCY_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
}


def compute_next_due(frequency: str, custom_days: int | None = None, from_dt: datetime | None = None) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    if frequency == "custom" and custom_days:
        delta = custom_days
    else:
        delta = FREQUENCY_DAYS.get(frequency, 30)
    return base + timedelta(days=delta)


def create_schedule(
    db: Session,
    *,
    tenant_id: UUID,
    asset_id: UUID,
    template_id: UUID,
    frequency: str,
    custom_days: int | None = None,
) -> MaintenanceSchedule:
    tmpl = db.get(ReportTemplate, template_id)
    if not tmpl or tmpl.tenant_id != tenant_id:
        raise ValueError("INVALID_TEMPLATE")
    freq_store = frequency if frequency != "custom" else f"custom_{custom_days or 30}d"
    sched = MaintenanceSchedule(
        tenant_id=tenant_id,
        asset_id=asset_id,
        template_id=template_id,
        frequency=freq_store,
        next_due_at=compute_next_due(frequency, custom_days),
    )
    db.add(sched)
    db.flush()
    return sched


def run_due_schedules(db: Session, tenant_id: UUID | None = None) -> int:
    """Create preventive work orders for due schedules. Returns count created."""
    now = datetime.now(timezone.utc)
    q = select(MaintenanceSchedule).where(
        MaintenanceSchedule.is_active.is_(True),
        MaintenanceSchedule.next_due_at <= now,
    )
    if tenant_id:
        q = q.where(MaintenanceSchedule.tenant_id == tenant_id)
    q = q.options(joinedload(MaintenanceSchedule.asset).joinedload(Asset.site))
    schedules = db.scalars(q).all()
    created = 0
    for sched in schedules:
        asset = sched.asset
        if not asset or not asset.site:
            continue
        site = asset.site
        wo = WorkOrder(
            tenant_id=sched.tenant_id,
            client_id=site.client_id,
            site_id=asset.site_id,
            asset_id=asset.id,
            source=WorkOrderSource.preventive,
            status=WorkOrderStatus.created,
            title=f"Preventive maintenance: {asset.name}",
            description=f"Scheduled maintenance ({sched.frequency})",
            template_id=sched.template_id,
        )
        db.add(wo)
        sched.last_generated_at = now
        freq_key = sched.frequency
        custom = None
        if freq_key.startswith("custom_"):
            try:
                custom = int(freq_key.split("_")[1].replace("d", ""))
                freq_key = "custom"
            except ValueError:
                freq_key = "monthly"
        sched.next_due_at = compute_next_due(freq_key, custom, now)
        created += 1
    db.flush()
    return created
