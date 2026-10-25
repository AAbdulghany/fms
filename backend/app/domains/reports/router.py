from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import MaintenanceReport, ReportStatus, Tenant, User, UserRole, UserSiteScope, WorkOrder
from app.schemas import MaintenanceReportOut, RejectReportBody
from app.services.audit import write_audit
from app.services.maintenance_report_pdf import resolve_report_locale
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


def _assert_wo_access(db: Session, current: User, wo: WorkOrder) -> None:
    """Mirror work_orders._access_wo RBAC for report endpoints."""
    if (
        current.role == UserRole.technician
        and wo.assignee_user_id != current.id
        and getattr(wo, "return_assignee_user_id", None) != current.id
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.client_admin and current.client_id and wo.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")


def _restore_return_assignee(db: Session, current: User, wo: WorkOrder | None) -> None:
    """After approval or rejection, give the work order back to the person who sent it."""
    if wo is None or wo.return_assignee_user_id is None:
        return
    previous = wo.return_assignee_user_id
    old = wo.assignee_user_id
    wo.assignee_user_id = previous
    wo.return_assignee_user_id = None
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="assign",
        entity_type="work_order",
        entity_id=str(wo.id),
        before={"assignee_user_id": str(old) if old else None},
        after={"assignee_user_id": str(previous)},
    )


def _get_report(db: Session, current: User, report_id: UUID) -> MaintenanceReport:
    r = db.get(MaintenanceReport, report_id)
    if not r or r.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    wo = r.work_order
    if wo:
        _assert_wo_access(db, current, wo)
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
    _restore_return_assignee(db, current, r.work_order)
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
    _restore_return_assignee(db, current, r.work_order)
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
    lang: str | None = Query(None, description="Report language: ar or en"),
) -> Response:
    """Always regenerate the PDF from current report + WO data (any WO status, incl. verified/closed)."""
    from app.domains.work_orders._common import _sync_maintenance_report_pdf_export

    r = _get_report(db, current, report_id)
    wo = db.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == r.work_order_id)
        .options(
            joinedload(WorkOrder.site),
            joinedload(WorkOrder.asset),
            joinedload(WorkOrder.assignee_user),
            joinedload(WorkOrder.client),
            joinedload(WorkOrder.documents),
        )
    ).first()
    tenant = db.get(Tenant, r.tenant_id)
    lang_code, _dir = resolve_report_locale(tenant.settings_json if tenant else {}, lang)

    if wo is None:
        company = tenant.name if tenant else ""
        pdf_bytes = render_report_summary_pdf(
            tenant_name=company,
            work_order_title="",
            work_order_id="",
            answers=r.answers_json or {},
            template_schema=dict(r.template_snapshot_json or {}),
            platform_company_name=company,
            client_name="",
            lang=lang_code,
            dir_=_dir,
        )
    else:
        pdf_bytes = _sync_maintenance_report_pdf_export(
            db, wo=wo, report=r, current=current, pdf_lang=lang_code
        )
        db.commit()

    suffix = lang_code if lang else "report"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="maintenance-report-{suffix}-{stamp}.pdf"'
            ),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
