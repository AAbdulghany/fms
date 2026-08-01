"""Work orders — request / approve / decline flow."""

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

@router.post("/request", response_model=WorkOrderOut)
def request_work_order(
    body: WorkOrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _request_roles],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    """client_admin and site_manager submit a work order request (status=requested)."""
    if body.tags:
        validate_tags(body.tags)

    ensure_client_access(current, body.client_id)
    site = ensure_site_access(db, current, body.site_id)
    if site.client_id != body.client_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_CLIENT_SITE")

    if body.asset_id:
        from app.models import Asset as _Asset

        asset = db.get(_Asset, body.asset_id)
        if not asset or asset.tenant_id != current.tenant_id or asset.site_id != body.site_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSET")

    if body.location_id:
        from app.models import Location

        loc = db.get(Location, body.location_id)
        if not loc or loc.tenant_id != current.tenant_id or loc.site_id != body.site_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_LOCATION")

    template_id = body.template_id
    if not template_id:
        default_tmpl = resolve_default_report_template(db, current.tenant_id)
        if default_tmpl:
            template_id = default_tmpl.id

    wo = WorkOrder(
        tenant_id=current.tenant_id,
        client_id=body.client_id,
        site_id=body.site_id,
        location_id=body.location_id,
        asset_id=body.asset_id,
        source=body.source,
        category=body.category,
        urgency=body.urgency,
        title=body.title,
        description=body.description,
        template_id=template_id,
        created_by_user_id=current.id,
        status=WorkOrderStatus.requested,
        tags=body.tags,
    )
    db.add(wo)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="request",
        entity_type="work_order",
        entity_id=str(wo.id),
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    background_tasks.add_task(notify_work_order_requested, wo.id)
    return _work_order_to_out(wo)


@router.post("/{work_order_id}/approve-request", response_model=WorkOrderOut)
def approve_work_order_request(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _approve_roles],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    """super_admin / company_admin approves a requested work order → status=created."""
    wo = db.get(WorkOrder, work_order_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if wo.status != WorkOrderStatus.requested:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NOT_IN_REQUESTED_STATUS")

    wo.status = WorkOrderStatus.created
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="work_order",
        entity_id=str(wo.id),
        before={"status": "requested"},
        after={"status": "created"},
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    if wo.created_by_user_id:
        background_tasks.add_task(
            notify_work_order_status_changed,
            wo.id,
            "requested",
            "created",
        )
    return _work_order_to_out(wo)


@router.post("/{work_order_id}/decline-request", response_model=WorkOrderOut)
def decline_work_order_request(
    work_order_id: UUID,
    body: DeclineRequestBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _approve_roles],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    """super_admin / company_admin declines a requested work order → status=declined."""
    wo = db.get(WorkOrder, work_order_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if wo.status != WorkOrderStatus.requested:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NOT_IN_REQUESTED_STATUS")

    wo.status = WorkOrderStatus.declined
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="work_order",
        entity_id=str(wo.id),
        before={"status": "requested"},
        after={"status": "declined", "decline_reason": body.reason.strip()},
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    if wo.created_by_user_id:
        background_tasks.add_task(
            notify_work_order_status_changed,
            wo.id,
            "requested",
            "declined",
        )
    return _work_order_to_out(wo)
