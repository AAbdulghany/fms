"""Tenant subscription management (Phase 3.1)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import _load_user, require_roles
from app.database import get_db
from app.models import Tenant, User, UserRole
from app.schemas import SubscriptionOut, SubscriptionUpdate
from app.services.subscription import get_subscription, update_subscription

router = APIRouter(prefix="/tenants", tags=["tenants"])

_super = Depends(require_roles(UserRole.super_admin))


@router.get("/{tenant_id}/subscription", response_model=SubscriptionOut)
def read_subscription(
    tenant_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(_load_user)],
    _: Annotated[User, _super],
) -> SubscriptionOut:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if tenant.id != current.tenant_id and not current.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    sub = get_subscription(db, tenant)
    return SubscriptionOut.model_validate(sub)


@router.patch("/{tenant_id}/subscription", response_model=SubscriptionOut)
def patch_subscription(
    tenant_id: UUID,
    body: SubscriptionUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(_load_user)],
    _: Annotated[User, _super],
) -> SubscriptionOut:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if tenant.id != current.tenant_id and not current.is_platform_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    sub = update_subscription(db, tenant, body.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(tenant)
    return SubscriptionOut.model_validate(sub)
