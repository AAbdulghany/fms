from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Asset, Site, User, UserRole, UserSiteScope
from app.schemas import AssetCreate, AssetOut
from app.services.asset_lifecycle import get_lifecycle_timeline, reset_asset_lifecycle
from app.services.audit import write_audit

router = APIRouter(prefix="/assets", tags=["assets"])

_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.site_manager))


@router.get("", response_model=list[AssetOut])
def list_assets(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    site_id: UUID | None = Query(None),
    category: str | None = Query(None),
    search: str | None = Query(None),
) -> list[Asset]:
    q = select(Asset).where(Asset.tenant_id == current.tenant_id)
    
    # Role-based filtering
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
    
    # P2-F1 Additional filters
    if site_id:
        q = q.where(Asset.site_id == site_id)
    
    if category:
        q = q.where(Asset.category == category)
    
    if search:
        q = q.where(Asset.name.ilike(f"%{search}%"))
    
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
    if body.location_id:
        from app.models import Location

        loc = db.get(Location, body.location_id)
        if not loc or loc.tenant_id != current.tenant_id or loc.site_id != body.site_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_LOCATION")
    a = Asset(
        tenant_id=current.tenant_id,
        site_id=body.site_id,
        location_id=body.location_id,
        parent_asset_id=body.parent_asset_id,
        name=body.name,
        category=body.category,
        model=body.model,
        serial=body.serial,
        max_repair_count=body.max_repair_count,
        max_age_years=body.max_age_years,
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


@router.get("/{asset_id}/lifecycle")
def get_asset_lifecycle(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get asset lifecycle timeline and status (P2-F2)."""
    asset = db.get(Asset, asset_id)
    if not asset or asset.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    
    # Role-based access check
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if scoped and asset.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    if current.role == UserRole.client_admin and current.client_id:
        site = db.get(Site, asset.site_id)
        if not site or site.client_id != current.client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    try:
        timeline = get_lifecycle_timeline(db, asset_id)
        return timeline
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{asset_id}/reset-lifecycle", response_model=AssetOut)
def reset_lifecycle(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> Asset:
    """Reset asset lifecycle when physical asset is replaced (P2-F2)."""
    asset = db.get(Asset, asset_id)
    if not asset or asset.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    
    try:
        reset_asset = reset_asset_lifecycle(db, asset_id)
        write_audit(
            db,
            tenant_id=current.tenant_id,
            actor=current,
            action="reset_lifecycle",
            entity_type="asset",
            entity_id=str(asset_id),
        )
        db.commit()
        db.refresh(reset_asset)
        return reset_asset
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
