"""
Minimal development seed: one tenant + one super_admin user only.

Idempotent: if the super user email already exists, does nothing.

Run from repo root (recommended):
  uv run python -m app.seed_super

Canonical module: app.cli.seed_super (shim at app.seed_super for compatibility).
"""

from sqlalchemy import select

from app.cli._demo_passwords import demo_password
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import Tenant, User, UserRole

TENANT_NAME = "Demo Facility Co"
SUPER_EMAIL = "super@demo.com"


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_super = db.scalars(
            select(User).where(
                User.email == SUPER_EMAIL,
                User.role == UserRole.super_admin,
            )
        ).first()
        if existing_super:
            print(f"Super user already exists: {SUPER_EMAIL} (tenant {existing_super.tenant_id}).")
            print("No changes made.")
            return

        tenant = db.scalars(select(Tenant).where(Tenant.name == TENANT_NAME)).first()
        if not tenant:
            tenant = Tenant(name=TENANT_NAME, status="active", settings_json={})
            db.add(tenant)
            db.flush()
            print(f"Created tenant: {TENANT_NAME}")
        else:
            print(f"Using existing tenant: {TENANT_NAME}")

        password = demo_password("super")
        user = User(
            tenant_id=tenant.id,
            email=SUPER_EMAIL,
            password_hash=hash_password(password),
            full_name="Super Admin",
            role=UserRole.super_admin,
            locale="en",
            is_platform_admin=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("Super user created.")
        print(f"  Email:    {SUPER_EMAIL}")
        print(f"  Password: {password}")
        print("Change the password after first login in production.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
