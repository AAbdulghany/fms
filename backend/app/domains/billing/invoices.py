from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_feature, require_roles
from app.database import get_db
from app.models import Client, Invoice, InvoiceStatus, User, UserRole, WorkOrder
from app.schemas import InvoiceOut, InvoicePatchBody, SendInvoiceBody
from app.services.audit import write_audit
from app.services.billing import (
    ALLOWED_INVOICE_CURRENCIES,
    apply_invoice_charge_edits,
    extract_invoice_charges,
    recalculate_draft_invoice,
)
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


def _invoice_out(db: Session, inv: Invoice) -> InvoiceOut:
    client = db.get(Client, inv.client_id)
    wo = db.get(WorkOrder, inv.work_order_id)
    meta = inv.metadata_json or {}
    charges = extract_invoice_charges(inv)
    base = InvoiceOut.model_validate(inv)
    return base.model_copy(
        update={
            "billing_email": (meta.get("billing_email") or (client.billing_email if client else None)),
            "notes": meta.get("notes") or "",
            "work_order_title": (meta.get("work_order_title") or (wo.title if wo else "") or ""),
            "client_name": client.legal_name if client else None,
            "labor_hours": charges["labor_hours"],
            "labor_rate_sar": charges["labor_rate_sar"],
            "labor_amount_sar": charges["labor_amount_sar"],
            "service_fee_sar": charges["service_fee_sar"],
        }
    )


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    status: str | None = Query(None),
    client_id: UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> list[InvoiceOut]:
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
    return [_invoice_out(db, inv) for inv in rows]


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    db.refresh(inv)
    _ = inv.line_items
    return _invoice_out(db, inv)


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def patch_invoice(
    invoice_id: UUID,
    body: InvoicePatchBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status not in (InvoiceStatus.draft, InvoiceStatus.approved):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVOICE_NOT_EDITABLE")

    meta = dict(inv.metadata_json or {})
    if body.due_date is not None:
        inv.due_date = body.due_date
    if body.issued_at is not None:
        inv.issued_at = datetime.combine(body.issued_at, datetime.min.time()).replace(tzinfo=timezone.utc)
    if body.currency is not None:
        cur = body.currency.strip().upper()
        if cur not in ALLOWED_INVOICE_CURRENCIES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_CURRENCY")
        inv.currency = cur
    if body.billing_email is not None:
        meta["billing_email"] = body.billing_email.strip()
    if body.notes is not None:
        meta["notes"] = body.notes
    if body.work_order_title is not None:
        meta["work_order_title"] = body.work_order_title.strip()
    inv.metadata_json = meta

    charge_fields = (body.labor_hours, body.labor_rate_sar, body.service_fee_sar)
    if any(v is not None for v in charge_fields):
        try:
            apply_invoice_charge_edits(
                inv,
                labor_hours=body.labor_hours,
                labor_rate_sar=body.labor_rate_sar,
                service_fee_sar=body.service_fee_sar,
            )
        except ValueError as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update_invoice",
        entity_type="invoice",
        entity_id=str(inv.id),
        after={
            "due_date": str(inv.due_date) if inv.due_date else None,
            "currency": inv.currency,
        },
    )
    db.commit()
    db.refresh(inv)
    _ = inv.line_items
    return _invoice_out(db, inv)


@router.post("/{invoice_id}/recalculate", response_model=InvoiceOut)
def recalculate_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    try:
        recalculate_draft_invoice(db, inv)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="recalculate_invoice",
        entity_type="invoice",
        entity_id=str(inv.id),
    )
    db.commit()
    db.refresh(inv)
    _ = inv.line_items
    return _invoice_out(db, inv)


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
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status != InvoiceStatus.draft:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    inv.status = InvoiceStatus.approved
    write_audit(db, tenant_id=current.tenant_id, actor=current, action="approve", entity_type="invoice", entity_id=str(inv.id))
    db.commit()
    db.refresh(inv)
    return _invoice_out(db, inv)


@router.post("/{invoice_id}/send", response_model=InvoiceOut)
def send_invoice(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
    body: SendInvoiceBody | None = None,
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    if inv.status not in (InvoiceStatus.approved, InvoiceStatus.draft):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_STATUS")
    client = db.get(Client, inv.client_id)
    meta = inv.metadata_json or {}
    to_email = (body.recipient_email if body and body.recipient_email else None) or meta.get("billing_email") or (
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
    return _invoice_out(db, inv)


@router.post("/{invoice_id}/mark-paid", response_model=InvoiceOut)
def mark_paid(
    invoice_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> InvoiceOut:
    inv = _access_invoice(db, current, invoice_id)
    inv.status = InvoiceStatus.paid
    inv.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inv)
    return _invoice_out(db, inv)
