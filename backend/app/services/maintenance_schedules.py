"""Maintenance schedule helpers (Phase 3.1)."""

from __future__ import annotations

from datetime import datetime, date, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Asset, MaintenanceSchedule, ReportTemplate, WorkOrder, WorkOrderSource, WorkOrderStatus

FREQUENCY_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "yearly": 365,
}

PREVENTIVE_LEAD_DAYS = 7


def compute_next_due(frequency: str, custom_days: int | None = None, from_dt: datetime | None = None) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    if frequency == "custom" and custom_days:
        delta = custom_days
    else:
        delta = FREQUENCY_DAYS.get(frequency, 30)
    return base + timedelta(days=delta)


def _parse_frequency(freq_store: str) -> tuple[str, int | None]:
    freq_key = freq_store
    custom: int | None = None
    if freq_key.startswith("custom_"):
        try:
            custom = int(freq_key.split("_")[1].replace("d", ""))
            freq_key = "custom"
        except ValueError:
            freq_key = "monthly"
    return freq_key, custom


def _advance_schedule_next_due(sched: MaintenanceSchedule, from_dt: datetime) -> None:
    freq_key, custom = _parse_frequency(sched.frequency)
    sched.next_due_at = compute_next_due(freq_key, custom, from_dt)
    sched.last_generated_at = None


def _has_open_preventive_wo(db: Session, asset_id: UUID, template_id: UUID) -> bool:
    existing = db.scalar(
        select(WorkOrder.id)
        .where(
            WorkOrder.asset_id == asset_id,
            WorkOrder.source == WorkOrderSource.preventive,
            WorkOrder.template_id == template_id,
            WorkOrder.status.notin_([WorkOrderStatus.closed, WorkOrderStatus.cancelled]),
        )
        .limit(1)
    )
    return existing is not None


def create_schedule(
    db: Session,
    *,
    tenant_id: UUID,
    asset_id: UUID,
    template_id: UUID,
    frequency: str,
    custom_days: int | None = None,
    last_maintenance_date: date | None = None,
    installed_on: date | None = None,
) -> MaintenanceSchedule:
    tmpl = db.get(ReportTemplate, template_id)
    if not tmpl or tmpl.tenant_id != tenant_id:
        raise ValueError("INVALID_TEMPLATE")
    freq_store = frequency if frequency != "custom" else f"custom_{custom_days or 30}d"
    # A1: anchor priority — last_maintenance_date > installed_on > today
    # If the computed next_due_at lands in the past, leave it (overdue); do NOT skip to today+interval.
    if last_maintenance_date:
        base = datetime.combine(last_maintenance_date, datetime.min.time(), tzinfo=timezone.utc)
    elif installed_on:
        base = datetime.combine(installed_on, datetime.min.time(), tzinfo=timezone.utc)
    else:
        base = datetime.now(timezone.utc)
    sched = MaintenanceSchedule(
        tenant_id=tenant_id,
        asset_id=asset_id,
        template_id=template_id,
        frequency=freq_store,
        next_due_at=compute_next_due(frequency, custom_days, base),
    )
    db.add(sched)
    db.flush()
    return sched


def run_due_schedules(db: Session, tenant_id: UUID | None = None) -> int:
    """Create preventive WOs for schedules due within PREVENTIVE_LEAD_DAYS.

    Rules:
    - A WO is triggered when next_due_at - PREVENTIVE_LEAD_DAYS <= now.
    - Skipped if an open preventive WO already exists for the same asset + template.
    - next_due_at is advanced only when the due date has actually passed (next_due_at <= now).
    """
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=PREVENTIVE_LEAD_DAYS)
    q = select(MaintenanceSchedule).where(
        MaintenanceSchedule.is_active.is_(True),
        MaintenanceSchedule.next_due_at <= horizon,
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

        # Dedup: skip if an open preventive WO already exists for this asset + template
        if _has_open_preventive_wo(db, asset.id, sched.template_id):
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
            description=(
                f"Scheduled maintenance ({sched.frequency})"
                f" — due {sched.next_due_at.date().isoformat()}"
            ),
            template_id=sched.template_id,
        )
        db.add(wo)
        sched.last_generated_at = now

        # Advance next_due_at only when the due date has actually passed
        if sched.next_due_at <= now:
            freq_key, custom = _parse_frequency(sched.frequency)
            sched.next_due_at = compute_next_due(freq_key, custom, now)

        created += 1
    db.flush()
    return created
