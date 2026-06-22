"""
Pitch / demo seed: tenant + role hierarchy users only (no demo company/WO).

Mirrors app.seed exactly so the demo environment starts clean.
Run from backend folder: python -m app.pitch_seed

Canonical: app.cli.pitch_seed (shim at app.pitch_seed).
"""
from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.cli._demo_passwords import demo_password
from app.core.security import hash_password
from app.models import Tenant, TenantSubscription, User, UserRole
from app.services.platform_bootstrap import ensure_default_packages, ensure_platform_settings

TENANT_NAME = "Demo Facility Co"

SEED_USERS = [
    ("admin@demo.com", "Company Admin", UserRole.company_admin, "admin"),
    ("engineer@demo.com", "Company Engineer", UserRole.company_engineer, "engineer"),
    ("tech@demo.com", "Technician", UserRole.technician, "tech"),
    ("clientmgr@demo.com", "Client Manager", UserRole.client_admin, "client"),
    ("sitemgr@demo.com", "Site Manager", UserRole.site_manager, "site"),
]


def _clear_demo_data(db: Session) -> None:
    """Wipe all tenant data so re-seeding is idempotent."""
    bind = db.get_bind()
    from sqlalchemy import inspect as sa_inspect

    insp = sa_inspect(bind)
    if not insp.has_table("tenants"):
        return

    if bind.dialect.name == "postgresql":
        db.execute(
            text(
                "TRUNCATE TABLE audit_logs, invoice_line_items, invoices, maintenance_reports, "
                "work_orders, maintenance_schedules, assets, sites, clients, users, "
                "tenant_subscriptions, tenants, notifications CASCADE"
            )
        )
    else:
        from app.models import (
            Asset,
            AuditLog,
            Client,
            Invoice,
            InvoiceLineItem,
            MaintenanceReport,
            MaintenanceSchedule,
            Notification,
            Site,
            UserSiteScope,
            WorkOrder,
        )

        for model in (
            AuditLog,
            Notification,
            InvoiceLineItem,
            Invoice,
            MaintenanceReport,
            WorkOrder,
            MaintenanceSchedule,
            Asset,
            UserSiteScope,
            User,
            TenantSubscription,
            Site,
            Client,
            Tenant,
        ):
            db.query(model).delete()
        db.flush()


def seed_pitch_demo(db: Session) -> dict[str, str]:
    """Reset and seed pitch demo data (users only). Caller must commit."""
    _clear_demo_data(db)
    packages = ensure_default_packages(db)
    ensure_platform_settings(db)

    tenant = Tenant(name=TENANT_NAME, status="active", settings_json={})
    db.add(tenant)
    db.flush()

    db.add(
        TenantSubscription(
            tenant_id=tenant.id,
            package_id=packages["pro"].id,
            status="active",
        )
    )
    db.flush()

    created = 0
    for email, full_name, role, pw_local in SEED_USERS:
        exists = db.scalars(select(User).where(User.email == email)).first()
        if exists:
            continue
        password = demo_password(pw_local)
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

    db.flush()
    return {
        "tenant_id": str(tenant.id),
        "users_created": str(created),
    }


if __name__ == "__main__":
    from app.database import SessionLocal, engine
    from app.schema_ensure import ensure_schema
    from app.services.platform_bootstrap import run_wave0_platform_bootstrap

    ensure_schema(engine)
    with SessionLocal() as db:
        run_wave0_platform_bootstrap(db)
        db.commit()
    with SessionLocal() as db:
        info = seed_pitch_demo(db)
        db.commit()
        print("Pitch demo seeded (users only):", info)
        print("Accounts:")
        for email, _, _, pw_local in SEED_USERS:
            print(f"  {email} / {demo_password(pw_local)}")
