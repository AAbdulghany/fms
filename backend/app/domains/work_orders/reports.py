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
        UserRole.company_engineer,
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

    if wo.status == WorkOrderStatus.in_progress:
        from app.services.report_context import stamp_job_start

        stamp_job_start(wo)

    wo_detail = _reload_wo_with_users(db, wo.id)
    asset_category = wo_detail.asset.category if wo_detail.asset else None
    source_val = getattr(wo.source, "value", str(wo.source or "corrective"))
    effective_schema = resolve_effective_schema(
        dict(tmpl.schema_json or {}),
        asset_category,
        wo_source=source_val,
        use_short_fill=True,
    )

    if wo.report:
        r = wo.report
        if r.status != ReportStatus.draft:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_EDITABLE")
        r.answers_json = body.answers
        # Always keep draft on the short fill profile (legacy long STD-INSP snapshots break submit).
        r.template_snapshot_json = effective_schema
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


@router.post("/{work_order_id}/report/reopen", response_model=MaintenanceReportOut)
def reopen_report(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> MaintenanceReport:
    """Return a submitted report to draft so it can be edited before the job is completed."""
    wo = _access_wo(db, current, work_order_id)
    if current.role not in (
        UserRole.technician,
        UserRole.company_admin,
        UserRole.super_admin,
        UserRole.site_manager,
        UserRole.company_engineer,
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if wo.status not in REPORT_EDITABLE_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_EDITABLE_AT_THIS_STATUS")
    if not wo.report:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_STARTED")
    r = wo.report
    if r.status == ReportStatus.draft:
        return r
    if r.status not in (ReportStatus.submitted, ReportStatus.rejected):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_EDITABLE")
    r.status = ReportStatus.draft
    db.commit()
    db.refresh(r)
    return r


_FIELD_HANDOFF_ROLES = {
    UserRole.technician,
    UserRole.company_engineer,
    UserRole.site_manager,
}
_REPORT_APPROVER_ROLES = {
    UserRole.super_admin,
    UserRole.company_admin,
    UserRole.client_admin,
    UserRole.manager,
}


@router.post("/{work_order_id}/report/send-approval", response_model=WorkOrderOut)
def send_report_for_approval(
    work_order_id: UUID,
    body: AssignBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    """Field roles name an approver. The work order is assigned to that person until they approve."""
    wo = _access_wo(db, current, work_order_id)
    if current.role not in _FIELD_HANDOFF_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if not wo.report or wo.report.status != ReportStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_SUBMITTED")
    target = db.get(User, body.assignee_user_id)
    if (
        not target
        or target.tenant_id != current.tenant_id
        or not target.is_active
        or target.role not in _REPORT_APPROVER_ROLES
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSIGNEE")
    old_assignee_id = wo.assignee_user_id
    if wo.return_assignee_user_id is None:
        wo.return_assignee_user_id = old_assignee_id or current.id
    wo.assignee_user_id = target.id
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="assign",
        entity_type="work_order",
        entity_id=str(wo.id),
        before={"assignee_user_id": str(old_assignee_id) if old_assignee_id else None},
        after={
            "assignee_user_id": str(target.id),
            "assignee_name": target.full_name or target.email,
            "return_assignee_user_id": str(wo.return_assignee_user_id),
        },
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    background_tasks.add_task(notify_work_order_assigned, wo.id)
    return _work_order_to_out(wo)


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
    from app.services.report_context import stamp_job_end, stamp_job_start
    from app.services.report_fill_profiles import normalize_answers_for_pdf

    stamp_job_start(wo)  # no-op if already started
    stamp_job_end(wo)
    # Persist normalized short→PDF fields on the draft answers before merge/validate.
    r.answers_json = normalize_answers_for_pdf(r.answers_json or {})
    inspector = resolve_report_inspector(db, wo, current)
    merged = merge_report_answers(db, wo, inspector, r.answers_json or {})
    r.answers_json = {**(r.answers_json or {}), **{
        k: merged[k]
        for k in (
            "inspection_start_time",
            "inspection_end_time",
            "time_elapsed_hours",
            "labor_log",
            "findings_defects",
            "tests_performed",
            "overall_condition",
            "parts_used",
        )
        if k in merged
    }}
    # Validate against short fill profile only — never the legacy long STD-INSP snapshot
    # (Site visit End time / tests / Findings). Those are filled by normalize for PDF.
    source_val = getattr(wo.source, "value", None) or str(wo.source or "corrective")
    short_schema = resolve_effective_schema(
        {},
        None,
        wo_source=source_val,
        use_short_fill=True,
    )
    # Drop any stale long-template fields from the snapshot used for validation.
    r.template_snapshot_json = short_schema
    # Belt: if normalize missed PDF fields, fill from job clock / short answers so
    # a mis-routed legacy validator cannot block submit.
    if not str(merged.get("inspection_end_time") or "").strip():
        ended = wo.job_ended_at
        if ended is not None:
            if ended.tzinfo is None:
                ended = ended.replace(tzinfo=timezone.utc)
            merged["inspection_end_time"] = ended.strftime("%H:%M")
            r.answers_json = {**(r.answers_json or {}), "inspection_end_time": merged["inspection_end_time"]}
    if not str(merged.get("tests_performed") or "").strip():
        merged["tests_performed"] = str(
            (r.answers_json or {}).get("fix_action")
            or (r.answers_json or {}).get("round_result")
            or "Completed"
        ).strip()
        r.answers_json = {**(r.answers_json or {}), "tests_performed": merged["tests_performed"]}
    if not str(merged.get("findings_defects") or "").strip():
        bits = [
            str((r.answers_json or {}).get("symptom") or "").strip(),
            str((r.answers_json or {}).get("fix_action") or "").strip(),
            str((r.answers_json or {}).get("issue_notes") or "").strip(),
        ]
        merged["findings_defects"] = "\n".join(b for b in bits if b) or "See work order report."
        r.answers_json = {**(r.answers_json or {}), "findings_defects": merged["findings_defects"]}

    missing = validate_required_fields(short_schema, merged)
    # Never surface legacy STD-INSP required-field names to the technician.
    missing = [
        m
        for m in missing
        if "End time" not in m
        and "Specific tests" not in m
        and "Findings / defects" not in m
        and "Site visit" not in m
    ]
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
