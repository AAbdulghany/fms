"""Auto-fill report answers from work order relational data and inspector profile."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Location, User, WorkOrder, WorkOrderDocument, WorkOrderSource

REPORT_PDF_DOC_DESCRIPTION = "report_pdf_export"

AUTO_FILL_FIELD_IDS = frozenset(
    {
        "inspector_full_name",
        "inspector_title",
        "inspector_contact",
        "inspector_license",
        "property_site_name",
        "property_full_address",
        "asset_unit_identification",
        "location_name",
        "inspection_date",
        "inspection_start_time",
        "inspection_type",
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
    mapping = {
        WorkOrderSource.preventive: "Routine / periodic",
        WorkOrderSource.corrective: "Interim",
        WorkOrderSource.request: "Pre-inspection",
    }
    return mapping.get(source, "Routine / periodic")


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

    return {
        "inspector_full_name": inspector.full_name,
        "inspector_title": _user_job_title(inspector),
        "inspector_contact": " / ".join(contact_parts),
        "inspector_license": _user_accreditation(inspector),
        "property_site_name": site.name if site else "",
        "property_full_address": _format_site_address(site),
        "asset_unit_identification": asset_label,
        "location_name": location_name,
        "inspection_date": opened.strftime("%Y-%m-%d"),
        "inspection_start_time": opened.strftime("%H:%M"),
        "inspection_type": _inspection_type_label(wo.source),
        "scope_systems_list": scope,
        "reference_documents": "\n".join(ref_lines),
    }


def merge_report_answers(
    db: Session,
    wo: WorkOrder,
    inspector: User,
    technician_answers: dict[str, Any] | None,
) -> dict[str, Any]:
    """Merge technician answers with live WO auto-fill (auto-fill always wins)."""
    auto = build_report_auto_fill(db, wo, inspector)
    merged = {**(technician_answers or {})}
    merged.update(auto)

    end_time = merged.get("inspection_end_time")
    if end_time:
        hours = _elapsed_hours(wo.opened_at, str(end_time))
        if hours is not None:
            merged["time_elapsed_hours"] = hours
            labor = merged.get("labor_log")
            if not labor:
                merged["labor_log"] = [{"hours": hours}]
            elif isinstance(labor, list) and labor and isinstance(labor[0], dict):
                if labor[0].get("hours") in (None, "", 0):
                    labor[0]["hours"] = hours

    return merged
