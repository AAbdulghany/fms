from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import Site, User, UserRole, UserSiteScope

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    cred: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
) -> User:
    if cred is None or not cred.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="NOT_AUTHENTICATED")
    payload = decode_token(cred.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    try:
        uid = UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_TOKEN")
    user = db.get(User, uid)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="USER_INACTIVE")

    # SECURITY FIX: Set the global tenant context for the request
    from app.database import tenant_context
    tenant_context.set(user.tenant_id)

    return user


def tenant_id(user: User) -> UUID:
    return user.tenant_id


def require_roles(*roles: UserRole):
    def _dep(current: Annotated[User, Depends(get_current_user)]) -> User:
        if current.is_platform_admin:
            return current
        if current.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
        return current

    return _dep


def ensure_site_access(db: Session, current: User, site_id: UUID) -> Site:
    """Verify the current user can access the given site (tenant + role scope checks).

    Mirrors the _ensure_site helper in locations.py but lives in deps.py so it
    can be shared across route modules (work_orders, assets, …).
    """
    site = db.get(Site, site_id)
    if not site or site.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    if current.role == UserRole.client_admin and current.client_id and site.client_id != current.client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    if current.role == UserRole.site_manager:
        scoped = list(
            db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        )
        if site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    return site


def ensure_client_access(current: User, client_id: UUID) -> None:
    """Verify the current user can act on the given client_id.

    super_admin and company_admin are unrestricted.  client_admin is limited to
    their own client_id; any other client_id raises 403.
    """
    if current.role == UserRole.client_admin and current.client_id and current.client_id != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
