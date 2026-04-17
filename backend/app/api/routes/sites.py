from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import Client, Site, User, UserRole, UserSiteScope
from app.schemas import SiteCreate, SiteOut, SiteProvisionRequest, SiteProvisionResponse
from app.services.audit import write_audit
from app.services.provisioning import generate_initial_password, synthetic_email, unique_username

router = APIRouter(prefix="/sites", tags=["sites"])

_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.site_manager))
_provision = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


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


@router.post("/provision", response_model=SiteProvisionResponse)
def provision_site_with_manager(
    body: SiteProvisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _provision],
) -> SiteProvisionResponse:
    """Create a site and a site_manager user with generated credentials."""
    client = db.get(Client, body.client_id)
    if not client or client.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_CLIENT")

    s = Site(
        tenant_id=current.tenant_id,
        client_id=body.client_id,
        name=body.name.strip(),
        timezone=body.timezone,
        address_json={},
        status="active",
    )
    db.add(s)
    db.flush()

    username = unique_username(db, current.tenant_id, "smgr")
    pwd = generate_initial_password()
    email = synthetic_email(username, current.tenant_id)

    mgr = User(
        tenant_id=current.tenant_id,
        client_id=None,
        email=email,
        username=username,
        password_hash=hash_password(pwd),
        full_name=body.manager_full_name.strip(),
        role=UserRole.site_manager,
        locale="ar",
        is_active=True,
        is_platform_admin=False,
        metadata_json={"must_change_password": True},
    )
    db.add(mgr)
    db.flush()
    db.add(UserSiteScope(user_id=mgr.id, site_id=s.id))

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="provision",
        entity_type="site",
        entity_id=str(s.id),
        after={"name": s.name, "manager_username": username},
    )
    db.commit()
    db.refresh(s)
    return SiteProvisionResponse(
        site=SiteOut.model_validate(s),
        manager_username=username,
        manager_email=email,
        initial_password=pwd,
    )


@router.get("/{site_id}", response_model=SiteOut)
def get_site(
    site_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Site:
    s = db.get(Site, site_id)
    if not s or s.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.client_admin and current.client_id:
        cl = db.get(Client, current.client_id)
        if cl and s.client_id != cl.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        if s.id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return s
