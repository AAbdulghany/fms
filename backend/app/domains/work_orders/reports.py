"""Work orders — maintenance report draft and submit."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import ensure_client_access, ensure_site_access, get_current_user, require_roles
from app.database import get_db
from app.models import (
    AuditLog,
    Comment,
    MaintenanceReport,
    ReportStatus,
    ReportTemplate,
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderStatus,
)
from app.schemas import (
    AssignBody,
    AuditLogOut,
    CommentCreate,
    CommentOut,
    DeclineRequestBody,
    DocumentCreate,
    DocumentOut,
    MaintenanceReportOut,
    PaginatedMeta,
    PaginatedWorkOrders,
    ReportAnswersUpdate,
    UserBrief,
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderUpdate,
)
from app.services.asset_lifecycle import on_work_order_completed
from app.services.audit import write_audit
from app.services.report_context import merge_report_answers, resolve_report_inspector
from app.services.report_schema_resolve import resolve_effective_schema
from app.services.report_template_defaults import resolve_default_report_template
from app.services.report_validation import validate_required_fields
from app.services.wo_notifications import (
    notify_work_order_assigned,
    notify_work_order_created,
    notify_work_order_requested,
    notify_work_order_status_changed,
)
from app.services.work_order_fsm import (
    TransitionError,
    assert_mutable,
    can_transition,
    validate_status_transition,
)

from ._common import (
    REPORT_PDF_DOC_DESCRIPTION,
    REPORT_EDITABLE_STATUSES,
    _ASSIGN_ROLES,
    _access_wo,
    _approve_roles,
    _assignee_audit_label,
    _assert_patch_fields_allowed,
    _create_roles,
    _reload_wo_with_users,
    _request_roles,
    _sync_maintenance_report_pdf_export,
    _validate_assignee,
    _wo_load_options,
    _work_order_status_allows_report,
    _work_order_to_out,
    validate_tags,
)
from .router import router

@router.get("/{work_order_id}/report", response_model=MaintenanceReportOut)
def get_report(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> MaintenanceReport:
    wo = _access_wo(db, current, work_order_id)
    if not wo.report:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="REPORT_NOT_STARTED")
    return wo.report


@router.put("/{work_order_id}/report", response_model=MaintenanceReportOut)
def upsert_report_draft(
    work_order_id: UUID,
    body: ReportAnswersUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> MaintenanceReport:
    wo = _access_wo(db, current, work_order_id)
    if current.role not in (
        UserRole.technician,
        UserRole.company_admin,
        UserRole.super_admin,
        UserRole.site_manager,
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if not wo.template_id:
        default_tmpl = resolve_default_report_template(db, wo.tenant_id)
        if default_tmpl:
            wo.template_id = default_tmpl.id
            db.flush()
    if not wo.template_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="TEMPLATE_REQUIRED")
    tmpl = db.get(ReportTemplate, wo.template_id)
    if not tmpl or tmpl.tenant_id != wo.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TEMPLATE")
    if not _work_order_status_allows_report(wo):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="REPORT_NOT_ALLOWED_AT_THIS_STATUS",
        )

    wo_detail = _reload_wo_with_users(db, wo.id)
    asset_category = wo_detail.asset.category if wo_detail.asset else None
    effective_schema = resolve_effective_schema(dict(tmpl.schema_json or {}), asset_category)

    if wo.report:
        r = wo.report
        if r.status != ReportStatus.draft:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_EDITABLE")
        r.answers_json = body.answers
    else:
        r = MaintenanceReport(
            tenant_id=wo.tenant_id,
            work_order_id=wo.id,
            template_id=tmpl.id,
            template_version=tmpl.version,
            template_snapshot_json=effective_schema,
            answers_json=body.answers,
            status=ReportStatus.draft,
        )
        db.add(r)
    db.commit()
    db.refresh(r)
    wo = _reload_wo_with_users(db, wo.id)
    try:
        _sync_maintenance_report_pdf_export(
            db,
            wo=wo_detail if wo_detail else wo,
            report=r,
            current=current,
            pdf_lang=body.pdf_lang,
        )
        db.commit()
    except Exception:
        db.rollback()
    return r


@router.post("/{work_order_id}/report/submit", response_model=MaintenanceReportOut)
def submit_report(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    pdf_lang: str | None = Query(None),
) -> MaintenanceReport:
    wo = _access_wo(db, current, work_order_id)
    if not wo.report:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_STARTED")
    if wo.status not in REPORT_EDITABLE_STATUSES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="REPORT_NOT_EDITABLE_AT_THIS_STATUS",
        )
    r = wo.report
    if r.status != ReportStatus.draft:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_DRAFT")
    wo = _reload_wo_with_users(db, wo.id)
    inspector = resolve_report_inspector(db, wo, current)
    merged = merge_report_answers(db, wo, inspector, r.answers_json or {})
    missing = validate_required_fields(r.template_snapshot_json, merged)
    if missing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "missing_fields": missing},
        )
    r.status = ReportStatus.submitted
    r.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(r)
    try:
        _sync_maintenance_report_pdf_export(
            db, wo=wo, report=r, current=current, pdf_lang=pdf_lang
        )
        db.commit()
    except Exception:
        db.rollback()
    return r
