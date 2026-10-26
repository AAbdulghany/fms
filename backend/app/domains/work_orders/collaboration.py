"""Work orders — history, comments, documents."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
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
    WorkOrderDetailOut,
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
    _report_pdf_storage_path,
    _request_roles,
    _sync_maintenance_report_pdf_export,
    _validate_assignee,
    _wo_load_options,
    _work_order_status_allows_report,
    _work_order_to_out,
    validate_tags,
)
from .router import router

_ASSIGNABLE_ROLES = (
    UserRole.site_manager,
    UserRole.client_admin,
    UserRole.technician,
    UserRole.company_engineer,
    UserRole.manager,
    UserRole.company_admin,
)


@router.get("/{work_order_id}/detail", response_model=WorkOrderDetailOut)
def get_work_order_detail(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> WorkOrderDetailOut:
    """Bundle WO + history/comments/assignable/documents/report for detail page (P9)."""
    wo = db.execute(
        select(WorkOrder)
        .where(WorkOrder.id == work_order_id)
        .options(*_wo_load_options(), joinedload(WorkOrder.report))
    ).scalar_one_or_none()
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.technician and wo.assignee_user_id != current.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.client_admin and current.client_id and wo.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = db.scalars(
            select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_type == "work_order", AuditLog.entity_id == str(wo.id))
        .options(joinedload(AuditLog.actor_user))
        .order_by(AuditLog.created_at.desc())
    ).all()
    history = [
        AuditLogOut(
            id=log.id,
            actor_user_id=log.actor_user_id,
            actor_name=(log.actor_user.full_name or log.actor_user.email) if log.actor_user else None,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            before_json=log.before_json,
            after_json=log.after_json,
            created_at=log.created_at,
        )
        for log in logs
    ]

    comment_rows = db.scalars(
        select(Comment)
        .where(Comment.work_order_id == wo.id)
        .options(joinedload(Comment.user))
        .order_by(Comment.created_at.asc())
    ).all()
    comments = [
        CommentOut(
            id=c.id,
            work_order_id=c.work_order_id,
            user_id=c.user_id,
            user_name=(c.user.full_name or c.user.email) if c.user else None,
            content=c.content,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comment_rows
    ]

    assignable_users = [
        UserBrief.model_validate(u)
        for u in db.scalars(
            select(User)
            .where(
                User.tenant_id == current.tenant_id,
                User.is_active.is_(True),
                User.role.in_(_ASSIGNABLE_ROLES),
            )
            .order_by(User.full_name)
        ).all()
    ]

    doc_rows = db.scalars(
        select(WorkOrderDocument)
        .where(WorkOrderDocument.work_order_id == wo.id)
        .options(joinedload(WorkOrderDocument.uploaded_by))
        .order_by(WorkOrderDocument.created_at.desc())
    ).all()
    documents = [
        DocumentOut(
            id=d.id,
            work_order_id=d.work_order_id,
            uploaded_by_user_id=d.uploaded_by_user_id,
            uploaded_by_name=(
                (d.uploaded_by.full_name or d.uploaded_by.email) if d.uploaded_by else None
            ),
            file_name=d.file_name,
            file_size=d.file_size,
            file_type=d.file_type,
            file_url=d.file_url,
            description=d.description,
            created_at=d.created_at,
        )
        for d in doc_rows
    ]

    report = MaintenanceReportOut.model_validate(wo.report) if wo.report else None
    return WorkOrderDetailOut(
        work_order=_work_order_to_out(wo),
        history=history,
        comments=comments,
        assignable_users=assignable_users,
        documents=documents,
        report=report,
    )


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
) -> Response:
    """Serve a work-order document. Report PDFs are always regenerated (incl. verified/closed)."""
    wo = _access_wo(db, current, work_order_id)
    doc = db.get(WorkOrderDocument, document_id)
    if not doc or doc.work_order_id != wo.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="DOCUMENT_NOT_FOUND")
    if doc.description != REPORT_PDF_DOC_DESCRIPTION:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="DOWNLOAD_ONLY_FOR_SERVER_GENERATED_PDFS",
        )

    report = wo.report
    if report is None:
        report = db.scalars(
            select(MaintenanceReport).where(MaintenanceReport.work_order_id == wo.id)
        ).first()
    if report is None:
        # Fall back to previously stored bytes if the report row is gone.
        path = _report_pdf_storage_path(doc.id)
        if not path.is_file():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="FILE_MISSING")
        return FileResponse(
            path,
            media_type=doc.file_type or "application/pdf",
            filename=doc.file_name,
        )

    name = (doc.file_name or "").lower()
    pdf_lang = "ar" if ("-ar-" in name or "_ar_" in name) else "en"
    wo = _reload_wo_with_users(db, wo.id)
    pdf_bytes = _sync_maintenance_report_pdf_export(
        db, wo=wo, report=report, current=current, pdf_lang=pdf_lang
    )
    db.commit()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="maintenance-report-{pdf_lang}-{stamp}.pdf"'
            ),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
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
