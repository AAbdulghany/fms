from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Invoice, InvoiceStatus, User, UserRole, WorkOrder
from app.schemas import InvoiceOut
from app.services.audit import write_audit
from app.services.billing import build_invoice_for_work_order
from app.services.pdf import render_invoice_pdf

router = APIRouter(prefix="/invoices", tags=["invoices"])

_finance = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


def _access_invoice(db: Session, current: User, inv_id: UUID) -> Invoice:
    inv = db.get(Invoice, inv_id)
    if not inv or inv.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.client_admin and current.client_id and inv.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return inv


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Invoice]:
    q = select(Invoice).where(Invoice.tenant_id == current.tenant_id)
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Invoice.client_id == current.client_id)
    q = q.options(selectinload(Invoice.line_items)).order_by(Invoice.number.desc())
    rows = db.scalars(q).all()
    return list(rows)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Invoice:
    inv = _access_invoice(db, current, invoice_id)
    db.refresh(inv)
    _ = inv.line_items
    return inv


@router.get("/{invoice_id}/pdf")
def invoice_pdf(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    inv = _access_invoice(db, current, invoice_id)
    pdf_bytes = render_invoice_pdf(db, invoice=inv)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{inv.number}.pdf"'},
    )


@router.post("/{invoice_id}/approve", response_model=InvoiceOut)
def approve_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> Invoice:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status != InvoiceStatus.draft:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    inv.status = InvoiceStatus.approved
    write_audit(db, tenant_id=current.tenant_id, actor=current, action="approve", entity_type="invoice", entity_id=str(inv.id))
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
def send_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> Invoice:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status not in (InvoiceStatus.approved, InvoiceStatus.draft):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    inv.status = InvoiceStatus.sent
    inv.issued_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut)
def mark_paid(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> Invoice:
    inv = _access_invoice(db, current, invoice_id)
    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    return inv
