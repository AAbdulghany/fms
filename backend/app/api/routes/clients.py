from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Client, User, UserRole
from app.schemas import ClientCreate, ClientOut
from app.services.audit import write_audit

router = APIRouter(prefix="/clients", tags=["clients"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


@router.get("", response_model=list[ClientOut])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Client]:
    q = select(Client).where(Client.tenant_id == current.tenant_id)
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Client.id == current.client_id)
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
