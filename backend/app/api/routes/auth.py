from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


def _resolve_login_identifier(body: LoginRequest) -> str:
    ident = (body.identifier or body.email or "").strip()
    return ident


def _authenticate_user_by_identifier(db: Session, ident: str, password: str) -> User | None:
    """Match email or username case-insensitively; require exactly one password match (tenant-safe)."""
    lower = ident.lower()
    candidates = db.query(User).filter(
        or_(
            func.lower(User.email) == lower,
            and_(User.username.isnot(None), func.lower(User.username) == lower),
        )
    ).all()

    matching = [u for u in candidates if verify_password(password, u.password_hash)]
    if len(matching) != 1:
        return None
    return matching[0]


def _must_change_password(user: User) -> bool:
    return bool((user.metadata_json or {}).get("must_change_password"))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    ident = _resolve_login_identifier(body)
    if not ident:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="IDENTIFIER_REQUIRED")

    user = _authenticate_user_by_identifier(db, ident, body.password)
    if not user:
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
        must_change_password=_must_change_password(user),
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
        must_change_password=_must_change_password(user),
    )


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "ok", "detail": "CLIENT_DISCARD_TOKENS"}
