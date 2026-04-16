from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_CREDENTIALS")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="USER_INACTIVE")
    s = get_settings()
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=user.role.value,
            is_platform_admin=user.is_platform_admin,
        ),
        refresh_token=create_refresh_token(user_id=user.id, tenant_id=user.tenant_id),
        expires_in=s.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="INVALID_REFRESH")
    from uuid import UUID

    user = db.get(User, UUID(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="USER_INACTIVE")
    s = get_settings()
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            role=user.role.value,
            is_platform_admin=user.is_platform_admin,
        ),
        refresh_token=create_refresh_token(user_id=user.id, tenant_id=user.tenant_id),
        expires_in=s.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "ok", "detail": "CLIENT_DISCARD_TOKENS"}
