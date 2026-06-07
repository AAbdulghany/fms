from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserCreateBody, UserCreateResponse, UserListOut, UserPatchBody, UserPatchMe, UserPublic

# Backward-compatible alias used by existing tests.
UserCreateRequest = UserCreateBody
from app.services.audit import write_audit
from app.services.provisioning import generate_initial_password

router = APIRouter(prefix="/users", tags=["users"])

_super_admin_only = Depends(require_roles(UserRole.super_admin))
_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))

# Roles that company_admin is permitted to create within their own tenant.
_COMPANY_ADMIN_CREATABLE = {
    UserRole.technician,
    UserRole.client_admin,
    UserRole.site_manager,
}


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
    _: Annotated[User, _admin],
) -> list[UserListOut]:
    """List all users in the tenant.

    super_admin sees all; company_admin sees all users within their tenant.
    """
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
    _: Annotated[User, _admin],
) -> UserCreateResponse:
    """Create a new user.

    super_admin can create any non-super_admin role.
    company_admin can create technician, client_admin, site_manager.
    """
    if current.role == UserRole.super_admin:
        if user_in.role == UserRole.super_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create another super_admin via this endpoint",
            )
    elif current.role == UserRole.company_admin:
        if user_in.role not in _COMPANY_ADMIN_CREATABLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"company_admin cannot create role '{user_in.role}'",
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
    _: Annotated[User, _admin],
) -> User:
    """super_admin and company_admin can edit users within the same tenant."""
    user = db.get(User, user_id)
    if not user or user.tenant_id != current.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")

    # company_admin cannot escalate roles or edit super_admins
    if current.role == UserRole.company_admin:
        if user.role == UserRole.super_admin:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
        if body.role is not None and body.role not in _COMPANY_ADMIN_CREATABLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"company_admin cannot assign role '{body.role}'",
            )

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
