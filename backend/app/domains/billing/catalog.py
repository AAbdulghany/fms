from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Contract, Part, PricingProfile, User, UserRole
from app.schemas import ContractCreate, ContractOut, PartCreate, PartOut, PricingProfileCreate, PricingProfileOut
from app.services.audit import write_audit

router = APIRouter(tags=["catalog"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


@router.get("/parts-catalog", response_model=list[PartOut])
def list_parts(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Part]:
    return list(db.scalars(select(Part).where(Part.tenant_id == current.tenant_id)).all())


@router.post("/parts-catalog", response_model=PartOut)
def create_part(
    body: PartCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Part:
    p = Part(
        tenant_id=current.tenant_id,
        sku=body.sku,
        name=body.name,
        unit_cost_sar=body.unit_cost_sar,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.get("/pricing-profiles", response_model=list[PricingProfileOut])
def list_pricing(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[PricingProfile]:
    return list(db.scalars(select(PricingProfile).where(PricingProfile.tenant_id == current.tenant_id)).all())


@router.post("/pricing-profiles", response_model=PricingProfileOut)
def create_pricing(
    body: PricingProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> PricingProfile:
    pr = PricingProfile(
        tenant_id=current.tenant_id,
        name=body.name,
        hourly_rate_sar=body.hourly_rate_sar,
        parts_markup_percent=body.parts_markup_percent,
        default_service_fee_sar=body.default_service_fee_sar,
        emergency_surcharge_percent=body.emergency_surcharge_percent,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


@router.get("/contracts", response_model=list[ContractOut])
def list_contracts(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Contract]:
    return list(db.scalars(select(Contract).where(Contract.tenant_id == current.tenant_id)).all())


@router.post("/contracts", response_model=ContractOut)
def create_contract(
    body: ContractCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Contract:
    pr = db.get(PricingProfile, body.pricing_profile_id)
    if not pr or pr.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PRICING_PROFILE")
    c = Contract(
        tenant_id=current.tenant_id,
        client_id=body.client_id,
        pricing_profile_id=body.pricing_profile_id,
        name=body.name,
        currency=body.currency,
    )
    db.add(c)
    write_audit(db, tenant_id=current.tenant_id, actor=current, action="create", entity_type="contract")
    db.commit()
    db.refresh(c)
    return c
