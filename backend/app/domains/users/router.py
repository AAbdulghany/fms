from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.database import get_db
from app.models import Tenant, User, UserRole
from app.rbac import (
    COMPANY_ADMIN_CREATABLE,
    can_create_role,
    can_manage_tenant_users,
    can_remove_members,
    is_platform_staff,
    tenant_admin_roles_for_require,
)
from app.schemas import UserCreateBody, UserCreateResponse, UserListOut, UserPatchBody, UserPatchMe, UserMeOut, UserPublic

# Backward-compatible alias used by existing tests.
UserCreateRequest = UserCreateBody
from app.services.audit import write_audit
from app.services.provisioning import generate_initial_password
from app.services.subscription import get_subscription

router = APIRouter(prefix="/users", tags=["users"])

_tenant_admin = Depends(require_roles(*tenant_admin_roles_for_require()))


def _user_me_out(db: Session, user: User) -> UserMeOut:
    meta = user.metadata_json or {}
    base = UserPublic.model_validate(user)
    features: list[str] = []
    if user.is_platform_admin:
        features = ["assets", "invoices", "csv_import", "advanced_scheduling", "ai_maintenance"]
    elif user.tenant_id:
        tenant = db.get(Tenant, user.tenant_id)
        if tenant:
            features = list(get_subscription(db, tenant).get("features") or [])
    data = base.model_dump()
    data["phone"] = user.phone
    data["job_title"] = meta.get("job_title")
    data["accreditation"] = meta.get("accreditation")
    data["features"] = features
    return UserMeOut(**data)


@router.get("/me", response_model=UserMeOut)
def me(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> UserMeOut:
    return _user_me_out(db, current)


@router.patch("/me", response_model=UserMeOut)
def patch_me(
    body: UserPatchMe,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> UserMeOut:
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
    if body.phone is not None:
        current.phone = body.phone.strip() if body.phone else None
    meta = dict(current.metadata_json or {})
    if body.job_title is not None:
        meta["job_title"] = body.job_title.strip() if body.job_title else None
    if body.accreditation is not None:
        meta["accreditation"] = body.accreditation.strip() if body.accreditation else None
    if body.job_title is not None or body.accreditation is not None:
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
    return _user_me_out(db, current)


@router.get("", response_model=list[UserListOut])
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _tenant_admin],
) -> list[UserListOut]:
    """List users in the tenant; hide platform staff from non-platform viewers."""
    q = select(User).where(User.tenant_id == current.tenant_id)
    if not is_platform_staff(current):
        q = q.where(
            User.is_platform_admin.is_(False),
            User.role.notin_([UserRole.super_user, UserRole.sw_dev]),
        )
    q = q.order_by(User.created_at.desc())
    users = db.scalars(q).all()
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

    # NT-P5-C06-BE: tenant admins may patch phone/email for client_admin and site_manager
    _contact_editable_roles = {UserRole.client_admin, UserRole.site_manager}
    _can_edit_contact = current.role in {UserRole.super_admin, UserRole.company_admin}
    if body.phone is not None:
        if not _can_edit_contact or user.role not in _contact_editable_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CANNOT_EDIT_CONTACT")
        user.phone = body.phone.strip() if body.phone else None
    if body.email is not None:
        if not _can_edit_contact or user.role not in _contact_editable_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CANNOT_EDIT_CONTACT")
        new_email = body.email.strip()
        existing = db.scalar(
            select(User).where(
                User.tenant_id == current.tenant_id,
                User.email == new_email,
                User.id != user.id,
            )
        )
        if existing:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="EMAIL_ALREADY_IN_USE")
        user.email = new_email

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
