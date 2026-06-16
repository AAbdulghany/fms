from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_current_user, require_feature, require_roles
from app.database import get_db
from app.models import Invoice, User, UserRole, WorkOrder
from app.schemas import GenerateInvoiceBody, InvoiceOut, InvoicePreviewOut
from app.services.audit import write_audit
from app.services.billing import build_invoice_for_work_order, preview_invoice_for_work_order

router = APIRouter(tags=["billing"], dependencies=[Depends(require_feature("invoices"))])

_finance = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


@router.get("/work-orders/{work_order_id}/invoice-preview", response_model=InvoicePreviewOut)
def invoice_preview(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
    currency: str | None = Query(None),
) -> InvoicePreviewOut:
    wo = db.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == work_order_id, WorkOrder.tenant_id == current.tenant_id)
        .options(
            joinedload(WorkOrder.client),
            joinedload(WorkOrder.site),
            joinedload(WorkOrder.assignee_user),
            joinedload(WorkOrder.report),
        )
    ).first()
    if not wo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    try:
        computed = preview_invoice_for_work_order(db, wo, currency_override=currency)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    completion = wo.closed_at or (wo.report.approved_at if wo.report else None)
    tech = wo.assignee_user.full_name if wo.assignee_user else None
    return InvoicePreviewOut(
        work_order_id=wo.id,
        work_order_title=wo.title or "",
        client_name=wo.client.legal_name if wo.client else "",
        site_name=wo.site.name if wo.site else "",
        technician_name=tech,
        completion_date=completion.date() if completion else None,
        currency=computed["currency"],
        labor_hours=computed["labor_hours"],
        labor_amount_sar=computed["labor_amount_sar"],
        parts=computed["parts"],
        service_fee_sar=computed["service_fee_sar"],
        emergency_surcharge_sar=computed["emergency_surcharge_sar"],
        subtotal_sar=computed["subtotal_sar"],
        tax_sar=computed["tax_sar"],
        total_sar=computed["total_sar"],
        work_summary=computed["work_summary"],
    )


@router.post("/work-orders/{work_order_id}/generate-invoice", response_model=InvoiceOut)
def generate_invoice_from_wo(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
    body: Optional[GenerateInvoiceBody] = Body(default=None),
) -> InvoiceOut:
    wo = db.get(WorkOrder, work_order_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    try:
        inv = build_invoice_for_work_order(db, wo, currency_override=body.currency if body else None)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="generate_invoice",
        entity_type="invoice",
        entity_id=str(inv.id),
    )
    db.commit()
    inv = db.scalars(
        select(Invoice)
        .where(Invoice.id == inv.id)
        .options(selectinload(Invoice.line_items))
    ).first()
    return InvoiceOut.model_validate(inv)
