from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import User, UserRole
from app.rbac import (
    COMPANY_ADMIN_CREATABLE,
    can_create_role,
    can_manage_tenant_users,
    can_remove_members,
    tenant_admin_roles_for_require,
)
from app.schemas import UserCreateBody, UserCreateResponse, UserListOut, UserPatchBody, UserPatchMe, UserPublic

# Backward-compatible alias used by existing tests.
UserCreateRequest = UserCreateBody
from app.services.audit import write_audit
from app.services.provisioning import generate_initial_password

router = APIRouter(prefix="/users", tags=["users"])

_tenant_admin = Depends(require_roles(*tenant_admin_roles_for_require()))


@router.get("/me", response_model=UserPublic)
def me(current: Annotated[User, Depends(get_current_user)]) -> User:
    return current


@router.patch("/me", response_model=UserPublic)
def patch_me(
    body: UserPatchMe,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    """Allow authenticated user to update their full_name and/or password.
    Username changes are explicitly NOT allowed.
    """
    if body.full_name is not None:
        current.full_name = body.full_name.strip()
    if body.password is not None:
        current.password_hash = hash_password(body.password)
        meta = dict(current.metadata_json or {})
        meta["must_change_password"] = False
        current.metadata_json = meta
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update_self",
        entity_type="user",
        entity_id=str(current.id),
        after={"full_name": current.full_name},
    )
    db.commit()
    db.refresh(current)
    return current


@router.get("", response_model=list[UserListOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _tenant_admin],
) -> list[UserListOut]:
    """List all users in the tenant."""
    users = db.scalars(
        select(User)
        .where(User.tenant_id == current.tenant_id)
        .order_by(User.created_at.desc())
    ).all()
    return [UserListOut.from_user(u) for u in users]


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreateBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _tenant_admin],
) -> UserCreateResponse:
    """Create a new user within the current tenant."""
    if not can_create_role(current, user_in.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create role '{user_in.role}'",
        )

    existing = db.scalars(
        select(User).where(
            User.tenant_id == current.tenant_id,
            User.email == user_in.email,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="EMAIL_ALREADY_IN_USE",
        )

    auto_password: str | None = None
    if user_in.password:
        pwd_hash = hash_password(user_in.password)
        must_change = False
    else:
        auto_password = generate_initial_password()
        pwd_hash = hash_password(auto_password)
        must_change = True

    new_user = User(
        tenant_id=current.tenant_id,
        email=user_in.email,
        password_hash=pwd_hash,
        full_name=user_in.full_name,
        role=user_in.role,
        locale=user_in.locale,
        phone=user_in.phone,
        client_id=user_in.client_id,
        is_active=True,
        is_platform_admin=False,
        metadata_json={"must_change_password": must_change},
    )
    db.add(new_user)
    db.flush()

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create_user",
        entity_type="user",
        entity_id=str(new_user.id),
        after={
            "email": new_user.email,
            "role": str(new_user.role),
            **({"initial_password_generated": True} if auto_password else {}),
        },
    )

    db.commit()
    db.refresh(new_user)
    return UserCreateResponse(
        user=UserPublic.model_validate(new_user),
        initial_password=auto_password,
    )


@router.patch("/{user_id}", response_model=UserPublic)
def patch_user(
    user_id: UUID,
    body: UserPatchBody,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _tenant_admin],
) -> User:
    """Tenant admins can edit users; sw_dev cannot deactivate (remove) members."""
    if not can_manage_tenant_users(current):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    user = db.get(User, user_id)
    if not user or user.tenant_id != current.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")

    if body.is_active is False and not can_remove_members(current):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CANNOT_REMOVE_MEMBERS")

    if body.role is not None and not can_create_role(current, body.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot assign role '{body.role}'",
        )

    if current.role == UserRole.company_engineer and user.role in {
        UserRole.company_admin,
        UserRole.company_engineer,
    }:
        if body.role is not None or body.is_active is False:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    if current.role == UserRole.company_admin and user.role in {
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.company_engineer,
    }:
        if body.role is not None or body.is_active is False or body.full_name is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role is not None:
        user.role = body.role
    if body.locale is not None:
        user.locale = body.locale

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update_user",
        entity_type="user",
        entity_id=str(user.id),
        after={
            "full_name": user.full_name,
            "is_active": user.is_active,
            "role": str(user.role),
        },
    )

    db.commit()
    db.refresh(user)
    return user
