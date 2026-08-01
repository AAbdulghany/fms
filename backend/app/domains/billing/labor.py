"""P2-F4: Technician profiles, labor entries, weekly schedules."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import (
    LaborEntry,
    TechnicianProfile,
    TechnicianSchedule,
    User,
    UserRole,
    WorkOrder,
)
from app.schemas import (
    LaborEntryCreate,
    LaborEntryOut,
    TechnicianProfileCreate,
    TechnicianProfileOut,
    TechnicianProfileUpdate,
    TechnicianScheduleCreate,
    TechnicianScheduleOut,
)
from app.services.audit import write_audit

router = APIRouter(prefix="/labor", tags=["labor"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.manager))
_tech_or_admin = Depends(
    require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.manager,
        UserRole.technician,
    )
)


def _wo_in_tenant(db: Session, tenant_id: UUID, wo_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, wo_id)
    if not wo or wo.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return wo


@router.get("/profiles", response_model=list[TechnicianProfileOut])
def list_profiles(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[TechnicianProfile]:
    q = select(TechnicianProfile).where(TechnicianProfile.tenant_id == current.tenant_id)
    if current.role == UserRole.technician:
        q = q.where(TechnicianProfile.user_id == current.id)
    elif current.role not in (UserRole.super_admin, UserRole.company_admin, UserRole.manager):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return list(db.scalars(q.order_by(TechnicianProfile.created_at.desc())).all())


@router.post("/profiles", response_model=TechnicianProfileOut)
def create_profile(
    body: TechnicianProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TechnicianProfile:
    u = db.get(User, body.user_id)
    if not u or u.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_USER")
    if u.role != UserRole.technician:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="USER_NOT_TECHNICIAN")
    existing = db.scalars(
        select(TechnicianProfile).where(
            TechnicianProfile.tenant_id == current.tenant_id,
            TechnicianProfile.user_id == body.user_id,
        )
    ).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="PROFILE_EXISTS")
    p = TechnicianProfile(
        tenant_id=current.tenant_id,
        user_id=body.user_id,
        hourly_rate_sar=body.hourly_rate_sar,
        overtime_multiplier=body.overtime_multiplier,
        is_active=body.is_active,
        skills_json=body.skills_json,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/profiles/{user_id}", response_model=TechnicianProfileOut)
def update_profile(
    user_id: UUID,
    body: TechnicianProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TechnicianProfile:
    p = db.scalars(
        select(TechnicianProfile).where(
            TechnicianProfile.tenant_id == current.tenant_id,
            TechnicianProfile.user_id == user_id,
        )
    ).first()
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if body.hourly_rate_sar is not None:
        p.hourly_rate_sar = body.hourly_rate_sar
    if body.overtime_multiplier is not None:
        p.overtime_multiplier = body.overtime_multiplier
    if body.is_active is not None:
        p.is_active = body.is_active
    if body.skills_json is not None:
        p.skills_json = body.skills_json
    db.commit()
    db.refresh(p)
    return p


@router.get("/entries", response_model=list[LaborEntryOut])
def list_labor_entries(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    work_order_id: UUID | None = Query(None),
    user_id: UUID | None = Query(None),
) -> list[LaborEntry]:
    q = select(LaborEntry).where(LaborEntry.tenant_id == current.tenant_id)
    if work_order_id:
        q = q.where(LaborEntry.work_order_id == work_order_id)
    if user_id:
        q = q.where(LaborEntry.user_id == user_id)
    if current.role == UserRole.technician:
        q = q.where(LaborEntry.user_id == current.id)
    elif current.role not in (UserRole.super_admin, UserRole.company_admin, UserRole.manager):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return list(db.scalars(q.order_by(LaborEntry.work_date.desc())).all())


@router.post("/entries", response_model=LaborEntryOut)
def create_labor_entry(
    body: LaborEntryCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _tech_or_admin],
) -> LaborEntry:
    wo = _wo_in_tenant(db, current.tenant_id, body.work_order_id)
    u = db.get(User, body.user_id)
    if not u or u.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_USER")
    if current.role == UserRole.technician:
        if body.user_id != current.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
        if wo.assignee_user_id != current.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="NOT_ASSIGNEE")
    ent = LaborEntry(
        tenant_id=current.tenant_id,
        work_order_id=body.work_order_id,
        user_id=body.user_id,
        work_date=body.work_date,
        hours_regular=body.hours_regular,
        hours_overtime=body.hours_overtime,
        notes=body.notes,
    )
    db.add(ent)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="labor_entry",
        entity_id=str(ent.id),
        after={"work_order_id": str(wo.id), "hours": str(body.hours_regular)},
    )
    db.commit()
    db.refresh(ent)
    return ent


@router.get("/schedules", response_model=list[TechnicianScheduleOut])
def list_schedules(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    user_id: UUID | None = Query(None),
) -> list[TechnicianSchedule]:
    if current.role not in (
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.manager,
        UserRole.technician,
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    q = select(TechnicianSchedule).where(TechnicianSchedule.tenant_id == current.tenant_id)
    if current.role == UserRole.technician:
        q = q.where(TechnicianSchedule.user_id == current.id)
    elif user_id:
        q = q.where(TechnicianSchedule.user_id == user_id)
    return list(db.scalars(q.order_by(TechnicianSchedule.user_id, TechnicianSchedule.day_of_week)).all())


@router.post("/schedules", response_model=TechnicianScheduleOut)
def create_schedule(
    body: TechnicianScheduleCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TechnicianSchedule:
    u = db.get(User, body.user_id)
    if not u or u.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_USER")
    sch = TechnicianSchedule(
        tenant_id=current.tenant_id,
        user_id=body.user_id,
        day_of_week=body.day_of_week,
        start_time=body.start_time,
        end_time=body.end_time,
        is_active=body.is_active,
    )
    db.add(sch)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="SCHEDULE_CONFLICT")
    db.refresh(sch)
    return sch


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> None:
    sch = db.get(TechnicianSchedule, schedule_id)
    if not sch or sch.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    db.delete(sch)
    db.commit()
