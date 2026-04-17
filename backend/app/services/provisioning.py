"""Generate usernames, passwords, and synthetic emails for provisioned accounts."""

from __future__ import annotations

import secrets
import string
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, User


def generate_initial_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def synthetic_email(username: str, tenant_id: UUID) -> str:
    """Placeholder email unique across tenants (username may repeat in another tenant)."""
    safe = username.lower().replace(" ", "")
    tid = str(tenant_id).replace("-", "")[:12]
    return f"{safe}.{tid}@users.fms.local"


def unique_username(db: Session, tenant_id: UUID, prefix: str) -> str:
    for _ in range(40):
        u = f"{prefix}-{secrets.token_hex(3)}".lower()
        exists = db.scalar(select(User.id).where(User.tenant_id == tenant_id, User.username == u))
        if not exists:
            return u
    raise RuntimeError("Could not allocate username")


def next_client_code(db: Session, tenant_id: UUID) -> str:
    year = datetime.now().year
    for _ in range(40):
        code = f"C-{year}-{secrets.token_hex(2).upper()}"
        exists = db.scalar(select(Client.id).where(Client.tenant_id == tenant_id, Client.code == code))
        if not exists:
            return code
    raise RuntimeError("Could not allocate client code")
