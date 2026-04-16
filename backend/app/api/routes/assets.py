from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Asset, Site, User, UserRole, UserSiteScope
from app.schemas import AssetCreate, AssetOut
from app.services.audit import write_audit

router = APIRouter(prefix="/assets", tags=["assets"])

_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.site_manager))


@router.get("", response_model=list[AssetOut])
def list_assets(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    site_id: UUID | None = Query(None),
) -> list[Asset]:
    q = select(Asset).where(Asset.tenant_id == current.tenant_id)
    if site_id:
        q = q.where(Asset.site_id == site_id)
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if not scoped:
            return []
        q = q.where(Asset.site_id.in_(scoped))
    if current.role == UserRole.client_admin and current.client_id:
        site_rows = db.scalars(select(Site.id).where(Site.client_id == current.client_id)).all()
        if not site_rows:
            return []
        q = q.where(Asset.site_id.in_(site_rows))
    return list(db.scalars(q).all())


@router.post("", response_model=AssetOut)
def create_asset(
    body: AssetCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> Asset:
    site = db.get(Site, body.site_id)
    if not site or site.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_SITE")
    a = Asset(
        tenant_id=current.tenant_id,
        site_id=body.site_id,
        parent_asset_id=body.parent_asset_id,
        name=body.name,
        category=body.category,
        model=body.model,
        serial=body.serial,
    )
    db.add(a)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="asset",
        entity_id=str(a.id),
        after={"name": body.name},
    )
    db.commit()
    db.refresh(a)
    return a
