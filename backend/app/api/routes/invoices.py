from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_feature, require_roles
from app.database import get_db
from app.models import Client, Invoice, InvoiceStatus, User, UserRole
from app.schemas import InvoiceOut, SendInvoiceBody
from app.services.audit import write_audit
from app.services.email import send_invoice_email
from app.services.pdf import render_invoice_pdf

router = APIRouter(
    prefix="/invoices",
    tags=["invoices"],
    dependencies=[Depends(require_feature("invoices"))],
)

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
    status: str | None = Query(None),
    client_id: UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> list[Invoice]:
    q = select(Invoice).where(Invoice.tenant_id == current.tenant_id)
    
    # Role-based filtering
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Invoice.client_id == current.client_id)
    
    # P2-F1 Additional filters
    if status:
        try:
            st = InvoiceStatus(status)
            q = q.where(Invoice.status == st)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    
    if client_id:
        q = q.where(Invoice.client_id == client_id)
    
    if date_from:
        q = q.where(Invoice.issued_at >= date_from)
    
    if date_to:
        q = q.where(Invoice.issued_at <= date_to)
    
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
    inline: bool = Query(False),
) -> Response:
    inv = _access_invoice(db, current, invoice_id)
    pdf_bytes = render_invoice_pdf(db, invoice=inv)
    disposition = "inline" if inline else "attachment"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="invoice-{inv.number}.pdf"'},
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
    body: SendInvoiceBody | None = None,
) -> Invoice:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status not in (InvoiceStatus.approved, InvoiceStatus.draft):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    client = db.get(Client, inv.client_id)
    to_email = (body.recipient_email if body and body.recipient_email else None) or (
        client.billing_email if client else None
    )
    if not to_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="NO_BILLING_EMAIL")
    pdf_bytes = render_invoice_pdf(db, invoice=inv)
    send_invoice_email(
        to_email,
        inv.number,
        pdf_bytes,
        client_name=client.legal_name if client else "",
    )
    inv.status = InvoiceStatus.sent
    inv.issued_at = datetime.now(timezone.utc)
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="send",
        entity_type="invoice",
        entity_id=str(inv.id),
        after={"recipient": to_email},
    )
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
