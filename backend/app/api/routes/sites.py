from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Client, Site, User, UserRole, UserSiteScope
from app.schemas import SiteCreate, SiteOut
from app.services.audit import write_audit

router = APIRouter(prefix="/sites", tags=["sites"])

_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.site_manager))


@router.get("", response_model=list[SiteOut])
def list_sites(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    client_id: UUID | None = Query(None),
) -> list[Site]:
    q = select(Site).where(Site.tenant_id == current.tenant_id)
    if client_id:
        q = q.where(Site.client_id == client_id)
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Site.client_id == current.client_id)
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if not scoped:
            return []
        q = q.where(Site.id.in_(scoped))
    return list(db.scalars(q).all())


@router.post("", response_model=SiteOut)
def create_site(
    body: SiteCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> Site:
    client = db.get(Client, body.client_id)
    if not client or client.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_CLIENT")
    s = Site(
        tenant_id=current.tenant_id,
        client_id=body.client_id,
        name=body.name,
        timezone=body.timezone,
        address_json=body.address_json,
    )
    db.add(s)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="site",
        entity_id=str(s.id),
        after={"name": body.name},
    )
    db.commit()
    db.refresh(s)
    return s
