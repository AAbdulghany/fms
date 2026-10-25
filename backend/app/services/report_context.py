"""Auto-fill report answers from work order relational data and inspector profile."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Client, Location, User, WorkOrder, WorkOrderDocument, WorkOrderSource

REPORT_PDF_DOC_DESCRIPTION = "report_pdf_export"

AUTO_FILL_FIELD_IDS = frozenset(
    {
        "inspector_full_name",
        "inspector_title",
        "inspector_contact",
        "inspector_license",
        "client_legal_name",
        "property_site_name",
        "property_full_address",
        "asset_unit_identification",
        "location_name",
        "inspection_date",
        "inspection_start_time",
        "inspection_type",
        "maintenance_tags",
        "wo_source",
        "scope_systems_list",
        "reference_documents",
    }
)


def resolve_report_inspector(db: Session, wo: WorkOrder, fallback: User) -> User:
    if wo.assignee_user:
        return wo.assignee_user
    if wo.assignee_user_id:
        u = db.get(User, wo.assignee_user_id)
        if u:
            return u
    return fallback


def _user_job_title(user: User) -> str:
    meta = user.metadata_json or {}
    title = (meta.get("job_title") or "").strip()
    if title:
        return title
    return str(user.role.value).replace("_", " ").title()


def _user_accreditation(user: User) -> str:
    meta = user.metadata_json or {}
    return (meta.get("accreditation") or "").strip()


def _format_site_address(site) -> str:
    if site is None:
        return ""
    addr = site.address_json or {}
    parts = [addr.get("address"), addr.get("city"), addr.get("country")]
    return ", ".join(str(p).strip() for p in parts if p)


def _inspection_type_label(source: WorkOrderSource) -> str:
    """Labels aligned with L1 Classic PDF (Corrective chip detection depends on these)."""
    mapping = {
        WorkOrderSource.preventive: "Preventive",
        WorkOrderSource.corrective: "Corrective",
        WorkOrderSource.request: "Request",
    }
    return mapping.get(source, "Corrective")


def _parse_hhmm(value: str) -> tuple[int, int] | None:
    if not value or not isinstance(value, str):
        return None
    parts = value.strip().split(":")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _elapsed_hours(start: datetime, end_hhmm: str) -> float | None:
    parsed = _parse_hhmm(end_hhmm)
    if parsed is None:
        return None
    end_hour, end_minute = parsed
    start_local = start
    if start_local.tzinfo is None:
        start_local = start_local.replace(tzinfo=timezone.utc)
    end_dt = start_local.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    if end_dt < start_local:
        from datetime import timedelta

        end_dt = end_dt + timedelta(days=1)
    delta = end_dt - start_local
    return round(max(delta.total_seconds(), 0) / 3600, 2)


def is_technician_visible_field(field: dict[str, Any]) -> bool:
    if field.get("auto_fill"):
        return False
    if field.get("visible") is False:
        return False
    if field.get("type") == "header":
        return False
    return True


def build_report_auto_fill(db: Session, wo: WorkOrder, inspector: User) -> dict[str, Any]:
    site = wo.site
    asset = wo.asset
    if asset is None and wo.asset_id:
        asset = db.get(Asset, wo.asset_id)

    client = wo.client
    if client is None and wo.client_id:
        client = db.get(Client, wo.client_id)

    location_name = ""
    if wo.location:
        location_name = wo.location.name
    elif wo.location_id:
        loc = db.get(Location, wo.location_id)
        if loc:
            location_name = loc.name

    opened = wo.opened_at
    if opened.tzinfo is None:
        opened = opened.replace(tzinfo=timezone.utc)

    job_start = wo.job_started_at or opened
    if job_start.tzinfo is None:
        job_start = job_start.replace(tzinfo=timezone.utc)

    contact_parts: list[str] = []
    if inspector.phone:
        contact_parts.append(inspector.phone.strip())
    contact_parts.append(inspector.email)

    asset_label = ""
    if asset:
        asset_label = asset.label_code or asset.name or str(asset.id)

    scope = wo.category or "general"
    if asset and asset.category:
        scope = f"{asset.category} — {wo.category or 'general'}"

    ref_lines: list[str] = []
    docs = wo.documents
    if docs is None:
        docs = list(
            db.scalars(
                select(WorkOrderDocument).where(WorkOrderDocument.work_order_id == wo.id)
            ).all()
        )
    for doc in docs:
        if doc.description == REPORT_PDF_DOC_DESCRIPTION:
            continue
        ref_lines.append(f"{doc.file_name}: /api/v1/uploads/{doc.file_url}")

    end_hhmm = ""
    if wo.job_ended_at:
        ended = wo.job_ended_at
        if ended.tzinfo is None:
            ended = ended.replace(tzinfo=timezone.utc)
        end_hhmm = ended.strftime("%H:%M")

    return {
        "inspector_full_name": inspector.full_name,
        "inspector_title": _user_job_title(inspector),
        "inspector_contact": " / ".join(contact_parts),
        "inspector_license": _user_accreditation(inspector),
        "client_legal_name": client.legal_name if client else "",
        "property_site_name": site.name if site else "",
        "property_full_address": _format_site_address(site),
        "asset_unit_identification": asset_label,
        "location_name": location_name,
        "inspection_date": job_start.strftime("%Y-%m-%d"),
        "inspection_start_time": job_start.strftime("%H:%M"),
        "inspection_end_time": end_hhmm,
        "inspection_type": _inspection_type_label(wo.source),
        "maintenance_tags": list(wo.tags or []),
        "wo_source": getattr(wo.source, "value", str(wo.source or "")),
        "scope_systems_list": scope,
        "reference_documents": "\n".join(ref_lines),
    }


def _job_elapsed_hours(wo: WorkOrder) -> float | None:
    """Labor hours from job_started_at → job_ended_at (preferred) or start→end HH:MM."""
    start = wo.job_started_at
    end = wo.job_ended_at
    if start and end:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if end < start:
            return None
        return round(max((end - start).total_seconds(), 0) / 3600, 2)
    return None


def merge_report_answers(
    db: Session,
    wo: WorkOrder,
    inspector: User,
    technician_answers: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge technician answers with live WO auto-fill (auto-fill always wins)."""
    from app.services.report_fill_profiles import normalize_answers_for_pdf

    auto = build_report_auto_fill(db, wo, inspector)
    merged = normalize_answers_for_pdf(technician_answers or {})
    # Auto-fill wins for context; keep tech end time only if job clock not set.
    tech_end = merged.get("inspection_end_time")
    merged.update(auto)
    if not auto.get("inspection_end_time") and tech_end:
        merged["inspection_end_time"] = tech_end

    hours = _job_elapsed_hours(wo)
    if hours is None and merged.get("inspection_end_time"):
        clock_start = wo.job_started_at or wo.opened_at
        hours = _elapsed_hours(clock_start, str(merged["inspection_end_time"]))

    if hours is not None:
        merged["time_elapsed_hours"] = hours
        labor = merged.get("labor_log")
        if not labor:
            merged["labor_log"] = [{"hours": hours}]
        elif isinstance(labor, list) and labor and isinstance(labor[0], dict):
            labor[0]["hours"] = hours

    return merged


def stamp_job_start(wo: WorkOrder, when: datetime | None = None) -> bool:
    """Set job_started_at once when work begins. Returns True if stamped."""
    if wo.job_started_at:
        return False
    wo.job_started_at = when or datetime.now(timezone.utc)
    return True


def stamp_job_end(wo: WorkOrder, when: datetime | None = None) -> datetime:
    """Set job_ended_at on report submit (always refresh to submit moment)."""
    ended = when or datetime.now(timezone.utc)
    if wo.job_started_at is None:
        wo.job_started_at = ended
    wo.job_ended_at = ended
    return ended
