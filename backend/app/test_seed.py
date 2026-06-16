import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (
    Tenant, User, Client, Site, Asset, 
    UserRole, ReportTemplate, WorkOrder, 
    WorkOrderStatus, Urgency, WorkOrderSource
)
from app.core.security import hash_password
from app.standard_inspection_report_schema import STANDARD_INSPECTION_SCHEMA

def seed_data():
    db = SessionLocal()
    try:
        print("Cleaning old data...")
        # Clear tables in order of dependency
        db.execute(text("TRUNCATE TABLE audit_logs, invoice_line_items, invoices, maintenance_reports, work_orders, maintenance_schedules, assets, sites, clients, users, tenants CASCADE"))

        # 1. Create Tenant
        tenant = Tenant(name="NexTask Demo Co", status="active")
        db.add(tenant)
        db.flush()
        t_id = tenant.id
        print(f"Created Tenant: {tenant.name} ({t_id})")

        # 2. Create Client and Site
        client = Client(tenant_id=t_id, legal_name="Global Enterprises Ltd", code="GE-001")
        db.add(client)
        db.flush()
        
        site = Site(
            tenant_id=t_id,
            client_id=client.id,
            name="Main Corporate HQ",
            timezone="Asia/Riyadh",
            address_json={
                "address": "456 Business Park Avenue",
                "city": "Jeddah",
                "country": "Saudi Arabia"
            }
        )
        db.add(site)
        db.flush()
        print(f"Created Client {client.legal_name} and Site {site.name}")

        # 3. Create Assets
        asset1 = Asset(tenant_id=t_id, site_id=site.id, name="HVAC Unit 01", category="HVAC", serial="HVAC-123")
        asset2 = Asset(tenant_id=t_id, site_id=site.id, name="Elevator North", category="Elevators", serial="ELV-999")
        db.add_all([asset1, asset2])
        db.flush()

        # 4. Create a Report Template
        tmpl = ReportTemplate(
            tenant_id=t_id,
            name="Standard Inspection",
            code="STD-INSP",
            schema_json=STANDARD_INSPECTION_SCHEMA,
        )
        db.add(tmpl)
        db.flush()

        # 5. Create Test Users (passwords match LoginPage + app.seed docs)
        users_data = [
            {"email": "super@demo.com", "password": "super123", "role": UserRole.super_user, "is_platform": True},
            {"email": "swdev@demo.com", "password": "swdev123", "role": UserRole.sw_dev, "is_platform": True},
            {"email": "admin@demo.com", "password": "admin123", "role": UserRole.company_admin, "is_platform": False},
            {"email": "client@demo.com", "password": "client123", "role": UserRole.client_admin, "is_platform": False, "client_id": client.id},
            {"email": "site@demo.com", "password": "site123", "role": UserRole.site_manager, "is_platform": False},
            {"email": "tech@demo.com", "password": "tech123", "role": UserRole.technician, "is_platform": False},
            {"email": "manager@demo.com", "password": "manager123", "role": UserRole.manager, "is_platform": False},
        ]

        for u_data in users_data:
            user = User(
                tenant_id=t_id,
                email=u_data["email"],
                password_hash=hash_password(u_data["password"]),
                role=u_data["role"],
                is_platform_admin=u_data.get("is_platform", False),
                client_id=u_data.get("client_id"),
                is_active=True
            )
            db.add(user)
            # If site manager, give them access to the site
            if u_data["role"] == UserRole.site_manager:
                from app.models import UserSiteScope
                scope = UserSiteScope(user_id=user.id, site_id=site.id) # This is tricky because user.id isn't set yet
                # We'll handle scopes after all users are flushed
        
        db.flush()

        # Fix Site Manager Scope
        site_mgr = db.scalar(select(User).where(User.email == "site@demo.com"))
        from app.models import UserSiteScope
        db.add(UserSiteScope(user_id=site_mgr.id, site_id=site.id))

        # 6. Create a few Initial Work Orders
        wo1 = WorkOrder(
            tenant_id=t_id, client_id=client.id, site_id=site.id, asset_id=asset1.id,
            title="Quarterly HVAC Check", urgency=Urgency.normal, 
            status=WorkOrderStatus.created, source=WorkOrderSource.preventive,
            template_id=tmpl.id
        )
        wo2 = WorkOrder(
            tenant_id=t_id, client_id=client.id, site_id=site.id, asset_id=asset2.id,
            title="Elevator Emergency Stop failure", urgency=Urgency.emergency, 
            status=WorkOrderStatus.assigned, source=WorkOrderSource.corrective,
            template_id=tmpl.id
        )
        db.add_all([wo1, wo2])

        db.commit()
        print("\\n--- TEST USERS READY ---")
        for u in users_data:
            print(f"  {u['email']} / {u['password']} ({u['role'].value})")
        print("------------------------")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
