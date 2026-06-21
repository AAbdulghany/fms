"""
Development seed: tenant + role hierarchy users only (no demo company/WO).

Run from backend folder: python -m app.seed
"""
from app.core.security import hash_password
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Tenant, User, UserRole

TENANT_NAME = "Demo Facility Co"

SEED_USERS = [
    ("admin@demo.com", "Company Admin", UserRole.company_admin, "admin123"),
    ("engineer@demo.com", "Company Engineer", UserRole.company_engineer, "engineer123"),
    ("tech@demo.com", "Technician", UserRole.technician, "tech123"),
    ("clientmgr@demo.com", "Client Manager", UserRole.client_admin, "client123"),
    ("sitemgr@demo.com", "Site Manager", UserRole.site_manager, "site123"),
]


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        tenant = db.scalars(select(Tenant).where(Tenant.name == TENANT_NAME)).first()
        if not tenant:
            tenant = Tenant(name=TENANT_NAME, status="active", settings_json={})
            db.add(tenant)
            db.flush()
            print(f"Created tenant: {TENANT_NAME}")
        else:
            print(f"Using tenant: {TENANT_NAME}")

        created = 0
        for email, full_name, role, password in SEED_USERS:
            exists = db.scalars(select(User).where(User.email == email)).first()
            if exists:
                continue
            db.add(
                User(
                    tenant_id=tenant.id,
                    email=email,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    role=role,
                    locale="ar",
                    is_active=True,
                    is_platform_admin=False,
                )
            )
            created += 1

        db.commit()
        if created == 0:
            print("Seed already applied (all users exist).")
        else:
            print(f"Seed complete — {created} user(s) created.")
        print("Accounts:")
        for email, _, _, password in SEED_USERS:
            print(f"  {email} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
