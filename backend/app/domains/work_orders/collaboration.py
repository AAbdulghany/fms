"""Work orders — history, comments, documents."""

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
