from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Contract, Part, PricingProfile, TaxProfile, User, UserRole
from app.schemas import (
    ContractCreate,
    ContractOut,
    PartBulkRequest,
    PartBulkResult,
    PartCreate,
    PartOut,
    PricingProfileCreate,
    PricingProfileOut,
    TaxProfileCreate,
    TaxProfileOut,
    TaxProfileUpdate,
)
from app.schemas.billing import ContractUpdate, PartUpdate
from app.services.audit import write_audit
from app.services.tax_profiles import ensure_default_tax_profile

router = APIRouter(tags=["catalog"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))

_PARTS_TEMPLATE_CSV = (
    "sku,name_en,name_ar,unit_cost_sar\n"
    "FILT-HEPA-01,HEPA Filter 24x24,فلتر هيبا ٢٤×٢٤,120.00\n"
    "BELT-V-A42,V-Belt A42,سير V مقاس A42,45.50\n"
    "OIL-COMP-5L,Compressor Oil 5L,زيت كمبروسور ٥ لتر,89.00\n"
)


def _part_display_name(name_en: str, name_ar: str, name: str = "") -> str:
    return (name_en or name or name_ar or "").strip()


@router.get("/parts-catalog", response_model=list[PartOut])
def list_parts(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    kind: str | None = None,
    q: str | None = None,
) -> list[Part]:
    stmt = select(Part).where(Part.tenant_id == current.tenant_id)
    if kind:
        k = kind.strip().lower().replace("-", "_")
        if k in ("raw", "raw_material", "material"):
            k = "raw_material"
        elif k in ("spare_asset", "spare", "asset"):
            k = "spare_asset"
        else:
            k = "part"
        stmt = stmt.where(Part.kind == k)
    needle = (q or "").strip()
    if needle:
        like = f"%{needle}%"
        stmt = stmt.where(
            (Part.sku.ilike(like))
            | (Part.name.ilike(like))
            | (Part.name_en.ilike(like))
            | (Part.name_ar.ilike(like))
        )
    return list(db.scalars(stmt.limit(80)).all())


@router.get("/parts-catalog/template.csv")
def parts_catalog_template(
    _: Annotated[User, Depends(get_current_user)],
) -> PlainTextResponse:
    """Downloadable CSV template for bulk parts import (EN + Egyptian Arabic)."""
    return PlainTextResponse(
        _PARTS_TEMPLATE_CSV,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="parts-catalog-template.csv"'},
    )


@router.post("/parts-catalog", response_model=PartOut)
def create_part(
    body: PartCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Part:
    display = _part_display_name(body.name_en, body.name_ar, body.name)
    p = Part(
        tenant_id=current.tenant_id,
        sku=body.sku.strip(),
        name=display,
        name_en=body.name_en or display,
        name_ar=body.name_ar or display,
        unit_cost_sar=body.unit_cost_sar,
        kind=body.kind or "part",
        qty_on_hand=body.qty_on_hand,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/parts-catalog/{part_id}", response_model=PartOut)
def update_part(
    part_id: UUID,
    body: PartUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Part:
    p = db.get(Part, part_id)
    if not p or p.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="PART_NOT_FOUND")
    data = body.model_dump(exclude_unset=True)
    if "kind" in data and data["kind"] is not None:
        k = str(data["kind"]).strip().lower().replace("-", "_")
        if k in ("raw", "raw_material", "material"):
            data["kind"] = "raw_material"
        elif k in ("spare_asset", "spare", "asset", "whole_asset"):
            data["kind"] = "spare_asset"
        else:
            data["kind"] = "part"
    if "name_en" in data or "name_ar" in data:
        en = data.get("name_en", p.name_en)
        ar = data.get("name_ar", p.name_ar)
        data["name"] = _part_display_name(en or "", ar or "", p.name)
    for key, val in data.items():
        setattr(p, key, val)
    db.commit()
    db.refresh(p)
    return p


@router.post("/parts-catalog/bulk", response_model=PartBulkResult)
def bulk_upsert_parts(
    body: PartBulkRequest,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> PartBulkResult:
    created = updated = skipped = 0
    errors: list[str] = []
    for i, item in enumerate(body.items):
        sku = (item.sku or "").strip()
        if not sku:
            skipped += 1
            errors.append(f"row {i + 1}: missing sku")
            continue
        en = (item.name_en or item.name or "").strip()
        ar = (item.name_ar or item.name or "").strip()
        display = _part_display_name(en, ar, item.name)
        try:
            cost = Decimal(str(item.unit_cost_sar or 0))
        except (InvalidOperation, TypeError):
            skipped += 1
            errors.append(f"row {i + 1} ({sku}): invalid unit_cost_sar")
            continue
        existing = db.scalar(
            select(Part).where(Part.tenant_id == current.tenant_id, Part.sku == sku)
        )
        kind_raw = (getattr(item, "kind", None) or "part").strip().lower().replace("-", "_")
        if kind_raw in ("raw", "raw_material", "material"):
            kind = "raw_material"
        elif kind_raw in ("spare_asset", "spare", "asset", "whole_asset"):
            kind = "spare_asset"
        else:
            kind = "part"
        try:
            qty = Decimal(str(getattr(item, "qty_on_hand", 0) or 0))
        except (InvalidOperation, TypeError):
            qty = Decimal("0")
        if existing:
            existing.name = display or existing.name
            existing.name_en = en or existing.name_en or existing.name
            existing.name_ar = ar or existing.name_ar or existing.name
            existing.unit_cost_sar = cost
            existing.kind = kind
            existing.qty_on_hand = qty
            updated += 1
        else:
            db.add(
                Part(
                    tenant_id=current.tenant_id,
                    sku=sku,
                    name=display,
                    name_en=en or display,
                    name_ar=ar or display,
                    unit_cost_sar=cost,
                    kind=kind,
                    qty_on_hand=qty,
                )
            )
            created += 1
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="bulk_upsert",
        entity_type="part",
        after={"created": created, "updated": updated, "skipped": skipped},
    )
    db.commit()
    return PartBulkResult(created=created, updated=updated, skipped=skipped, errors=errors)


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
    # Upsert General by name so Commercial Terms can re-save the default
    if body.name.strip().lower() == "general":
        existing = db.scalar(
            select(PricingProfile).where(
                PricingProfile.tenant_id == current.tenant_id,
                PricingProfile.name == "General",
            )
        )
        if existing:
            existing.hourly_rate_sar = body.hourly_rate_sar
            existing.parts_markup_percent = body.parts_markup_percent
            existing.default_service_fee_sar = body.default_service_fee_sar
            existing.emergency_surcharge_percent = body.emergency_surcharge_percent
            db.commit()
            db.refresh(existing)
            return existing
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
        tax_rate_percent=body.tax_rate_percent,
        tax_inclusive=body.tax_inclusive,
    )
    db.add(c)
    write_audit(db, tenant_id=current.tenant_id, actor=current, action="create", entity_type="contract")
    db.commit()
    db.refresh(c)
    return c


@router.patch("/contracts/{contract_id}", response_model=ContractOut)
def update_contract(
    contract_id: UUID,
    body: ContractUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Contract:
    c = db.get(Contract, contract_id)
    if not c or c.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CONTRACT_NOT_FOUND")
    data = body.model_dump(exclude_unset=True)
    if "pricing_profile_id" in data:
        pr = db.get(PricingProfile, data["pricing_profile_id"])
        if not pr or pr.tenant_id != current.tenant_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_PRICING_PROFILE")
    for key, val in data.items():
        setattr(c, key, val)
    db.commit()
    db.refresh(c)
    return c


@router.delete("/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(
    contract_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> None:
    """UAT #4 — soft-delete custom commercial term (status=cancelled)."""
    c = db.get(Contract, contract_id)
    if not c or c.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="CONTRACT_NOT_FOUND")
    c.status = "cancelled"
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="delete",
        entity_type="contract",
        entity_id=str(c.id),
    )
    db.commit()


@router.get("/tax-profiles", response_model=list[TaxProfileOut])
def list_tax_profiles(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[TaxProfile]:
    ensure_default_tax_profile(db, current.tenant_id)
    db.commit()
    return list(
        db.scalars(select(TaxProfile).where(TaxProfile.tenant_id == current.tenant_id)).all()
    )


@router.post("/tax-profiles", response_model=TaxProfileOut)
def create_tax_profile(
    body: TaxProfileCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TaxProfile:
    if body.is_default:
        for row in db.scalars(
            select(TaxProfile).where(TaxProfile.tenant_id == current.tenant_id)
        ).all():
            row.is_default = False
    tp = TaxProfile(
        tenant_id=current.tenant_id,
        name=body.name,
        rate_percent=body.rate_percent,
        tax_inclusive=body.tax_inclusive,
        rounding=body.rounding or "HALF_UP",
        is_default=body.is_default,
    )
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp


@router.patch("/tax-profiles/{profile_id}", response_model=TaxProfileOut)
def update_tax_profile(
    profile_id: UUID,
    body: TaxProfileUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TaxProfile:
    tp = db.get(TaxProfile, profile_id)
    if not tp or tp.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TAX_PROFILE_NOT_FOUND")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_default"):
        for row in db.scalars(
            select(TaxProfile).where(TaxProfile.tenant_id == current.tenant_id)
        ).all():
            row.is_default = False
    for key, val in data.items():
        setattr(tp, key, val)
    db.commit()
    db.refresh(tp)
    return tp
