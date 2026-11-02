"""
Minimal seed: one tenant + one platform Super Admin only.

Idempotent: if the Super Admin email already exists, does nothing.

Selected by SEED_MODULE=super in app.cli.docker_migrate.

Env (optional):
  SUPER_ADMIN_EMAIL       default aabdulghany@orbittech.co
  SUPER_ADMIN_USERNAME    default local-part of email (aabdulghany)
  SUPER_ADMIN_PASSWORD    if unset, a random temp password is generated
  SUPER_ADMIN_FULL_NAME   default Super Admin
  SUPER_ADMIN_TENANT_NAME default Orbit Platform

CLI:
  uv run python -m app.seed_super
"""

from __future__ import annotations

import os
import secrets
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Tenant, User, UserRole


def _env(name: str, default: str) -> str:
    return (os.environ.get(name) or default).strip()


def _resolve_identity() -> tuple[str, str, str, str]:
    email = _env("SUPER_ADMIN_EMAIL", "aabdulghany@orbittech.co").lower()
    username = _env("SUPER_ADMIN_USERNAME", email.split("@", 1)[0])
    full_name = _env("SUPER_ADMIN_FULL_NAME", "Super Admin")
    tenant_name = _env("SUPER_ADMIN_TENANT_NAME", "Orbit Platform")
    return email, username, full_name, tenant_name


def _resolve_password() -> tuple[str, bool]:
    """Return (password, generated)."""
    explicit = os.environ.get("SUPER_ADMIN_PASSWORD", "").strip()
    if explicit:
        return explicit, False
    # URL-safe temp password; printed once in migrate logs.
    return secrets.token_urlsafe(18), True


def seed_super(db: Session) -> dict[str, Any]:
    """Create platform Super Admin if missing. Caller must commit."""
    email, username, full_name, tenant_name = _resolve_identity()

    existing = db.scalars(select(User).where(User.email == email)).first()
    if existing:
        print(f"Super user already exists: {email} (tenant {existing.tenant_id}).")
        print("No changes made.")
        return {
            "email": email,
            "username": existing.username or username,
            "created": False,
            "tenant_id": str(existing.tenant_id),
        }

    tenant = db.scalars(select(Tenant).where(Tenant.name == tenant_name)).first()
    if not tenant:
        tenant = Tenant(name=tenant_name, status="active", settings_json={})
        db.add(tenant)
        db.flush()
        print(f"Created tenant: {tenant_name}")
    else:
        print(f"Using existing tenant: {tenant_name}")

    password, generated = _resolve_password()
    user = User(
        tenant_id=tenant.id,
        email=email,
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        role=UserRole.super_user,
        locale="en",
        is_platform_admin=True,
        is_active=True,
        metadata_json={"seed_profile": "super"},
    )
    db.add(user)
    db.flush()

    print("Super user created.")
    print(f"  Email:    {email}")
    print(f"  Username: {username}")
    print(f"  Password: {password}")
    if generated:
        print("  (temporary — change after first login)")
    else:
        print("  (from SUPER_ADMIN_PASSWORD)")

    return {
        "email": email,
        "username": username,
        "created": True,
        "password_generated": generated,
        "tenant_id": str(tenant.id),
        # Password only in logs, not returned to API callers.
    }


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_super(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
