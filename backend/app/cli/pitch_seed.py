"""Pitch / demo seed: rich multi-client dataset for sales demos and E2E tests.

Creates:
  - 1 maintenance tenant "Demo Facility Co" with a Pro subscription
  - 2 end clients (Global Enterprises Ltd, Riyadh Retail Group)
  - 3 sites across both clients
  - ~15 assets across categories
  - ~50 work orders spread across all statuses
  - 2 draft invoices on verified WOs
  - Full user roster (super, swdev, admin, client × 2, site, tech)

Canonical: app.cli.pitch_seed (shim at app.pitch_seed).
Run: python -m app.pitch_seed
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.cli._demo_passwords import demo_password
from app.cli._seed_lib import UserSeedSpec, create_seed_user, truncate_tenant_data
from app.models import (
    Asset,
    Client,
    Invoice,
    InvoiceStatus,
    ReportTemplate,
    Site,
    Tenant,
    TenantSubscription,
    Urgency,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.services.billing_setup import ensure_client_active_contract
from app.services.platform_bootstrap import ensure_default_packages, ensure_platform_settings
from app.standard_inspection_report_schema import STANDARD_INSPECTION_SCHEMA

TENANT_NAME = "Demo Facility Co"

_NOW = datetime.now(timezone.utc)


def _ago(**kwargs) -> datetime:
    return _NOW - timedelta(**kwargs)


# ---------------------------------------------------------------------------
# User specs
# ---------------------------------------------------------------------------

SEED_USERS: list[tuple[str, str, UserRole, str]] = [
    ("super@demo.com", "Super Admin", UserRole.super_user, "super"),
    ("swdev@demo.com", "SW Developer", UserRole.sw_dev, "swdev"),
    ("admin@demo.com", "Company Admin", UserRole.company_admin, "admin"),
    ("client@demo.com", "Client Admin GE", UserRole.client_admin, "client"),
    ("client2@demo.com", "Client Admin RR", UserRole.client_admin, "client2"),
    ("site@demo.com", "Site Manager", UserRole.site_manager, "site"),
    ("tech@demo.com", "Field Technician", UserRole.technician, "tech"),
]

_USER_SPECS: list[UserSeedSpec] = [
    UserSeedSpec(
        email="super@demo.com", pw_local="super",
        role=UserRole.super_user, full_name="Super Admin",
        username="superadmin", phone="+966500000001",
        locale="en", is_platform=True,
        metadata_json={"seed_profile": "pitch"},
    ),
    UserSeedSpec(
        email="swdev@demo.com", pw_local="swdev",
        role=UserRole.sw_dev, full_name="SW Developer",
        username="swdev", phone="+966500000002",
        locale="en", is_platform=True,
        metadata_json={"seed_profile": "pitch"},
    ),
    UserSeedSpec(
        email="admin@demo.com", pw_local="admin",
        role=UserRole.company_admin, full_name="Company Admin",
        username="companyadmin", phone="+966500000003",
        locale="ar",
        metadata_json={"seed_profile": "pitch"},
    ),
    # client_id will be patched after clients are flushed
    UserSeedSpec(
        email="client@demo.com", pw_local="client",
        role=UserRole.client_admin, full_name="Client Admin GE",
        username="clientadmin_ge", phone="+966500000004",
        locale="ar",
        metadata_json={"seed_profile": "pitch"},
    ),
    UserSeedSpec(
        email="client2@demo.com", pw_local="client2",
        role=UserRole.client_admin, full_name="Client Admin RR",
        username="clientadmin_rr", phone="+966500000005",
        locale="ar",
        metadata_json={"seed_profile": "pitch"},
    ),
    UserSeedSpec(
        email="site@demo.com", pw_local="site",
        role=UserRole.site_manager, full_name="Site Manager",
        username="sitemanager", phone="+966500000006",
        locale="ar",
        metadata_json={"seed_profile": "pitch"},
    ),
    UserSeedSpec(
        email="tech@demo.com", pw_local="tech",
        role=UserRole.technician, full_name="Field Technician",
        username="technician", phone="+966500000007",
        locale="ar",
        metadata_json={"seed_profile": "pitch"},
    ),
]


# ---------------------------------------------------------------------------
# Main seeder
# ---------------------------------------------------------------------------

def seed_pitch_demo(db: Session) -> dict[str, str | int]:
    """Reset and seed rich pitch demo data. Caller must commit."""
    truncate_tenant_data(db)
    packages = ensure_default_packages(db)
    ensure_platform_settings(db)

    # ---- Tenant ----
    tenant = Tenant(name=TENANT_NAME, status="active", settings_json={})
    db.add(tenant)
    db.flush()
    t_id = tenant.id

    db.add(TenantSubscription(
        tenant_id=t_id,
        package_id=packages["pro"].id,
        status="active",
    ))
    db.flush()

    # ---- Clients ----
    client_ge = Client(
        tenant_id=t_id, legal_name="Global Enterprises Ltd",
        code="GE-001", status="active",
        billing_email="billing@globalent.com",
        activity_type="commercial",
    )
    client_rr = Client(
        tenant_id=t_id, legal_name="Riyadh Retail Group",
        code="RR-002", status="active",
        billing_email="finance@rrgroup.sa",
        activity_type="retail",
    )
    db.add_all([client_ge, client_rr])
    db.flush()

    ensure_client_active_contract(db, t_id, client_ge.id)
    ensure_client_active_contract(db, t_id, client_rr.id)

    # ---- Sites ----
    site_ge_hq = Site(
        tenant_id=t_id, client_id=client_ge.id,
        name="GE Corporate HQ", timezone="Asia/Riyadh",
        address_json={"address": "456 Business Park Ave", "city": "Riyadh", "country": "Saudi Arabia"},
    )
    site_ge_wh = Site(
        tenant_id=t_id, client_id=client_ge.id,
        name="GE Logistics Warehouse", timezone="Asia/Riyadh",
        address_json={"address": "Industrial Zone Block 7", "city": "Jeddah", "country": "Saudi Arabia"},
    )
    site_rr_mall = Site(
        tenant_id=t_id, client_id=client_rr.id,
        name="Riyadh Park Mall", timezone="Asia/Riyadh",
        address_json={"address": "King Fahd Road", "city": "Riyadh", "country": "Saudi Arabia"},
    )
    db.add_all([site_ge_hq, site_ge_wh, site_rr_mall])
    db.flush()

    # ---- Report template ----
    tmpl = ReportTemplate(
        tenant_id=t_id,
        name="Standard Inspection",
        code="STD-INSP",
        schema_json=STANDARD_INSPECTION_SCHEMA,
    )
    db.add(tmpl)
    db.flush()

    # ---- Assets (~15) ----
    assets_data = [
        # GE HQ
        dict(site=site_ge_hq, name="HVAC Central Unit A", category="HVAC", serial="HVAC-GE-001"),
        dict(site=site_ge_hq, name="HVAC Central Unit B", category="HVAC", serial="HVAC-GE-002"),
        dict(site=site_ge_hq, name="Elevator North Tower", category="Elevators", serial="ELV-GE-001"),
        dict(site=site_ge_hq, name="Elevator South Tower", category="Elevators", serial="ELV-GE-002"),
        dict(site=site_ge_hq, name="Fire Suppression System", category="Fire Safety", serial="FIRE-GE-001"),
        dict(site=site_ge_hq, name="Electrical Panel Main", category="Electrical", serial="ELEC-GE-001"),
        # GE Warehouse
        dict(site=site_ge_wh, name="Chiller Unit WH-1", category="HVAC", serial="HVAC-GE-WH-001"),
        dict(site=site_ge_wh, name="Loading Dock Door 1", category="Doors", serial="DOOR-WH-001"),
        dict(site=site_ge_wh, name="Loading Dock Door 2", category="Doors", serial="DOOR-WH-002"),
        dict(site=site_ge_wh, name="Emergency Generator", category="Electrical", serial="GEN-WH-001"),
        # RR Mall
        dict(site=site_rr_mall, name="Escalator Level 1-2", category="Elevators", serial="ESC-RR-001"),
        dict(site=site_rr_mall, name="Escalator Level 2-3", category="Elevators", serial="ESC-RR-002"),
        dict(site=site_rr_mall, name="Rooftop HVAC Array", category="HVAC", serial="HVAC-RR-001"),
        dict(site=site_rr_mall, name="Central Fire Alarm Panel", category="Fire Safety", serial="FIRE-RR-001"),
        dict(site=site_rr_mall, name="Parking Ventilation Fan", category="Ventilation", serial="VENT-RR-001"),
    ]
    assets: list[Asset] = []
    for a in assets_data:
        asset = Asset(
            tenant_id=t_id, site_id=a["site"].id,
            name=a["name"], category=a["category"], serial=a["serial"],
        )
        db.add(asset)
        assets.append(asset)
    db.flush()

    # Convenience groups
    ge_hq_assets = assets[:6]
    ge_wh_assets = assets[6:10]
    rr_assets = assets[10:]

    # ---- Users ----
    users: dict[str, User] = {}
    for spec in _USER_SPECS:
        u = create_seed_user(db, t_id, spec)
        users[spec.email] = u
    db.flush()

    # Wire client_id for client admins
    users["client@demo.com"].client_id = client_ge.id
    users["client2@demo.com"].client_id = client_rr.id
    db.flush()

    # Site scope for site manager (all sites)
    site_mgr = users["site@demo.com"]
    for site in [site_ge_hq, site_ge_wh, site_rr_mall]:
        db.add(UserSiteScope(user_id=site_mgr.id, site_id=site.id))
    db.flush()

    tech = users["tech@demo.com"]

    # ---- Work orders (~50) ----
    # Distribution: created+requested=8, assigned=10, in_progress=8, on_hold=5,
    #               completed+verified=10, closed=5, cancelled=4

    wo_specs = [
        # --- created (4) ---
        dict(title="Quarterly HVAC Filter Check", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[0], status=WorkOrderStatus.created,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             opened_at=_ago(days=3)),
        dict(title="Elevator Annual Safety Cert GE-North", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[2], status=WorkOrderStatus.created,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             opened_at=_ago(days=2)),
        dict(title="Rooftop HVAC Array Inspection", site=site_rr_mall, client=client_rr,
             asset=rr_assets[2], status=WorkOrderStatus.created,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             opened_at=_ago(days=1)),
        dict(title="Fire Alarm Panel Routine Check", site=site_rr_mall, client=client_rr,
             asset=rr_assets[3], status=WorkOrderStatus.created,
             urgency=Urgency.urgent, source=WorkOrderSource.preventive,
             opened_at=_ago(hours=12)),
        # --- requested (4) ---
        dict(title="Loading Dock Door 1 — Sensor Fault", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[1], status=WorkOrderStatus.requested,
             urgency=Urgency.urgent, source=WorkOrderSource.request,
             opened_at=_ago(days=4)),
        dict(title="Parking Fan Noise Complaint", site=site_rr_mall, client=client_rr,
             asset=rr_assets[4], status=WorkOrderStatus.requested,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=5)),
        dict(title="GE-WH Emergency Generator Test Request", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[3], status=WorkOrderStatus.requested,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=6)),
        dict(title="HVAC Unit B Leak Complaint", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[1], status=WorkOrderStatus.requested,
             urgency=Urgency.urgent, source=WorkOrderSource.request,
             opened_at=_ago(days=3)),
        # --- assigned (10) ---
        dict(title="Electrical Panel Thermal Scan", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[5], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=7)),
        dict(title="Escalator Level 1-2 Lubrication", site=site_rr_mall, client=client_rr,
             asset=rr_assets[0], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=8)),
        dict(title="Chiller Unit WH-1 — Belt Replacement", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[0], status=WorkOrderStatus.assigned,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=6)),
        dict(title="Fire Suppression Pressure Test", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[4], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=5)),
        dict(title="Escalator Level 2-3 Safety Inspection", site=site_rr_mall, client=client_rr,
             asset=rr_assets[1], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=9)),
        dict(title="Loading Dock Door 2 — Seal Check", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[2], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=4)),
        dict(title="HVAC Central Unit A — Coil Cleaning", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[0], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=10)),
        dict(title="Elevator South Tower — Controller Reset", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[3], status=WorkOrderStatus.assigned,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=3)),
        dict(title="Central Fire Alarm Panel — Sensor Calibration", site=site_rr_mall, client=client_rr,
             asset=rr_assets[3], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=11)),
        dict(title="GE-WH Gen — Fuel Level Check", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[3], status=WorkOrderStatus.assigned,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=12)),
        # --- in_progress (8) ---
        dict(title="HVAC Refrigerant Recharge HQ", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[1], status=WorkOrderStatus.in_progress,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=14)),
        dict(title="Escalator 1-2 Drive Motor Replacement", site=site_rr_mall, client=client_rr,
             asset=rr_assets[0], status=WorkOrderStatus.in_progress,
             urgency=Urgency.emergency, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=2)),
        dict(title="Fire Suppression System Full Service", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[4], status=WorkOrderStatus.in_progress,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=13)),
        dict(title="Chiller Full Overhaul WH-1", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[0], status=WorkOrderStatus.in_progress,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=15)),
        dict(title="Electrical Panel Main — Breaker Swap", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[5], status=WorkOrderStatus.in_progress,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=7)),
        dict(title="Rooftop HVAC Array Deep Clean", site=site_rr_mall, client=client_rr,
             asset=rr_assets[2], status=WorkOrderStatus.in_progress,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=16)),
        dict(title="Loading Dock Door 1 — Full Mechanism Repair", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[1], status=WorkOrderStatus.in_progress,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=6)),
        dict(title="Parking Ventilation Fan Bearing Replacement", site=site_rr_mall, client=client_rr,
             asset=rr_assets[4], status=WorkOrderStatus.in_progress,
             urgency=Urgency.normal, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=4)),
        # --- on_hold (5) ---
        dict(title="Elevator North — Part on Order", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[2], status=WorkOrderStatus.on_hold,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=20)),
        dict(title="HVAC Unit A — Pending Client Approval", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[0], status=WorkOrderStatus.on_hold,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=18)),
        dict(title="Escalator 2-3 — Awaiting Parts", site=site_rr_mall, client=client_rr,
             asset=rr_assets[1], status=WorkOrderStatus.on_hold,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=22)),
        dict(title="Gen — Major Service Hold", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[3], status=WorkOrderStatus.on_hold,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=25)),
        dict(title="Fire Alarm Panel RR — Circuit Board Recall", site=site_rr_mall, client=client_rr,
             asset=rr_assets[3], status=WorkOrderStatus.on_hold,
             urgency=Urgency.urgent, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=30)),
        # --- completed (5) ---
        dict(title="HVAC Unit B — Scheduled Service", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[1], status=WorkOrderStatus.completed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=35)),
        dict(title="Loading Dock Door 2 — Roller Track Repair", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[2], status=WorkOrderStatus.completed,
             urgency=Urgency.normal, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=40)),
        dict(title="Escalator 1-2 Safety Audit", site=site_rr_mall, client=client_rr,
             asset=rr_assets[0], status=WorkOrderStatus.completed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=28)),
        dict(title="Electrical Panel Surge Suppressor Install", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[5], status=WorkOrderStatus.completed,
             urgency=Urgency.normal, source=WorkOrderSource.corrective,
             assignee=tech, opened_at=_ago(days=5)),
        dict(title="Rooftop HVAC Filter Replacement", site=site_rr_mall, client=client_rr,
             asset=rr_assets[2], status=WorkOrderStatus.completed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=3)),
        # --- verified (5) — eligible for invoicing ---
        dict(title="HVAC Central Unit A — Semi-Annual Service", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[0], status=WorkOrderStatus.verified,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=60)),
        dict(title="Elevator South — Annual Certification", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[3], status=WorkOrderStatus.verified,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=55)),
        dict(title="Chiller WH-1 — Annual Maintenance", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[0], status=WorkOrderStatus.verified,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=50)),
        dict(title="Escalator 2-3 Full Annual Inspection", site=site_rr_mall, client=client_rr,
             asset=rr_assets[1], status=WorkOrderStatus.verified,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=45)),
        dict(title="Fire Suppression Annual Test & Tag", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[4], status=WorkOrderStatus.verified,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=4)),
        # --- closed (5) ---
        dict(title="Elevator North — Annual Cert (prev year)", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[2], status=WorkOrderStatus.closed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=90)),
        dict(title="Rooftop HVAC Full Annual (prev year)", site=site_rr_mall, client=client_rr,
             asset=rr_assets[2], status=WorkOrderStatus.closed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=95)),
        dict(title="Parking Fan Full Service Q1", site=site_rr_mall, client=client_rr,
             asset=rr_assets[4], status=WorkOrderStatus.closed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=100)),
        dict(title="Gen — Annual Fuel System Service", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[3], status=WorkOrderStatus.closed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=80)),
        dict(title="Fire Alarm Full Building Survey", site=site_rr_mall, client=client_rr,
             asset=rr_assets[3], status=WorkOrderStatus.closed,
             urgency=Urgency.normal, source=WorkOrderSource.preventive,
             assignee=tech, opened_at=_ago(days=75)),
        # --- cancelled (4) ---
        dict(title="HVAC Unit B — Upgrade (client cancelled)", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[1], status=WorkOrderStatus.cancelled,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=45)),
        dict(title="Escalator 1-2 — Replacement (budget hold)", site=site_rr_mall, client=client_rr,
             asset=rr_assets[0], status=WorkOrderStatus.cancelled,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=50)),
        dict(title="Loading Dock Door 1 — Duplicate Request", site=site_ge_wh, client=client_ge,
             asset=ge_wh_assets[1], status=WorkOrderStatus.cancelled,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=55)),
        dict(title="Electrical Panel — Scope Change Cancel", site=site_ge_hq, client=client_ge,
             asset=ge_hq_assets[5], status=WorkOrderStatus.cancelled,
             urgency=Urgency.normal, source=WorkOrderSource.request,
             opened_at=_ago(days=60)),
    ]

    work_orders: list[WorkOrder] = []
    for spec in wo_specs:
        wo = WorkOrder(
            tenant_id=t_id,
            client_id=spec["client"].id,
            site_id=spec["site"].id,
            asset_id=spec["asset"].id,
            title=spec["title"],
            status=spec["status"],
            urgency=spec["urgency"],
            source=spec["source"],
            assignee_user_id=spec.get("assignee") and spec["assignee"].id,
            template_id=tmpl.id,
            opened_at=spec["opened_at"],
        )
        db.add(wo)
        work_orders.append(wo)
    db.flush()

    # ---- Draft invoices on the first 2 verified WOs ----
    verified_wos = [w for w in work_orders if w.status == WorkOrderStatus.verified]
    invoice_count = 0
    for i, wo in enumerate(verified_wos[:2]):
        inv = Invoice(
            tenant_id=t_id,
            client_id=wo.client_id,
            work_order_id=wo.id,
            number=f"INV-DEMO-{i + 1:04d}",
            status=InvoiceStatus.draft,
            subtotal_sar=1500,
            tax_sar=225,
            total_sar=1725,
            currency="SAR",
        )
        db.add(inv)
        invoice_count += 1
    db.flush()

    wo_by_status: dict[str, int] = {}
    for wo in work_orders:
        k = wo.status.value
        wo_by_status[k] = wo_by_status.get(k, 0) + 1

    return {
        "tenant_id": str(t_id),
        "users_created": str(len(_USER_SPECS)),
        "clients": 2,
        "sites": 3,
        "assets": len(assets),
        "work_orders": len(work_orders),
        "invoices": invoice_count,
        "wo_by_status": wo_by_status,
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
        print("\nAccounts:")
        for email, _, _, pw_local in SEED_USERS:
            print(f"  {email} / {demo_password(pw_local)}")
