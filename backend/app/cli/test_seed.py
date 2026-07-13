"""Dev/CI seed: tenant + comprehensive role-hierarchy users ONLY.

No clients, sites, assets, or work orders — just enough data to exercise
every authentication role in automated tests and local development.

Run from backend folder:
  python -m app.test_seed   (shim) — or via docker_migrate SEED_MODULE=test
"""
from __future__ import annotations

from app.cli._demo_passwords import demo_password
from app.cli._seed_lib import UserSeedSpec, create_seed_user, truncate_tenant_data
from app.database import SessionLocal, engine
from app.models import Tenant, TenantSubscription, UserRole
from app.schema_ensure import ensure_schema
from app.services.platform_bootstrap import (
    ensure_default_packages,
    ensure_platform_settings,
    run_wave0_platform_bootstrap,
)

TENANT_NAME = "Orbit Demo Co"

SEED_USER_SPECS: list[UserSeedSpec] = [
    UserSeedSpec(
        email="super@demo.com",
        pw_local="super",
        role=UserRole.super_user,
        full_name="Super Admin",
        username="superadmin",
        phone="+966500000001",
        locale="en",
        is_platform=True,
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="swdev@demo.com",
        pw_local="swdev",
        role=UserRole.sw_dev,
        full_name="SW Developer",
        username="swdev",
        phone="+966500000002",
        locale="en",
        is_platform=True,
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="admin@demo.com",
        pw_local="admin",
        role=UserRole.company_admin,
        full_name="Company Admin",
        username="companyadmin",
        phone="+966500000003",
        locale="ar",
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="engineer@demo.com",
        pw_local="engineer",
        role=UserRole.company_engineer,
        full_name="Company Engineer",
        username="engineer",
        phone="+966500000004",
        locale="ar",
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="manager@demo.com",
        pw_local="manager",
        role=UserRole.manager,
        full_name="Operations Manager",
        username="manager",
        phone="+966500000005",
        locale="ar",
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="client@demo.com",
        pw_local="client",
        role=UserRole.client_admin,
        full_name="Client Admin",
        username="clientadmin",
        phone="+966500000006",
        locale="ar",
        # No client_id — test seed has no clients
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="site@demo.com",
        pw_local="site",
        role=UserRole.site_manager,
        full_name="Site Manager",
        username="sitemanager",
        phone="+966500000007",
        locale="ar",
        metadata_json={"seed_profile": "test"},
    ),
    UserSeedSpec(
        email="tech@demo.com",
        pw_local="tech",
        role=UserRole.technician,
        full_name="Field Technician",
        username="technician",
        phone="+966500000008",
        locale="ar",
        metadata_json={"seed_profile": "test"},
    ),
]


def seed_data() -> dict[str, str]:
    """Reset and seed dev/test users only. Called by docker_migrate."""
    ensure_schema(engine)
    with SessionLocal() as db:
        run_wave0_platform_bootstrap(db)
        db.commit()

    with SessionLocal() as db:
        result = _seed(db)
        db.commit()

    print("\n--- TEST USERS READY ---")
    for spec in SEED_USER_SPECS:
        print(f"  {spec.email} / {demo_password(spec.pw_local)} ({spec.role.value})")
    print("------------------------")
    return result


def _seed(db) -> dict[str, str]:
    """Wipe + re-create tenant and users. Caller must commit."""
    truncate_tenant_data(db)

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

    for spec in SEED_USER_SPECS:
        create_seed_user(db, tenant.id, spec)

    db.flush()
    return {
        "tenant_id": str(tenant.id),
        "users_created": str(len(SEED_USER_SPECS)),
    }


if __name__ == "__main__":
    seed_data()
