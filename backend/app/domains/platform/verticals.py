"""A1 — GET /verticals and GET /asset-type-catalog endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import User, UserRole
from app.models.asset_types import (
    AssetType,
    AssetTypeTemplate,
    AssetTypeTemplateVertical,
    Vertical,
)
from app.schemas.asset_types import AssetTypeTemplateOut, VerticalOut

router = APIRouter(tags=["verticals"])

# catalog readable by company_admin, super_admin, super_user only
_catalog_roles = Depends(
    require_roles(UserRole.company_admin, UserRole.super_admin, UserRole.super_user)
)


@router.get("/verticals", response_model=list[VerticalOut])
def list_verticals(
    db: Annotated[Session, Depends(get_db)],
    _current: Annotated[User, Depends(get_current_user)],
) -> list[VerticalOut]:
    """List active verticals ordered by sort_order. Available to any authenticated user."""
    rows = db.scalars(
        select(Vertical).where(Vertical.is_active.is_(True)).order_by(Vertical.sort_order)
    ).all()
    return [VerticalOut.model_validate(r) for r in rows]


@router.get("/asset-type-catalog", response_model=list[AssetTypeTemplateOut])
def list_asset_type_catalog(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _roles: Annotated[User, _catalog_roles],
    vertical: str | None = Query(None, description="Filter by vertical code"),
) -> list[AssetTypeTemplateOut]:
    """List active catalog templates. With *vertical*, returns templates tagged for that vertical
    plus universal templates (no vertical tags). Each item carries ``adopted`` and ``asset_type_id``
    for the caller's tenant.
    """
    q = select(AssetTypeTemplate).where(AssetTypeTemplate.is_active.is_(True))
    templates = list(db.scalars(q).all())

    if vertical:
        v = db.scalar(
            select(Vertical).where(Vertical.code == vertical, Vertical.is_active.is_(True))
        )
        if v:
            filtered: list[AssetTypeTemplate] = []
            for tmpl in templates:
                tags = db.scalars(
                    select(AssetTypeTemplateVertical.vertical_id).where(
                        AssetTypeTemplateVertical.template_id == tmpl.id
                    )
                ).all()
                # universal (no tags) or tagged with the requested vertical
                if not tags or v.id in tags:
                    filtered.append(tmpl)
            templates = filtered

    # Build adoption map for this tenant
    adopted_map: dict[UUID, UUID] = {}  # template_id → asset_type.id
    for at in db.scalars(
        select(AssetType).where(
            AssetType.tenant_id == current.tenant_id,
            AssetType.source_template_id.is_not(None),
        )
    ).all():
        if at.source_template_id:
            adopted_map[at.source_template_id] = at.id

    result: list[AssetTypeTemplateOut] = []
    for tmpl in templates:
        vert_ids = db.scalars(
            select(AssetTypeTemplateVertical.vertical_id).where(
                AssetTypeTemplateVertical.template_id == tmpl.id
            )
        ).all()
        vert_codes = []
        for vid in vert_ids:
            v_row = db.get(Vertical, vid)
            if v_row:
                vert_codes.append(v_row.code)

        is_adopted = tmpl.id in adopted_map
        out = AssetTypeTemplateOut(
            id=tmpl.id,
            code=tmpl.code,
            name_en=tmpl.name_en,
            name_ar=tmpl.name_ar,
            vertical_codes=vert_codes,
            default_max_age_years=tmpl.default_max_age_years,
            default_max_repair_count=tmpl.default_max_repair_count,
            default_criticality=tmpl.default_criticality,
            default_frequency=tmpl.default_frequency,
            version=tmpl.version,
            is_active=tmpl.is_active,
            adopted=is_adopted,
            asset_type_id=adopted_map.get(tmpl.id),
        )
        result.append(out)

    return result
