"""A3 — Work order parts consumption endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Part, User, UserRole, WorkOrder
from app.schemas import WorkOrderPartCreate, WorkOrderPartOut
from app.services.work_order_parts import add_wo_part, list_wo_parts, remove_wo_part

from .router import router

_staff = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.site_manager,
        UserRole.technician,
    )
)


def _access_wo(db: Session, current: User, work_order_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="WORK_ORDER_NOT_FOUND")
    return wo


def _to_out(db: Session, row) -> WorkOrderPartOut:
    part = db.get(Part, row.part_id)
    return WorkOrderPartOut(
        id=row.id,
        work_order_id=row.work_order_id,
        part_id=row.part_id,
        quantity=row.quantity,
        unit_cost_sar=row.unit_cost_sar,
        part_sku=part.sku if part else None,
        part_name=part.name if part else None,
    )


@router.get("/{work_order_id}/parts", response_model=list[WorkOrderPartOut])
def get_wo_parts(
    work_order_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[WorkOrderPartOut]:
    _access_wo(db, current, work_order_id)
    rows = list_wo_parts(db, current.tenant_id, work_order_id)
    return [_to_out(db, r) for r in rows]


@router.post(
    "/{work_order_id}/parts",
    response_model=WorkOrderPartOut,
    status_code=status.HTTP_201_CREATED,
)
def post_wo_part(
    work_order_id: UUID,
    body: WorkOrderPartCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _staff],
) -> WorkOrderPartOut:
    wo = _access_wo(db, current, work_order_id)
    row = add_wo_part(
        db,
        tenant_id=current.tenant_id,
        work_order=wo,
        part_id=body.part_id,
        quantity=body.quantity,
    )
    db.commit()
    db.refresh(row)
    return _to_out(db, row)


@router.delete("/{work_order_id}/parts/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wo_part(
    work_order_id: UUID,
    line_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _staff],
) -> None:
    _access_wo(db, current, work_order_id)
    remove_wo_part(
        db, tenant_id=current.tenant_id, work_order_id=work_order_id, line_id=line_id
    )
    db.commit()
