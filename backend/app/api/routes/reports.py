from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import MaintenanceReport, ReportStatus, Tenant, User, UserRole, WorkOrder
from app.schemas import MaintenanceReportOut, RejectReportBody
from app.services.audit import write_audit
from app.services.pdf import render_report_summary_pdf

router = APIRouter(prefix="/reports", tags=["reports"])

_approvers = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.client_admin,
        UserRole.manager,
    )
)


def _get_report(db: Session, current: User, report_id: UUID) -> MaintenanceReport:
    r = db.get(MaintenanceReport, report_id)
    if not r or r.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    wo = r.work_order
    if current.role == UserRole.client_admin and current.client_id and wo.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return r


@router.post("/{report_id}/approve", response_model=MaintenanceReportOut)
def approve_report(
    report_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _approvers],
) -> MaintenanceReport:
    r = _get_report(db, current, report_id)
    if r.status != ReportStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_SUBMITTED")
    r.status = ReportStatus.approved
    r.approved_at = datetime.now(timezone.utc)
    r.approved_by_user_id = current.id
    r.rejection_reason = None
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="approve",
        entity_type="maintenance_report",
        entity_id=str(r.id),
    )
    db.commit()
    db.refresh(r)
    return r


@router.post("/{report_id}/reject", response_model=MaintenanceReportOut)
def reject_report(
    report_id: UUID,
    body: RejectReportBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _approvers],
) -> MaintenanceReport:
    r = _get_report(db, current, report_id)
    if r.status != ReportStatus.submitted:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="REPORT_NOT_SUBMITTED")
    r.status = ReportStatus.rejected
    r.rejection_reason = body.reason
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="reject",
        entity_type="maintenance_report",
        entity_id=str(r.id),
    )
    db.commit()
    db.refresh(r)
    return r


@router.get("/{report_id}/pdf")
def report_pdf(
    report_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    r = _get_report(db, current, report_id)
    wo = db.get(WorkOrder, r.work_order_id)
    tenant = db.get(Tenant, r.tenant_id)
    pdf_bytes = render_report_summary_pdf(
        tenant_name=tenant.name if tenant else "",
        work_order_title=wo.title if wo else str(wo.id),
        answers=r.answers_json or {},
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
    )
