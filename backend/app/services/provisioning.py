"""Generate usernames, passwords, and synthetic emails for provisioned accounts."""

from __future__ import annotations

import re
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


def company_slug(legal_name: str) -> str:
    """Derive a URL-safe slug from a company legal name.

    Lowercases, strips non-alphanumeric characters and truncates to 32 chars.
    Example: "Giza Systems LLC" → "gizasystemsllc"
    """
    slug = re.sub(r"[^a-z0-9]", "", legal_name.lower())
    return slug[:32]


def build_manager_username(first_name: str, role_suffix: str, slug: str) -> str:
    """Build a structured manager username.

    Args:
        first_name: Manager's first name (e.g. "Abdullah").
        role_suffix: 'cmgr' for client manager, 'smgr' for site manager.
        slug: Company slug derived from legal name (e.g. "gizasystems").

    Returns:
        Username like "abdullah-cmgr@gizasystems".
    """
    name = re.sub(r"[^a-z0-9]", "", first_name.lower().split()[0])
    return f"{name}-{role_suffix}@{slug}"


def ensure_unique_username(db: Session, tenant_id: UUID, base_username: str) -> str:
    """Return *base_username* if available, else append -2, -3, … until unique."""
    exists = db.scalar(
        select(User.id).where(User.tenant_id == tenant_id, User.username == base_username)
    )
    if not exists:
        return base_username
    for i in range(2, 100):
        candidate = f"{base_username}-{i}"
        exists = db.scalar(
            select(User.id).where(User.tenant_id == tenant_id, User.username == candidate)
        )
        if not exists:
            return candidate
    raise RuntimeError("Could not allocate unique username")


# Keep backward-compatible alias used by older routes before being updated.
def unique_username(db: Session, tenant_id: UUID, prefix: str) -> str:
    """Legacy: random hex suffix username. Prefer build_manager_username + ensure_unique_username."""
    for _ in range(40):
        u = f"{prefix}-{secrets.token_hex(3)}".lower()
        exists = db.scalar(select(User.id).where(User.tenant_id == tenant_id, User.username == u))
        if not exists:
            return u
    raise RuntimeError("Could not allocate username")


def next_client_code(db: Session, tenant_id: UUID, legal_name: str = "") -> str:
    """Generate a unique client code derived from company name slug + year."""
    year = datetime.now().year
    slug_part = company_slug(legal_name)[:8].upper() if legal_name else ""
    prefix = f"C-{slug_part}-{year}" if slug_part else f"C-{year}"
    for _ in range(40):
        code = f"{prefix}-{secrets.token_hex(2).upper()}"
        exists = db.scalar(
            select(Client.id).where(Client.tenant_id == tenant_id, Client.code == code)
        )
        if not exists:
            return code
    raise RuntimeError("Could not allocate client code")
