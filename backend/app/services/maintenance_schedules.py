"""Maintenance schedule helpers — Automation Plan #1 core.

Calendar projection until asset aging (EOL), and a single open preventive
"next action" WO that advances when the previous one is finished.
"""

from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from typing import Iterator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Asset, MaintenanceSchedule, ReportTemplate, WorkOrder, WorkOrderSource, WorkOrderStatus
from app.services.asset_metadata import expected_eol_date

FREQUENCY_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "semi_annual": 182,
    "semi-annual": 182,
    "semiannual": 182,
    "yearly": 365,
    "annually": 365,
    "annual": 365,
}

# Canonical keys exposed in UI / asset-type allowlists
CANONICAL_FREQUENCIES = frozenset(
    {"daily", "weekly", "monthly", "quarterly", "semi_annual", "yearly"}
)

PREVENTIVE_LEAD_DAYS = 7
# Safety cap when projecting open-ended schedules (no max_age_years)
_MAX_PROJECTED_OCCURRENCES = 500


def normalize_frequency(frequency: str) -> str:
    """Map aliases to a canonical FREQUENCY_DAYS key."""
    raw = (frequency or "monthly").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "semiannual": "semi_annual",
        "semi_annually": "semi_annual",
        "biannual": "semi_annual",
        "bi_annual": "semi_annual",
        "annually": "yearly",
        "annual": "yearly",
    }
    return aliases.get(raw, raw)


def frequency_interval_days(frequency: str, custom_days: int | None = None) -> int:
    key = normalize_frequency(frequency)
    if key == "custom" and custom_days:
        return max(1, int(custom_days))
    if key.startswith("custom_"):
        try:
            return max(1, int(key.split("_")[1].replace("d", "")))
        except ValueError:
            return 30
    return FREQUENCY_DAYS.get(key, 30)


def compute_next_due(
    frequency: str, custom_days: int | None = None, from_dt: datetime | None = None
) -> datetime:
    base = from_dt or datetime.now(timezone.utc)
    return base + timedelta(days=frequency_interval_days(frequency, custom_days))


def _parse_frequency(freq_store: str) -> tuple[str, int | None]:
    freq_key = normalize_frequency(freq_store)
    custom: int | None = None
    if freq_key.startswith("custom_"):
        try:
            custom = int(freq_key.split("_")[1].replace("d", ""))
            freq_key = "custom"
        except ValueError:
            freq_key = "monthly"
    return freq_key, custom


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def schedule_eol_cutoff(asset: Asset | None) -> datetime | None:
    """Last instant at which PM is still planned (inclusive day of expected EOL)."""
    if not asset:
        return None
    eol = expected_eol_date(asset)
    if not eol:
        return None
    return datetime.combine(eol, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc)


def _advance_schedule_next_due(sched: MaintenanceSchedule, from_dt: datetime) -> None:
    freq_key, custom = _parse_frequency(sched.frequency)
    sched.next_due_at = compute_next_due(freq_key, custom, from_dt)
    sched.last_generated_at = None


_TERMINAL_WO_STATUSES = (
    WorkOrderStatus.completed,
    WorkOrderStatus.verified,
    WorkOrderStatus.closed,
    WorkOrderStatus.cancelled,
    WorkOrderStatus.declined,
)


def _has_open_preventive_wo(db: Session, asset_id: UUID, template_id: UUID | None = None) -> bool:
    """True if a non-terminal preventive WO already covers this asset.

    One open next-action WO per asset (not per template) — avoids duplicates
    in the same month when multiple schedules / ensure calls race.
    """
    q = select(WorkOrder.id).where(
        WorkOrder.asset_id == asset_id,
        WorkOrder.source == WorkOrderSource.preventive,
        WorkOrder.status.notin_(_TERMINAL_WO_STATUSES),
    )
    if template_id is not None:
        # Prefer same-template match first; fall through to any open PM on asset
        same = db.scalar(q.where(WorkOrder.template_id == template_id).limit(1))
        if same is not None:
            return True
    return db.scalar(q.limit(1)) is not None


def _dedupe_open_preventive_wos(db: Session, asset_id: UUID) -> None:
    """Keep the earliest open preventive WO for an asset; cancel the rest."""
    rows = list(
        db.scalars(
            select(WorkOrder)
            .where(
                WorkOrder.asset_id == asset_id,
                WorkOrder.source == WorkOrderSource.preventive,
                WorkOrder.status.notin_(_TERMINAL_WO_STATUSES),
            )
            .order_by(WorkOrder.opened_at.asc())
        ).all()
    )
    for extra in rows[1:]:
        extra.status = WorkOrderStatus.cancelled


def _series_first_due(sched: MaintenanceSchedule, asset: Asset | None) -> datetime:
    """First PM due: install / last-maintenance + interval (never before that anchor)."""
    from app.services.asset_metadata import read_asset_meta

    freq_key, custom = _parse_frequency(sched.frequency)
    base: datetime | None = None
    if asset is not None:
        meta = read_asset_meta(asset)
        last_maint = meta.get("last_maintenance_date")
        if last_maint is not None:
            base = datetime.combine(last_maint, datetime.min.time(), tzinfo=timezone.utc)
        elif asset.installed_on is not None:
            base = datetime.combine(asset.installed_on, datetime.min.time(), tzinfo=timezone.utc)
    if base is not None:
        return compute_next_due(freq_key, custom, base)
    return _aware(sched.next_due_at)


def iter_projected_dues(
    sched: MaintenanceSchedule,
    *,
    range_start: datetime,
    range_end: datetime,
    asset: Asset | None = None,
) -> Iterator[datetime]:
    """Yield dues in [range_start, range_end], forward-only from install/last-maint.

    Never walks backward — the series starts at (anchor + interval) and only
    advances. Capped by asset aging EOL when set.
    """
    interval = timedelta(days=frequency_interval_days(sched.frequency))
    if interval.days < 1:
        return

    asset_ref = asset if asset is not None else getattr(sched, "asset", None)
    eol = schedule_eol_cutoff(asset_ref)
    hard_end = range_end
    if eol is not None and eol < hard_end:
        hard_end = eol

    due = _series_first_due(sched, asset_ref)
    guard = 0
    # Skip forward into the requested window (do not invent earlier dates)
    while due < range_start and due <= hard_end and guard < _MAX_PROJECTED_OCCURRENCES:
        due = due + interval
        guard += 1

    while due <= hard_end and guard < _MAX_PROJECTED_OCCURRENCES:
        if due >= range_start:
            yield due
        due = due + interval
        guard += 1


def _count_projected_until_eol(sched: MaintenanceSchedule, asset: Asset | None) -> int:
    """How many PM occurrences remain from series start through EOL (cap applied)."""
    eol = schedule_eol_cutoff(asset)
    if eol is None:
        # Open-ended: count a year ahead from next due for automation planning
        range_end = _aware(sched.next_due_at) + timedelta(days=365)
    else:
        range_end = eol
    range_start = _series_first_due(sched, asset)
    return sum(
        1
        for _ in iter_projected_dues(
            sched, range_start=range_start, range_end=range_end, asset=asset
        )
    )


def refresh_schedule_automation_meta(
    sched: MaintenanceSchedule,
    asset: Asset | None,
    *,
    next_wo_id: UUID | None = None,
    anchor: str | None = None,
    anchor_date: date | None = None,
) -> dict:
    """Persist trigger-ready series facts on the schedule (no dummy reminders).

    Downstream jobs read ``ai_meta_json`` — they do not invent calendar rows.
    Only the open next-action WO is the live work item.
    """
    now = datetime.now(timezone.utc)
    due = _aware(sched.next_due_at)
    eol = schedule_eol_cutoff(asset)
    days_until_next = (due.date() - now.date()).days
    days_until_eol = (eol.date() - now.date()).days if eol else None
    meta = {
        "plan": "pm_series_v1",
        "automation_ready": True,
        "dummy_reminders": False,
        "frequency": sched.frequency,
        "interval_days": frequency_interval_days(sched.frequency),
        "anchor": anchor,
        "anchor_date": anchor_date.isoformat() if anchor_date else None,
        "next_due_at": due.isoformat(),
        "days_until_next": days_until_next,
        "eol_at": eol.isoformat() if eol else None,
        "days_until_eol": days_until_eol,
        "projected_occurrence_count": _count_projected_until_eol(sched, asset),
        "next_action_wo_id": str(next_wo_id) if next_wo_id else None,
        "updated_at": now.isoformat(),
    }
    prev = dict(sched.ai_meta_json or {})
    prev.update(meta)
    sched.ai_meta_json = prev
    return prev


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
    seed_next_action: bool = True,
) -> MaintenanceSchedule:
    tmpl = db.get(ReportTemplate, template_id)
    if not tmpl or tmpl.tenant_id != tenant_id:
        raise ValueError("INVALID_TEMPLATE")
    freq_key = normalize_frequency(frequency)
    if freq_key == "custom":
        freq_store = f"custom_{custom_days or 30}d"
    else:
        freq_store = freq_key
    # A1: anchor priority — last_maintenance_date > installed_on > today
    # If the computed next_due_at lands in the past, leave it (overdue); do NOT skip to today+interval.
    if last_maintenance_date:
        base = datetime.combine(last_maintenance_date, datetime.min.time(), tzinfo=timezone.utc)
        anchor = "last_maintenance"
        anchor_date = last_maintenance_date
    elif installed_on:
        base = datetime.combine(installed_on, datetime.min.time(), tzinfo=timezone.utc)
        anchor = "installed_on"
        anchor_date = installed_on
    else:
        base = datetime.now(timezone.utc)
        anchor = "today"
        anchor_date = base.date()
    sched = MaintenanceSchedule(
        tenant_id=tenant_id,
        asset_id=asset_id,
        template_id=template_id,
        frequency=freq_store,
        next_due_at=compute_next_due(freq_key, custom_days, base),
    )
    db.add(sched)
    db.flush()

    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id).options(joinedload(Asset.site))
    )
    wo = None
    if seed_next_action:
        wo = ensure_next_preventive_wo(db, sched)

    refresh_schedule_automation_meta(
        sched,
        asset,
        next_wo_id=wo.id if wo is not None else None,
        anchor=anchor,
        anchor_date=anchor_date,
    )
    db.flush()
    return sched


def _build_preventive_wo(sched: MaintenanceSchedule, asset: Asset, *, due_at: datetime) -> WorkOrder:
    site = asset.site
    assert site is not None
    return WorkOrder(
        tenant_id=sched.tenant_id,
        client_id=site.client_id,
        site_id=asset.site_id,
        asset_id=asset.id,
        source=WorkOrderSource.preventive,
        status=WorkOrderStatus.created,
        title=f"Preventive maintenance: {asset.name}",
        description=(
            f"Scheduled maintenance ({sched.frequency})"
            f" — due {due_at.date().isoformat()}"
        ),
        template_id=sched.template_id,
        due_at=due_at,
    )


def ensure_next_preventive_wo(db: Session, sched: MaintenanceSchedule) -> WorkOrder | None:
    """Ensure one open preventive WO exists for this schedule (Automation Plan #1 next action)."""
    asset = sched.asset
    if asset is None:
        asset = db.get(Asset, sched.asset_id)
    if not asset or not asset.site_id:
        # Lazy-load site if relationship missing
        asset = db.scalar(
            select(Asset)
            .where(Asset.id == sched.asset_id)
            .options(joinedload(Asset.site))
        )
    if not asset or not asset.site:
        return None

    eol = schedule_eol_cutoff(asset)
    due = _aware(sched.next_due_at)
    if eol is not None and due > eol:
        sched.is_active = False
        return None

    _dedupe_open_preventive_wos(db, asset.id)
    if _has_open_preventive_wo(db, asset.id):
        return None

    # Also skip if an open WO already targets the same calendar month
    month_start = due.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1)
    same_month = db.scalar(
        select(WorkOrder.id)
        .where(
            WorkOrder.asset_id == asset.id,
            WorkOrder.source == WorkOrderSource.preventive,
            WorkOrder.status.notin_(_TERMINAL_WO_STATUSES),
            WorkOrder.due_at.isnot(None),
            WorkOrder.due_at >= month_start,
            WorkOrder.due_at < month_end,
        )
        .limit(1)
    )
    if same_month is not None:
        return None

    wo = _build_preventive_wo(sched, asset, due_at=due)
    db.add(wo)
    sched.last_generated_at = datetime.now(timezone.utc)
    db.flush()
    return wo


def on_preventive_work_order_finished(db: Session, work_order: WorkOrder) -> WorkOrder | None:
    """When a PM WO is closed/completed: advance the schedule and open the next action.

    Stops (deactivates schedule) once the next due would fall after asset aging EOL.
    """
    if work_order.source != WorkOrderSource.preventive:
        return None
    if not work_order.asset_id or not work_order.template_id:
        return None

    sched = db.scalar(
        select(MaintenanceSchedule)
        .where(
            MaintenanceSchedule.asset_id == work_order.asset_id,
            MaintenanceSchedule.template_id == work_order.template_id,
            MaintenanceSchedule.is_active.is_(True),
        )
        .options(joinedload(MaintenanceSchedule.asset).joinedload(Asset.site))
        .limit(1)
    )
    if not sched:
        return None

    now = datetime.now(timezone.utc)
    # Advance from the later of previous due / completion time so the series stays on cadence
    advance_from = max(_aware(sched.next_due_at), now)
    _advance_schedule_next_due(sched, advance_from)

    asset = sched.asset
    eol = schedule_eol_cutoff(asset)
    if eol is not None and _aware(sched.next_due_at) > eol:
        sched.is_active = False
        refresh_schedule_automation_meta(sched, asset, next_wo_id=None)
        return None

    wo = ensure_next_preventive_wo(db, sched)
    refresh_schedule_automation_meta(
        sched,
        asset,
        next_wo_id=wo.id if wo is not None else None,
    )
    return wo


def ensure_next_actions_for_tenant(db: Session, tenant_id: UUID) -> int:
    """Create the next-event preventive WO for every active schedule that lacks one.

    Used for existing assets registered before seeding was wired, and as a
    recovery path — never creates dummy reminders, only the live next action.
    """
    q = (
        select(MaintenanceSchedule)
        .where(
            MaintenanceSchedule.tenant_id == tenant_id,
            MaintenanceSchedule.is_active.is_(True),
        )
        .options(joinedload(MaintenanceSchedule.asset).joinedload(Asset.site))
    )
    created = 0
    for sched in db.scalars(q).unique().all():
        asset = sched.asset
        if not asset or not asset.site:
            continue
        eol = schedule_eol_cutoff(asset)
        if eol is not None and _aware(sched.next_due_at) > eol:
            sched.is_active = False
            continue
        wo = ensure_next_preventive_wo(db, sched)
        if wo is not None:
            refresh_schedule_automation_meta(sched, asset, next_wo_id=wo.id)
            created += 1
        else:
            refresh_schedule_automation_meta(sched, asset, next_wo_id=None)
    db.flush()
    return created


def run_due_schedules(db: Session, tenant_id: UUID | None = None) -> int:
    """Backfill preventive WOs for schedules due within PREVENTIVE_LEAD_DAYS.

    Automation Plan #1 prefers create-on-schedule + create-on-finish; this job
    recovers schedules that lost their open next-action WO.
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

        eol = schedule_eol_cutoff(asset)
        if eol is not None and _aware(sched.next_due_at) > eol:
            sched.is_active = False
            continue

        if ensure_next_preventive_wo(db, sched) is not None:
            created += 1

        # Keep next_due_at as the planned occurrence; only nudge forward if overdue
        # and an open WO already covers it (avoid double-advance on finish hook).
        if sched.next_due_at <= now and _has_open_preventive_wo(db, asset.id, sched.template_id):
            pass
    db.flush()
    return created
