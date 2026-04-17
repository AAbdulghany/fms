from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    MaintenanceReport,
    ReportStatus,
    ReportTemplate,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderStatus,
)
from app.schemas import (
    AssignBody,
    MaintenanceReportOut,
    PaginatedMeta,
    PaginatedWorkOrders,
    ReportAnswersUpdate,
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderUpdate,
)
from app.services.asset_lifecycle import on_work_order_completed
from app.services.audit import write_audit
from app.services.report_validation import validate_required_fields
from app.services.work_order_fsm import can_transition

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

_create_roles = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.client_admin,
        UserRole.site_manager,
    )
)

# P2-F3: Valid maintenance tags
VALID_TAGS = {"preventive", "corrective", "protective"}


def validate_tags(tags: list[str]) -> None:
    """Validate that all tags are from the allowed set."""
    invalid = set(tags) - VALID_TAGS
    if invalid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tags: {', '.join(invalid)}. Valid tags: {', '.join(VALID_TAGS)}"
        )


def _access_wo(db: Session, current: User, wo_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, wo_id)
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
    return wo


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
    q = q.order_by(WorkOrder.opened_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.scalars(q).all())
    return PaginatedWorkOrders(
        data=[WorkOrderOut.model_validate(r) for r in rows],
        meta=PaginatedMeta(page=page, page_size=page_size, total=int(total or 0)),
    )


@router.post("", response_model=WorkOrderOut)
def create_work_order(
    body: WorkOrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _create_roles],
) -> WorkOrder:
    # P2-F3: Validate tags
    if body.tags:
        validate_tags(body.tags)
    
    if body.location_id:
        from app.models import Location

        loc = db.get(Location, body.location_id)
        if (
            not loc
            or loc.tenant_id != current.tenant_id
            or loc.site_id != body.site_id
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_LOCATION")

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
        template_id=body.template_id,
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
    db.refresh(wo)
    return wo


@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> WorkOrder:
    return _access_wo(db, current, work_order_id)


@router.patch("/{work_order_id}", response_model=WorkOrderOut)
def patch_work_order(
    work_order_id: UUID,
    body: WorkOrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> WorkOrder:
    wo = _access_wo(db, current, work_order_id)
    if body.status is not None:
        if not can_transition(wo.status, body.status):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TRANSITION")
        
        old_status = wo.status
        wo.status = body.status
        
        if body.status == WorkOrderStatus.closed:
            wo.closed_at = datetime.now(timezone.utc)
        
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
    if body.assignee_user_id is not None:
        wo.assignee_user_id = body.assignee_user_id
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
    db.refresh(wo)
    return wo


@router.post("/{work_order_id}/assign", response_model=WorkOrderOut)
def assign_work_order(
    work_order_id: UUID,
    body: AssignBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
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
) -> WorkOrder:
    wo = _access_wo(db, current, work_order_id)
    wo.assignee_user_id = body.assignee_user_id
    if wo.status == WorkOrderStatus.created:
        if not can_transition(wo.status, WorkOrderStatus.assigned):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TRANSITION")
        wo.status = WorkOrderStatus.assigned
    db.commit()
    db.refresh(wo)
    return wo


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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="TEMPLATE_REQUIRED")
    tmpl = db.get(ReportTemplate, wo.template_id)
    if not tmpl or tmpl.tenant_id != wo.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TEMPLATE")

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
            template_snapshot_json=dict(tmpl.schema_json),
            answers_json=body.answers,
            status=ReportStatus.draft,
        )
        db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.post("/{work_order_id}/report/submit", response_model=MaintenanceReportOut)
def submit_report(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> MaintenanceReport:
    wo = _access_wo(db, current, work_order_id)
    if not wo.report:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_STARTED")
    r = wo.report
    if r.status != ReportStatus.draft:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_DRAFT")
    missing = validate_required_fields(r.template_snapshot_json, r.answers_json or {})
    if missing:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "missing_fields": missing},
        )
    r.status = ReportStatus.submitted
    r.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(r)
    return r
