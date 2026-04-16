from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User, UserRole, WorkOrder
from app.schemas import InvoiceOut
from app.services.audit import write_audit
from app.services.billing import build_invoice_for_work_order

router = APIRouter(tags=["billing"])

_finance = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


@router.post("/work-orders/{work_order_id}/generate-invoice", response_model=InvoiceOut)
def generate_invoice_from_wo(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _finance],
) -> InvoiceOut:
    wo = db.get(WorkOrder, work_order_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    try:
        inv = build_invoice_for_work_order(db, wo)
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
