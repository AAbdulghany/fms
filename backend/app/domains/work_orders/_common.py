"""Shared helpers and role dependencies for work order routes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.models import (
    MaintenanceReport,
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderStatus,
)
from app.schemas import UserBrief, WorkOrderOut
from app.services.report_context import merge_report_answers, resolve_report_inspector

_create_roles = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.company_engineer,
    )
)

_request_roles = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.client_admin,
        UserRole.site_manager,
    )
)

_approve_roles = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
    )
)

# P2-F3: Valid maintenance tags
VALID_TAGS = {"preventive", "corrective", "protective"}

_ASSIGN_ROLES = {
    UserRole.super_admin,
    UserRole.company_admin,
    UserRole.company_engineer,
    UserRole.site_manager,
}

_ASSIGNABLE_USER_ROLES = {
    UserRole.site_manager,
    UserRole.client_admin,
    UserRole.technician,
    UserRole.company_engineer,
    UserRole.manager,
    UserRole.company_admin,
}

_SELF_ASSIGN_ROLES = {
    UserRole.technician,
    UserRole.company_engineer,
    UserRole.site_manager,
    UserRole.company_admin,
    UserRole.super_admin,
}

_WO_ADMIN_PATCH_ROLES = _ASSIGN_ROLES


def validate_tags(tags: list[str]) -> None:
    """Validate that all tags are from the allowed set."""
    invalid = set(tags) - VALID_TAGS
    if invalid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tags: {', '.join(invalid)}. Valid tags: {', '.join(VALID_TAGS)}"
        )


REPORT_PDF_DOC_DESCRIPTION = "report_pdf_export"

def auto_work_order_title(
    *,
    asset_name: str,
    source: str,
    lang: str | None,
) -> str:
    """Corrective maintenance — Asset / صيانة وقائية — Asset."""
    code = "ar" if (lang or "").lower().startswith("ar") else "en"
    if code == "ar":
        kind = {"preventive": "وقائية", "corrective": "تصحيحية"}.get(source)
        label = f"صيانة {kind}" if kind else "صيانة"
    else:
        kind = {"preventive": "Preventive", "corrective": "Corrective"}.get(source)
        label = f"{kind} maintenance" if kind else "Request"
    return f"{label} — {asset_name}"

# Technicians fill reports during inspection (before marking WO completed).
REPORT_EDITABLE_STATUSES = frozenset(
    {
        WorkOrderStatus.in_progress,
        WorkOrderStatus.on_hold,
        WorkOrderStatus.completed,
    }
)


def _work_order_status_allows_report(wo: WorkOrder) -> bool:
    return wo.status in REPORT_EDITABLE_STATUSES


def _report_pdf_storage_path(document_id: UUID) -> Path:
    from app.config import get_settings

    settings = get_settings()
    base = Path(settings.data_dir).resolve() / "report_pdfs"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{document_id}.pdf"


def _sync_maintenance_report_pdf_export(
    db: Session,
    *,
    wo: WorkOrder,
    report: MaintenanceReport,
    current: User,
    pdf_lang: str | None = None,
) -> bytes:
    """Regenerate the maintenance report PDF and replace any prior export document.

    Returns the freshly rendered PDF bytes so callers (e.g. Export) can stream
    them without rendering twice.
    """
    from app.services.maintenance_report_pdf import resolve_report_locale
    from app.services.pdf import render_report_summary_pdf

    old_docs = list(
        db.scalars(
            select(WorkOrderDocument).where(
                WorkOrderDocument.work_order_id == wo.id,
                WorkOrderDocument.description == REPORT_PDF_DOC_DESCRIPTION,
            )
        ).all()
    )
    for o in old_docs:
        p = _report_pdf_storage_path(o.id)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
        db.delete(o)
    db.flush()

    tenant = db.get(Tenant, wo.tenant_id)
    inspector = resolve_report_inspector(db, wo, current)
    merged_answers = merge_report_answers(
        db,
        wo,
        inspector,
        report.answers_json or {},
    )
    lang, dir_ = resolve_report_locale(tenant.settings_json if tenant else {}, pdf_lang)
    client_name = ""
    if wo.client is not None:
        client_name = wo.client.legal_name or ""
    elif getattr(wo, "client_id", None):
        from app.models import Client

        c = db.get(Client, wo.client_id)
        if c:
            client_name = c.legal_name or ""
    pdf_bytes = render_report_summary_pdf(
        tenant_name=tenant.name if tenant else "",
        work_order_title=wo.title or str(wo.id),
        work_order_id=str(wo.id),
        answers=merged_answers,
        template_schema=dict(report.template_snapshot_json or {}),
        # L1: tenant is the customer-facing company brand (not Orbit platform).
        platform_company_name=tenant.name if tenant else "",
        platform_copyright="",
        client_name=client_name,
        lang=lang,
        dir_=dir_,
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    doc = WorkOrderDocument(
        tenant_id=wo.tenant_id,
        work_order_id=wo.id,
        uploaded_by_user_id=current.id,
        file_name=f"maintenance-report-{lang}-{stamp}.pdf",
        file_size=len(pdf_bytes),
        file_type="application/pdf",
        file_url="auto_pdf",
        description=REPORT_PDF_DOC_DESCRIPTION,
    )
    db.add(doc)
    db.flush()
    _report_pdf_storage_path(doc.id).write_bytes(pdf_bytes)
    return pdf_bytes


def _access_wo(db: Session, current: User, wo_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, wo_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if (
        current.role == UserRole.technician
        and wo.assignee_user_id != current.id
        and wo.return_assignee_user_id != current.id
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.client_admin and current.client_id and wo.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return wo


def _validate_assignee(db: Session, tenant_id: UUID, assignee_user_id: UUID) -> User:
    """Ensure assignee exists, is active, in-tenant, and has an assignable role."""
    assignee = db.get(User, assignee_user_id)
    if (
        not assignee
        or assignee.tenant_id != tenant_id
        or not assignee.is_active
        or assignee.role not in _ASSIGNABLE_USER_ROLES
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSIGNEE")
    return assignee


def _assert_patch_fields_allowed(current: User, body: WorkOrderUpdate) -> None:
    """Technicians and client_admins may only transition status on accessible WOs."""
    admin_fields_set = any(
        getattr(body, field) is not None
        for field in ("title", "description", "urgency", "template_id", "assignee_user_id", "tags")
    )
    if admin_fields_set and current.role not in _WO_ADMIN_PATCH_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")


def _wo_load_options():
    return (
        joinedload(WorkOrder.creator_user),
        joinedload(WorkOrder.assignee_user),
        joinedload(WorkOrder.client),
        joinedload(WorkOrder.site),
        joinedload(WorkOrder.asset),
        joinedload(WorkOrder.location),
    )


def _work_order_context_fields(wo: WorkOrder) -> dict:
    site = wo.site if hasattr(wo, "site") else None
    asset = wo.asset if hasattr(wo, "asset") else None
    location = wo.location if hasattr(wo, "location") else None
    addr = (site.address_json or {}) if site else {}
    return {
        "company_name": wo.client.legal_name if hasattr(wo, "client") and wo.client else None,
        "site_name": site.name if site else None,
        "asset_name": asset.name if asset else None,
        "asset_category": asset.category if asset else None,
        "asset_serial": asset.serial if asset else None,
        "asset_label_code": asset.label_code if asset else None,
        "asset_model": asset.model if asset else None,
        "site_address": addr.get("address"),
        "site_city": addr.get("city"),
        "site_country": addr.get("country"),
        "location_name": location.name if location else None,
    }


def _work_order_to_out(wo: WorkOrder) -> WorkOrderOut:
    from app.services.diagnostic_codes import downtime_minutes
    from app.services.report_context import _job_elapsed_hours

    base = WorkOrderOut.model_validate(wo)
    return base.model_copy(
        update={
            "creator": UserBrief.model_validate(wo.creator_user) if wo.creator_user else None,
            "assignee": UserBrief.model_validate(wo.assignee_user) if wo.assignee_user else None,
            "downtime_minutes": downtime_minutes(wo.downtime_started_at, wo.downtime_ended_at),
            "job_hours": _job_elapsed_hours(wo),
            **_work_order_context_fields(wo),
        }
    )


def _reload_wo_with_users(db: Session, wo_id: UUID) -> WorkOrder:
    return db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == wo_id)
        .options(*_wo_load_options())
    ).scalar_one()


def _assignee_audit_label(db: Session, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    u = db.get(User, user_id)
    if not u:
        return None
    return u.full_name or u.email

