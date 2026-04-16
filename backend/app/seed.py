"""
Development seed: idempotent-ish — creates demo tenant, users, catalog, template, sample WO.
Run from backend folder: python -m app.seed
"""
from decimal import Decimal

from app.core.security import hash_password
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import (
    Asset,
    Client,
    Contract,
    Part,
    PricingProfile,
    ReportTemplate,
    Site,
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalars(select(Tenant).where(Tenant.name == "Demo Facility Co")).first():
            print("Seed already applied (tenant exists).")
            return

        t = Tenant(name="Demo Facility Co", status="active", settings_json={})
        db.add(t)
        db.flush()

        admin = User(
            tenant_id=t.id,
            email="admin@demo.com",
            password_hash=hash_password("admin123"),
            full_name="Company Admin",
            role=UserRole.company_admin,
            locale="ar",
            is_platform_admin=False,
        )
        tech = User(
            tenant_id=t.id,
            email="tech@demo.com",
            password_hash=hash_password("tech123"),
            full_name="Technician",
            role=UserRole.technician,
            locale="ar",
        )
        db.add_all([admin, tech])
        db.flush()

        client = Client(tenant_id=t.id, legal_name="Acme Client", code="ACME", billing_email="billing@acme.test")
        db.add(client)
        db.flush()

        site = Site(tenant_id=t.id, client_id=client.id, name="Tower A", timezone="Asia/Riyadh")
        db.add(site)
        db.flush()

        asset = Asset(tenant_id=t.id, site_id=site.id, name="Rooftop HVAC Unit 1", category="hvac")
        db.add(asset)
        db.flush()

        db.add(UserSiteScope(user_id=tech.id, site_id=site.id))

        profile = PricingProfile(
            tenant_id=t.id,
            name="Standard",
            hourly_rate_sar=Decimal("150"),
            parts_markup_percent=Decimal("20"),
            default_service_fee_sar=Decimal("200"),
            emergency_surcharge_percent=Decimal("10"),
        )
        db.add(profile)
        db.flush()

        db.add(
            Contract(
                tenant_id=t.id,
                client_id=client.id,
                pricing_profile_id=profile.id,
                name="MSA 2026",
                currency="SAR",
            )
        )

        db.add(
            Part(tenant_id=t.id, sku="FLT-001", name="Air filter", unit_cost_sar=Decimal("45"))
        )

        schema = {
            "sections": [
                {
                    "id": "sec_1",
                    "title_key": "visual_inspection",
                    "fields": [
                        {
                            "id": "fld_check",
                            "type": "checklist",
                            "label_key": "filters_clean",
                            "options": ["Pass", "Fail", "N/A"],
                            "required": True,
                        },
                        {
                            "id": "labor_log",
                            "type": "labor_log",
                            "label_key": "labor",
                            "required": False,
                        },
                        {
                            "id": "parts_used",
                            "type": "parts_used",
                            "label_key": "parts",
                            "required": False,
                        },
                    ],
                }
            ]
        }
        tmpl = ReportTemplate(
            tenant_id=t.id,
            name="HVAC Inspection",
            code="hvac_insp",
            version=1,
            schema_json=schema,
            maintenance_types=["hvac"],
        )
        db.add(tmpl)
        db.flush()

        wo = WorkOrder(
            tenant_id=t.id,
            client_id=client.id,
            site_id=site.id,
            asset_id=asset.id,
            source=WorkOrderSource.corrective,
            category="hvac",
            title="Quarterly HVAC check",
            description="Inspect filters and log labor",
            template_id=tmpl.id,
            assignee_user_id=tech.id,
            status=WorkOrderStatus.assigned,
            created_by_user_id=admin.id,
        )
        db.add(wo)
        db.commit()
        print("Seed complete.")
        print("  admin@demo.com / admin123")
        print("  tech@demo.com / tech123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
