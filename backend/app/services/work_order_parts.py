"""A3 — WorkOrderPart attach / list helpers."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Part, WorkOrder, WorkOrderPart


def list_wo_parts(db: Session, tenant_id: UUID, work_order_id: UUID) -> list[WorkOrderPart]:
    return list(
        db.scalars(
            select(WorkOrderPart).where(
                WorkOrderPart.tenant_id == tenant_id,
                WorkOrderPart.work_order_id == work_order_id,
            )
        ).all()
    )


def add_wo_part(
    db: Session,
    *,
    tenant_id: UUID,
    work_order: WorkOrder,
    part_id: UUID,
    quantity: Decimal,
) -> WorkOrderPart:
    if work_order.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="WORK_ORDER_NOT_FOUND")
    part = db.get(Part, part_id)
    if not part or part.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PART")
    qty = quantity if quantity > 0 else Decimal("1")
    row = WorkOrderPart(
        tenant_id=tenant_id,
        work_order_id=work_order.id,
        part_id=part.id,
        quantity=qty,
        unit_cost_sar=part.unit_cost_sar,
    )
    db.add(row)
    db.flush()
    return row


def remove_wo_part(
    db: Session, *, tenant_id: UUID, work_order_id: UUID, line_id: UUID
) -> None:
    row = db.get(WorkOrderPart, line_id)
    if (
        not row
        or row.tenant_id != tenant_id
        or row.work_order_id != work_order_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PART_LINE_NOT_FOUND")
    db.delete(row)
    db.flush()
