from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import User, UserRole

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
