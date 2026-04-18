from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
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
from app.services.report_validation import validate_required_fields
from app.services.wo_notifications import (
    notify_work_order_assigned,
    notify_work_order_created,
    notify_work_order_status_changed,
)
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


REPORT_PDF_DOC_DESCRIPTION = "report_pdf_export"


def _work_order_status_allows_report(wo: WorkOrder) -> bool:
    return wo.status == WorkOrderStatus.completed


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
) -> None:
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
    pdf_bytes = render_report_summary_pdf(
        tenant_name=tenant.name if tenant else "",
        work_order_title=wo.title or str(wo.id),
        answers=report.answers_json or {},
        template_schema=dict(report.template_snapshot_json or {}),
    )
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    doc = WorkOrderDocument(
        tenant_id=wo.tenant_id,
        work_order_id=wo.id,
        uploaded_by_user_id=current.id,
        file_name=f"maintenance-report-{stamp}.pdf",
        file_size=len(pdf_bytes),
        file_type="application/pdf",
        file_url="auto_pdf",
        description=REPORT_PDF_DOC_DESCRIPTION,
    )
    db.add(doc)
    db.flush()
    _report_pdf_storage_path(doc.id).write_bytes(pdf_bytes)


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


def _work_order_to_out(wo: WorkOrder) -> WorkOrderOut:
    base = WorkOrderOut.model_validate(wo)
    return base.model_copy(
        update={
            "creator": UserBrief.model_validate(wo.creator_user) if wo.creator_user else None,
            "assignee": UserBrief.model_validate(wo.assignee_user) if wo.assignee_user else None,
            "company_name": wo.client.legal_name if hasattr(wo, 'client') and wo.client else None,
            "site_name": wo.site.name if hasattr(wo, 'site') and wo.site else None,
        }
    )


def _reload_wo_with_users(db: Session, wo_id: UUID) -> WorkOrder:
    return db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == wo_id)
        .options(
            joinedload(WorkOrder.creator_user),
            joinedload(WorkOrder.assignee_user),
            joinedload(WorkOrder.client),
            joinedload(WorkOrder.site),
        )
    ).scalar_one()


def _assignee_audit_label(db: Session, user_id: UUID | None) -> str | None:
    if user_id is None:
        return None
    u = db.get(User, user_id)
    if not u:
        return None
    return u.full_name or u.email


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
    q = q.options(
        joinedload(WorkOrder.creator_user),
        joinedload(WorkOrder.assignee_user),
        joinedload(WorkOrder.client),
        joinedload(WorkOrder.site),
    )
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
        .options(joinedload(WorkOrder.creator_user), joinedload(WorkOrder.assignee_user))
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
    old_status_value: str | None = None
    if body.status is not None:
        if not can_transition(wo.status, body.status):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TRANSITION")

        old_status = wo.status
        old_status_value = old_status.value
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
    if not _work_order_status_allows_report(wo):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="REPORT_REQUIRES_COMPLETED_WORK_ORDER",
        )

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
    try:
        _sync_maintenance_report_pdf_export(db, wo=wo, report=r, current=current)
        db.commit()
    except Exception:
        db.rollback()
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
    try:
        _sync_maintenance_report_pdf_export(db, wo=wo, report=r, current=current)
        db.commit()
    except Exception:
        db.rollback()
    return r


@router.get("/{work_order_id}/history", response_model=list[AuditLogOut])
def get_work_order_history(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[AuditLogOut]:
    wo = _access_wo(db, current, work_order_id)
    
    logs = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "work_order",
            AuditLog.entity_id == str(wo.id)
        )
        .options(joinedload(AuditLog.actor_user))
        .order_by(AuditLog.created_at.desc())
    ).all()
    
    result = []
    for log in logs:
        actor_name = None
        if log.actor_user:
            actor_name = log.actor_user.full_name or log.actor_user.email
        
        result.append(
            AuditLogOut(
                id=log.id,
                actor_user_id=log.actor_user_id,
                actor_name=actor_name,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                before_json=log.before_json,
                after_json=log.after_json,
                created_at=log.created_at,
            )
        )
    
    return result


@router.get("/{work_order_id}/comments", response_model=list[CommentOut])
def get_work_order_comments(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[CommentOut]:
    wo = _access_wo(db, current, work_order_id)
    
    comments = db.scalars(
        select(Comment)
        .where(Comment.work_order_id == wo.id)
        .options(joinedload(Comment.user))
        .order_by(Comment.created_at.asc())
    ).all()
    
    result = []
    for comment in comments:
        user_name = None
        if comment.user:
            user_name = comment.user.full_name or comment.user.email
        
        result.append(
            CommentOut(
                id=comment.id,
                work_order_id=comment.work_order_id,
                user_id=comment.user_id,
                user_name=user_name,
                content=comment.content,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
        )
    
    return result


@router.post("/{work_order_id}/comments", response_model=CommentOut)
def create_work_order_comment(
    work_order_id: UUID,
    body: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> CommentOut:
    wo = _access_wo(db, current, work_order_id)
    
    comment = Comment(
        tenant_id=current.tenant_id,
        work_order_id=wo.id,
        user_id=current.id,
        content=body.content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    user_name = current.full_name or current.email
    
    return CommentOut(
        id=comment.id,
        work_order_id=comment.work_order_id,
        user_id=comment.user_id,
        user_name=user_name,
        content=comment.content,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/{work_order_id}/documents", response_model=list[DocumentOut])
def get_work_order_documents(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[DocumentOut]:
    wo = _access_wo(db, current, work_order_id)
    
    documents = db.scalars(
        select(WorkOrderDocument)
        .where(WorkOrderDocument.work_order_id == wo.id)
        .options(joinedload(WorkOrderDocument.uploaded_by))
        .order_by(WorkOrderDocument.created_at.desc())
    ).all()
    
    result = []
    for doc in documents:
        uploaded_by_name = None
        if doc.uploaded_by:
            uploaded_by_name = doc.uploaded_by.full_name or doc.uploaded_by.email
        
        result.append(
            DocumentOut(
                id=doc.id,
                work_order_id=doc.work_order_id,
                uploaded_by_user_id=doc.uploaded_by_user_id,
                uploaded_by_name=uploaded_by_name,
                file_name=doc.file_name,
                file_size=doc.file_size,
                file_type=doc.file_type,
                file_url=doc.file_url,
                description=doc.description,
                created_at=doc.created_at,
            )
        )
    
    return result


@router.get("/{work_order_id}/documents/{document_id}/file")
def download_work_order_document_file(
    work_order_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    wo = _access_wo(db, current, work_order_id)
    doc = db.get(WorkOrderDocument, document_id)
    if not doc or doc.work_order_id != wo.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="DOCUMENT_NOT_FOUND")
    if doc.description != REPORT_PDF_DOC_DESCRIPTION:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="DOWNLOAD_ONLY_FOR_SERVER_GENERATED_PDFS",
        )
    path = _report_pdf_storage_path(doc.id)
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_MISSING")
    return FileResponse(
        path,
        media_type=doc.file_type or "application/pdf",
        filename=doc.file_name,
    )


@router.post("/{work_order_id}/documents", response_model=DocumentOut)
def upload_work_order_document(
    work_order_id: UUID,
    body: DocumentCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> DocumentOut:
    wo = _access_wo(db, current, work_order_id)
    
    document = WorkOrderDocument(
        tenant_id=current.tenant_id,
        work_order_id=wo.id,
        uploaded_by_user_id=current.id,
        file_name=body.file_name,
        file_size=body.file_size,
        file_type=body.file_type,
        file_url=body.file_url,
        description=body.description,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    uploaded_by_name = current.full_name or current.email
    
    return DocumentOut(
        id=document.id,
        work_order_id=document.work_order_id,
        uploaded_by_user_id=document.uploaded_by_user_id,
        uploaded_by_name=uploaded_by_name,
        file_name=document.file_name,
        file_size=document.file_size,
        file_type=document.file_type,
        file_url=document.file_url,
        description=document.description,
        created_at=document.created_at,
    )


@router.delete("/{work_order_id}/documents/{document_id}")
def delete_work_order_document(
    work_order_id: UUID,
    document_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    wo = _access_wo(db, current, work_order_id)
    
    document = db.get(WorkOrderDocument, document_id)
    if not document or document.work_order_id != wo.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="DOCUMENT_NOT_FOUND")
    
    # Only allow deleting own documents or if admin
    can_delete = (
        document.uploaded_by_user_id == current.id or
        current.role in [UserRole.super_admin, UserRole.company_admin, UserRole.site_manager]
    )
    
    if not can_delete:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CANNOT_DELETE_DOCUMENT")
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted"}
