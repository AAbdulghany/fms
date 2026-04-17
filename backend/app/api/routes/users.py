from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import User, UserRole
from app.schemas import UserPublic
from app.services.audit import write_audit

router = APIRouter(prefix="/users", tags=["users"])

_super_admin_only = Depends(require_roles(UserRole.super_admin))


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole
    locale: str = "ar"
    phone: str | None = None
    client_id: str | None = None


@router.get("/me", response_model=UserPublic)
def me(current: Annotated[User, Depends(get_current_user)]) -> User:
    return current


@router.get("", response_model=list[UserPublic])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _super_admin_only],
) -> list[User]:
    """List all users in the tenant (super_admin only)."""
    users = db.scalars(
        select(User)
        .where(User.tenant_id == current.tenant_id)
        .order_by(User.created_at.desc())
    ).all()
    return list(users)


@router.post("", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _super_admin_only],
) -> User:
    """Create a new user (super_admin only). Can create company_admin or technician roles."""
    # Validate role: super_admin can only create company_admin and technician
    if user_in.role not in (UserRole.company_admin, UserRole.technician):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super admin can only create company_admin or technician users"
        )
    
    # Check if email already exists in tenant
    existing = db.scalars(
        select(User).where(
            User.tenant_id == current.tenant_id,
            User.email == user_in.email
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered in this tenant"
        )
    
    # Create user
    new_user = User(
        tenant_id=current.tenant_id,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        locale=user_in.locale,
        phone=user_in.phone,
        client_id=user_in.client_id if user_in.client_id else None,
        is_active=True,
        is_platform_admin=False,
    )
    db.add(new_user)
    
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create_user",
        entity_type="user",
        entity_id=str(new_user.id),
    )
    
    db.commit()
    db.refresh(new_user)
    return new_user
