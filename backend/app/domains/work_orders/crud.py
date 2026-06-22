"""Work orders — list, create, get, patch, assign."""

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

@router.get("", response_model=PaginatedWorkOrders)
def list_work_orders(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    urgency: str | None = Query(None),
    client_id: UUID | None = Query(None),
    site_id: UUID | None = Query(None),
    assignee_user_id: UUID | None = Query(None),
    asset_id: Annotated[UUID | None, Query()] = None,
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    search: str | None = Query(None),
    tags: str | None = Query(None),  # P2-F3: Comma-separated tags filter
) -> PaginatedWorkOrders:
    q = select(WorkOrder).where(WorkOrder.tenant_id == current.tenant_id)
    
    # Role-based filtering
    if current.role == UserRole.technician:
        q = q.where(WorkOrder.assignee_user_id == current.id)
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(WorkOrder.client_id == current.client_id)
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if scoped:
            q = q.where(WorkOrder.site_id.in_(scoped))
        else:
            q = q.where(false())
    
    # P2-F1 Additional filters
    if status_filter:
        try:
            st = WorkOrderStatus(status_filter)
            q = q.where(WorkOrder.status == st)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    
    if urgency:
        q = q.where(WorkOrder.urgency == urgency)
    
    if client_id:
        q = q.where(WorkOrder.client_id == client_id)
    
    if site_id:
        q = q.where(WorkOrder.site_id == site_id)
    
    if assignee_user_id:
        q = q.where(WorkOrder.assignee_user_id == assignee_user_id)
    
    if asset_id:
        q = q.where(WorkOrder.asset_id == asset_id)
    
    if date_from:
        q = q.where(WorkOrder.opened_at >= date_from)
    
    if date_to:
        q = q.where(WorkOrder.opened_at <= date_to)
    
    if search:
        q = q.where(WorkOrder.title.ilike(f"%{search}%"))
    
    # P2-F3: Tags filter - work orders having any of the specified tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            validate_tags(tag_list)
            q = q.where(WorkOrder.tags.overlap(tag_list))
    
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.options(*_wo_load_options())
    q = q.order_by(WorkOrder.opened_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.scalars(q).all())
    return PaginatedWorkOrders(
        data=[_work_order_to_out(r) for r in rows],
        meta=PaginatedMeta(page=page, page_size=page_size, total=int(total or 0)),
    )


@router.post("", response_model=WorkOrderOut)
def create_work_order(
    body: WorkOrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _create_roles],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    # P2-F3: Validate tags
    if body.tags:
        validate_tags(body.tags)

    # SECURITY: enforce client scope before touching any data
    ensure_client_access(current, body.client_id)

    # SECURITY: enforce site scope; also verify site belongs to the stated client
    site = ensure_site_access(db, current, body.site_id)
    if site.client_id != body.client_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_CLIENT_SITE")

    # SECURITY: verify asset belongs to this tenant and site
    from app.models import Asset as _Asset

    asset = db.get(_Asset, body.asset_id)
    if not asset or asset.tenant_id != current.tenant_id or asset.site_id != body.site_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSET")

    if body.location_id:
        from app.models import Location

        loc = db.get(Location, body.location_id)
        if (
            not loc
            or loc.tenant_id != current.tenant_id
            or loc.site_id != body.site_id
        ):
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
        status=WorkOrderStatus.created,
        tags=body.tags,
    )
    db.add(wo)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="work_order",
        entity_id=str(wo.id),
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    background_tasks.add_task(notify_work_order_created, wo.id)
    return _work_order_to_out(wo)

@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> WorkOrderOut:
    wo = db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == work_order_id)
        .options(*_wo_load_options())
    ).scalar_one_or_none()
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.technician and wo.assignee_user_id != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.client_admin and current.client_id and wo.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return _work_order_to_out(wo)


@router.patch("/{work_order_id}", response_model=WorkOrderOut)
def patch_work_order(
    work_order_id: UUID,
    body: WorkOrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> WorkOrderOut:
    wo = _access_wo(db, current, work_order_id)
    assert_mutable(wo, body)
    _assert_patch_fields_allowed(current, body)
    if body.assignee_user_id is not None:
        if current.role not in _ASSIGN_ROLES:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
        _validate_assignee(db, current.tenant_id, body.assignee_user_id)
        wo.assignee_user_id = body.assignee_user_id
    old_status_value: str | None = None
    if body.status is not None:
        try:
            validate_status_transition(wo, wo.status, body.status, body, current)
        except TransitionError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.code) from exc
        if not can_transition(wo.status, body.status) and wo.status != body.status:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TRANSITION")

        old_status = wo.status
        old_status_value = old_status.value
        wo.status = body.status

        if body.status == WorkOrderStatus.closed:
            wo.closed_at = datetime.now(timezone.utc)

        if body.status == WorkOrderStatus.on_hold and body.hold_reason:
            wo.description = f"{wo.description}\n[ON HOLD] {body.hold_reason.strip()}".strip()

        if body.status == WorkOrderStatus.cancelled and body.cancellation_reason:
            wo.description = f"{wo.description}\n[CANCELLED] {body.cancellation_reason.strip()}".strip()

        # P2-F2: Hook asset lifecycle check when WO completes
        if body.status == WorkOrderStatus.completed and old_status != WorkOrderStatus.completed:
            on_work_order_completed(db, wo)
    if body.title is not None:
        wo.title = body.title
    if body.description is not None:
        wo.description = body.description
    if body.urgency is not None:
        wo.urgency = body.urgency
    if body.template_id is not None:
        wo.template_id = body.template_id
    if body.tags is not None:
        # P2-F3: Validate and update tags
        validate_tags(body.tags)
        wo.tags = body.tags
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="work_order",
        entity_id=str(wo.id),
        after={"status": wo.status.value},
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    if body.status is not None and old_status_value is not None and wo.status.value != old_status_value:
        background_tasks.add_task(
            notify_work_order_status_changed,
            wo.id,
            old_status_value,
            wo.status.value,
        )
    return _work_order_to_out(wo)


@router.get("/{work_order_id}/assignable-users", response_model=list[UserBrief])
def get_assignable_users(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[UserBrief]:
    wo = _access_wo(db, current, work_order_id)
    
    # Get users with roles: site_manager, client_admin, technician, manager
    assignable_roles = [
        UserRole.site_manager,
        UserRole.client_admin,
        UserRole.technician,
        UserRole.manager,
    ]
    
    users = db.scalars(
        select(User)
        .where(
            User.tenant_id == current.tenant_id,
            User.is_active == True,
            User.role.in_(assignable_roles),
        )
        .order_by(User.full_name)
    ).all()
    
    return [UserBrief.model_validate(u) for u in users]


@router.post("/{work_order_id}/assign", response_model=WorkOrderOut)
def assign_work_order(
    work_order_id: UUID,
    body: AssignBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    _: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.super_admin,
                UserRole.company_admin,
                UserRole.site_manager,
            )
        ),
    ],
) -> WorkOrderOut:
    wo = _access_wo(db, current, work_order_id)
    old_assignee_id = wo.assignee_user_id
    old_status = wo.status
    _validate_assignee(db, current.tenant_id, body.assignee_user_id)
    wo.assignee_user_id = body.assignee_user_id
    if wo.status == WorkOrderStatus.created:
        if not can_transition(wo.status, WorkOrderStatus.assigned):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TRANSITION")
        wo.status = WorkOrderStatus.assigned
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="assign",
        entity_type="work_order",
        entity_id=str(wo.id),
        before={
            "assignee_user_id": str(old_assignee_id) if old_assignee_id else None,
            "assignee_name": _assignee_audit_label(db, old_assignee_id),
            "status": old_status.value,
        },
        after={
            "assignee_user_id": str(wo.assignee_user_id) if wo.assignee_user_id else None,
            "assignee_name": _assignee_audit_label(db, wo.assignee_user_id),
            "status": wo.status.value,
        },
    )
    db.commit()
    wo = _reload_wo_with_users(db, wo.id)
    background_tasks.add_task(notify_work_order_assigned, wo.id)
    return _work_order_to_out(wo)
