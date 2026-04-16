from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _encode(payload: dict[str, Any], expires_delta: timedelta, secret: str) -> str:
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def create_access_token(
    *,
    user_id: UUID,
    tenant_id: UUID,
    role: str,
    is_platform_admin: bool,
) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "is_platform_admin": is_platform_admin,
        "type": "access",
    }
    return _encode(
        payload,
        timedelta(minutes=s.access_token_expire_minutes),
        s.secret_key,
    )


def create_refresh_token(*, user_id: UUID, tenant_id: UUID) -> str:
    s = get_settings()
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "type": "refresh",
    }
    return _encode(
        payload,
        timedelta(days=s.refresh_token_expire_days),
        s.secret_key,
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
