from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import Client, Site, User, UserRole, UserSiteScope
from app.rbac import tenant_admin_roles_for_require
from app.schemas import (
    ClientCreate,
    ClientOut,
    ClientProvisionRequest,
    ClientProvisionResponse,
    ClientUpdate,
)
from app.services.audit import write_audit
from app.services.provisioning import (
    build_manager_username,
    company_slug,
    ensure_unique_username,
    generate_initial_password,
    next_client_code,
    synthetic_email,
)

router = APIRouter(prefix="/clients", tags=["clients"])

_admin = Depends(require_roles(*tenant_admin_roles_for_require()))


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    include_archived: bool = False,
) -> list[Client]:
    q = select(Client).where(Client.tenant_id == current.tenant_id)
    if not include_archived:
        q = q.where(Client.status == "active")
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Client.id == current.client_id)
    if current.role == UserRole.site_manager:
        scoped_site_ids = db.scalars(
            select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)
        ).all()
        if not scoped_site_ids:
            return []
        client_ids = db.scalars(
            select(Site.client_id).where(Site.id.in_(scoped_site_ids)).distinct()
        ).all()
        if not client_ids:
            return []
        q = q.where(Client.id.in_(client_ids))
    return list(db.scalars(q).all())


@router.post("", response_model=ClientOut)
def create_client(
    body: ClientCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Client:
    c = Client(
        tenant_id=current.tenant_id,
        legal_name=body.legal_name,
        code=body.code,
        billing_email=body.billing_email,
        status="active",
        activity_type=body.activity_type,
    )
    db.add(c)
    db.flush()
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="client",
        entity_id=str(c.id),
        after={"legal_name": c.legal_name},
    )
    db.commit()
    db.refresh(c)
    return c


@router.post("/provision", response_model=ClientProvisionResponse)
def provision_client_with_manager(
    body: ClientProvisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> ClientProvisionResponse:
    """Create a company (client) and a client_admin user with generated username/password."""
    code = next_client_code(db, current.tenant_id, body.legal_name.strip())
    slug = company_slug(body.legal_name.strip())
    c = Client(
        tenant_id=current.tenant_id,
        legal_name=body.legal_name.strip(),
        code=code,
        billing_email=None,
        status="active",
        activity_type=body.activity_type,
    )
    db.add(c)
    db.flush()

    first_name = body.manager_full_name.strip().split()[0]
    base_username = build_manager_username(first_name, "cmgr", slug)
    username = ensure_unique_username(db, current.tenant_id, base_username)
    pwd = generate_initial_password()
    email = synthetic_email(username, current.tenant_id)

    mgr = User(
        tenant_id=current.tenant_id,
        client_id=c.id,
        email=email,
        username=username,
        password_hash=hash_password(pwd),
        full_name=body.manager_full_name.strip(),
        role=UserRole.client_admin,
        locale="ar",
        is_active=True,
        is_platform_admin=False,
        metadata_json={"must_change_password": True},
    )
    db.add(mgr)
    db.flush()

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="provision",
        entity_type="client",
        entity_id=str(c.id),
        after={"legal_name": c.legal_name, "manager_username": username},
    )
    db.commit()
    db.refresh(c)

    return ClientProvisionResponse(
        client=ClientOut.model_validate(c),
        company_id=c.id,
        company_code=c.code,
        manager_username=username,
        manager_email=email,
        initial_password=pwd,
    )


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> Client:
    c = db.get(Client, client_id)
    if not c or c.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.client_admin and current.client_id and c.id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return c


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: UUID,
    body: ClientUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Client:
    c = db.get(Client, client_id)
    if not c or c.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if body.legal_name is not None:
        c.legal_name = body.legal_name.strip()
    if body.code is not None:
        code = body.code.strip()
        dup = db.scalar(
            select(Client.id).where(
                Client.tenant_id == current.tenant_id,
                Client.code == code,
                Client.id != c.id,
            )
        )
        if dup:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CODE_IN_USE")
        c.code = code
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="client",
        entity_id=str(c.id),
        after={"legal_name": c.legal_name, "code": c.code},
    )
    db.commit()
    db.refresh(c)
    return c


@router.post("/{client_id}/archive", response_model=ClientOut)
def archive_client(
    client_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> Client:
    c = db.get(Client, client_id)
    if not c or c.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    c.status = "archived"
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="archive",
        entity_type="client",
        entity_id=str(c.id),
        after={"status": "archived"},
    )
    db.commit()
    db.refresh(c)
    return c
