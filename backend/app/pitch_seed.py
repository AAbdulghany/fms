"""Pitch-ready demo seed — 1 maintenance tenant, 2 end clients (Wave 2 / NT-113)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Asset,
    Client,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    ReportTemplate,
    Site,
    Tenant,
    TenantSubscription,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
    Urgency,
)
from app.services.asset_labels import generate_label_code, qr_payload_for_asset
from app.services.platform_bootstrap import ensure_default_packages, ensure_platform_settings
from app.standard_inspection_report_schema import STANDARD_INSPECTION_SCHEMA


def _clear_demo_data(db: Session) -> None:
    bind = db.get_bind()
    from sqlalchemy import inspect

    insp = inspect(bind)
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
            Tenant,
            TenantSubscription,
            User,
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
    """Reset and seed pitch demo data. Caller must commit."""
    _clear_demo_data(db)
    packages = ensure_default_packages(db)
    ensure_platform_settings(db)

    tenant = Tenant(name="NexTask Demo Maintenance Co", status="active")
    db.add(tenant)
    db.flush()

    pro = packages["pro"]
    db.add(
        TenantSubscription(
            tenant_id=tenant.id,
            package_id=pro.id,
            status="active",
        )
    )

    clients_data = [
        ("Global Enterprises Ltd", "GE-001", "Main Corporate HQ"),
        ("Riyadh Retail Group", "RRG-002", "Mall Central Branch"),
    ]
    clients: list[Client] = []
    sites: list[Site] = []
    for legal_name, code, site_name in clients_data:
        c = Client(tenant_id=tenant.id, legal_name=legal_name, code=code)
        db.add(c)
        db.flush()
        clients.append(c)
        s = Site(
            tenant_id=tenant.id,
            client_id=c.id,
            name=site_name,
            timezone="Asia/Riyadh",
            address_json={"city": "Riyadh", "country": "Saudi Arabia"},
        )
        db.add(s)
        db.flush()
        sites.append(s)

    tmpl = ReportTemplate(
        tenant_id=tenant.id,
        name="Standard Inspection",
        code="STD-INSP",
        schema_json=STANDARD_INSPECTION_SCHEMA,
    )
    db.add(tmpl)
    db.flush()

    assets: list[Asset] = []
    for i, site in enumerate(sites):
        for j, (name, cat) in enumerate([("HVAC Unit", "HVAC"), ("Elevator", "LIFT")]):
            label = generate_label_code(db, tenant_id=tenant.id, site_id=site.id, category=cat)
            a = Asset(
                tenant_id=tenant.id,
                site_id=site.id,
                name=f"{name} {j + 1} — {clients[i].code}",
                category=cat,
                serial=f"{cat}-{i}{j}",
                label_code=label,
            )
            db.add(a)
            db.flush()
            a.qr_payload = qr_payload_for_asset(a.id)
            assets.append(a)

    users_data = [
        ("super@demo.com", "super123", UserRole.super_user, True, None, None),
        ("swdev@demo.com", "swdev123", UserRole.sw_dev, True, None, None),
        ("admin@demo.com", "admin123", UserRole.company_admin, False, None, None),
        ("client@demo.com", "client123", UserRole.client_admin, False, clients[0].id, None),
        ("client2@demo.com", "client223", UserRole.client_admin, False, clients[1].id, None),
        ("site@demo.com", "site123", UserRole.site_manager, False, None, sites[0].id),
        ("tech@demo.com", "tech123", UserRole.technician, False, None, None),
    ]
    for email, pwd, role, is_platform, client_id, site_id in users_data:
        u = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(pwd),
            role=role,
            is_platform_admin=is_platform,
            client_id=client_id,
            is_active=True,
        )
        db.add(u)
        db.flush()
        if role == UserRole.site_manager and site_id:
            db.add(UserSiteScope(user_id=u.id, site_id=site_id))

    for i, asset in enumerate(assets[:3]):
        wo = WorkOrder(
            tenant_id=tenant.id,
            client_id=clients[i % 2].id,
            site_id=asset.site_id,
            asset_id=asset.id,
            title=f"Scheduled maintenance — {asset.name}",
            urgency=Urgency.normal,
            status=WorkOrderStatus.created,
            source=WorkOrderSource.preventive,
            template_id=tmpl.id,
        )
        db.add(wo)
        db.flush()
        if i < 2:
            inv = Invoice(
                tenant_id=tenant.id,
                client_id=wo.client_id,
                work_order_id=wo.id,
                number=f"INV-DEMO-{i + 1:03d}",
                status=InvoiceStatus.draft,
                subtotal_sar=Decimal("500.00"),
                tax_sar=Decimal("75.00"),
                total_sar=Decimal("575.00"),
            )
            db.add(inv)
            db.flush()
            db.add(
                InvoiceLineItem(
                    invoice_id=inv.id,
                    line_type="labor",
                    description="Preventive maintenance labor",
                    quantity=Decimal("2"),
                    unit_price_sar=Decimal("250.00"),
                    amount_sar=Decimal("500.00"),
                )
            )

    db.flush()
    inv_count = len(db.scalars(select(Invoice).where(Invoice.tenant_id == tenant.id)).all())
    return {
        "tenant_id": str(tenant.id),
        "clients": str(len(clients)),
        "assets": str(len(assets)),
        "invoices": str(inv_count),
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
        print("Pitch demo seeded:", info)
