"""Clean local DEV seed: 1 tenant, 1 hospital client, current roles, A1–A4 baselines.

Wipes tenant data (keeps platform verticals/templates), then creates:
  - Orbit Dev Co (tenant) + full subscription
  - Cairo General Hospital (vertical=hospital) + Main Campus site
  - All existing role users (same emails as test_seed)
  - Adopt hospital-relevant asset type templates
  - Sample bilingual parts + default TaxProfile 15%

Run from backend/:
  python -m app.cli.clean_dev_seed
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from decimal import Decimal

from sqlalchemy import select

from app.cli._seed_lib import create_seed_user, truncate_tenant_data
from app.cli._seed_passwords import seed_password
from app.cli.test_seed import SEED_USER_SPECS
from app.database import SessionLocal, engine
from app.models import (
    Client,
    Part,
    Site,
    Tenant,
    TenantSubscription,
    UserRole,
    UserSiteScope,
)
from app.models.asset_types import AssetTypeTemplate, AssetTypeTemplateVertical, Vertical
from app.schema_ensure import ensure_schema
from app.services.asset_types import apply_client_vertical
from app.services.asset_types_service import adopt_templates
from app.services.billing_setup import (
    ensure_client_active_contract,
    ensure_tenant_pricing_profile,
)
from app.services.platform_bootstrap import (
    ensure_default_packages,
    ensure_platform_settings,
    run_wave0_platform_bootstrap,
)
from app.services.tax_profiles import ensure_default_tax_profile
from app.services.report_template_sync import sync_std_insp_all_tenants

TENANT_NAME = "Orbit Dev Co"
HOSPITAL_NAME = "Cairo General Hospital"
HOSPITAL_CODE = "CGH-01"
SITE_NAME = "Main Campus"

SAMPLE_PARTS = [
    ("FILT-HEPA-01", "HEPA Filter 24x24", "فلتر هيبا ٢٤×٢٤", "120.00"),
    ("BELT-V-A42", "V-Belt A42", "سير V مقاس A42", "45.50"),
    ("OIL-COMP-5L", "Compressor Oil 5L", "زيت كمبروسور ٥ لتر", "89.00"),
    ("GASKET-FL-01", "Flange Gasket DN50", "جوان فلنشة DN50", "18.00"),
    ("SENSOR-TMP-NTC", "NTC Temp Sensor", "حساس حرارة NTC", "65.00"),
]


def seed_clean_dev() -> dict:
    ensure_schema(engine)
    with SessionLocal() as db:
        run_wave0_platform_bootstrap(db)
        db.commit()

    with SessionLocal() as db:
        info = _seed(db)
        db.commit()

    print("\n--- CLEAN DEV READY ---")
    print(f"  Tenant: {TENANT_NAME}")
    print(f"  Client: {HOSPITAL_NAME} (hospital)")
    print(f"  Site:   {SITE_NAME}")
    for spec in SEED_USER_SPECS:
        print(f"  {spec.email} / {seed_password(spec.pw_local)} ({spec.role.value})")
    print("-----------------------")
    return info


def _seed(db) -> dict:
    truncate_tenant_data(db)

    packages = ensure_default_packages(db)
    ensure_platform_settings(db)

    tenant = Tenant(name=TENANT_NAME, status="active", settings_json={})
    db.add(tenant)
    db.flush()

    full = packages.get("full") or next(iter(packages.values()))
    db.add(
        TenantSubscription(
            tenant_id=tenant.id,
            package_id=full.id,
            status="active",
        )
    )
    db.flush()

    ensure_default_tax_profile(db, tenant.id)
    ensure_tenant_pricing_profile(db, tenant.id)

    client = Client(
        tenant_id=tenant.id,
        legal_name=HOSPITAL_NAME,
        code=HOSPITAL_CODE,
        status="active",
    )
    db.add(client)
    db.flush()
    apply_client_vertical(db, client, vertical_code="hospital", activity_type="hospital")
    db.flush()

    site = Site(
        tenant_id=tenant.id,
        client_id=client.id,
        name=SITE_NAME,
        timezone="Africa/Cairo",
        address_json={"city": "Cairo", "country": "EG"},
        status="active",
    )
    db.add(site)
    db.flush()

    ensure_client_active_contract(db, tenant.id, client.id)

    for spec in SEED_USER_SPECS:
        use_spec = spec
        if spec.role == UserRole.client_admin:
            use_spec = dc_replace(spec, client_id=client.id)
        user = create_seed_user(db, tenant.id, use_spec)
        db.flush()
        if spec.role in (UserRole.site_manager, UserRole.technician):
            db.add(UserSiteScope(user_id=user.id, site_id=site.id))

    hospital = db.scalar(select(Vertical).where(Vertical.code == "hospital"))
    tmpl_ids: list = []
    if hospital:
        all_tmpls = list(
            db.scalars(
                select(AssetTypeTemplate).where(AssetTypeTemplate.is_active.is_(True))
            ).all()
        )
        for tmpl in all_tmpls:
            tag_ids = set(
                db.scalars(
                    select(AssetTypeTemplateVertical.vertical_id).where(
                        AssetTypeTemplateVertical.template_id == tmpl.id
                    )
                ).all()
            )
            # Universal (no tags) or hospital-tagged
            if not tag_ids or hospital.id in tag_ids:
                tmpl_ids.append(tmpl.id)
    adopted = 0
    if tmpl_ids:
        result = adopt_templates(db, tenant.id, tmpl_ids)
        adopted = len(result.get("created") or [])

    # Ensure standard inspection templates exist for PM defaults
    sync_std_insp_all_tenants(db)

    for sku, en, ar, cost in SAMPLE_PARTS:
        db.add(
            Part(
                tenant_id=tenant.id,
                sku=sku,
                name=en,
                name_en=en,
                name_ar=ar,
                unit_cost_sar=Decimal(cost),
            )
        )

    db.flush()
    return {
        "tenant_id": str(tenant.id),
        "client_id": str(client.id),
        "site_id": str(site.id),
        "asset_types_adopted": adopted,
        "parts": len(SAMPLE_PARTS),
    }


if __name__ == "__main__":
    seed_clean_dev()
