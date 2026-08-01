"""Shared utilities for seed scripts (test_seed + pitch_seed).

Provides:
  - truncate_tenant_data(db)  — idempotent wipe of all tenant tables
  - UserSeedSpec dataclass     — typed spec for a single user
  - create_seed_user(db, ...)  — insert one user from a spec
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import text, inspect as sa_inspect

from app.models import User, UserRole, UserSiteScope
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

_TRUNCATE_PG = (
    "TRUNCATE TABLE "
    "audit_logs, notifications, "
    "invoice_line_items, invoices, "
    "labor_entries, "
    "comments, work_order_documents, "
    "maintenance_reports, work_orders, "
    "maintenance_schedules, "
    "assets, locations, "
    "user_site_scopes, "
    "technician_schedules, technician_profiles, "
    "contracts, pricing_profiles, parts_catalog, "
    "report_templates, "
    "sites, clients, "
    "users, "
    "tenant_subscriptions, tenants "
    "CASCADE"
)


def truncate_tenant_data(db: Session) -> None:
    """Wipe all tenant-scoped tables so re-seeding is idempotent.

    Uses TRUNCATE CASCADE on PostgreSQL; falls back to ORM-level bulk deletes
    on SQLite (used in pytest fixtures) which respect FK order automatically.
    """
    bind = db.get_bind()
    insp = sa_inspect(bind)
    if not insp.has_table("tenants"):
        return

    if bind.dialect.name == "postgresql":
        db.execute(text(_TRUNCATE_PG))
    else:
        from app.models import (
            AuditLog,
            Asset,
            Client,
            Contract,
            Invoice,
            InvoiceLineItem,
            LaborEntry,
            Location,
            MaintenanceReport,
            MaintenanceSchedule,
            Notification,
            Part,
            PricingProfile,
            ReportTemplate,
            Site,
            TechnicianProfile,
            TechnicianSchedule,
            Tenant,
            TenantSubscription,
            UserSiteScope,
            WorkOrder,
            WorkOrderDocument,
            Comment,
        )
        # Delete in child→parent order to satisfy FK constraints.
        # SQLAlchemy ORM delete() properly tracks deletions in the session
        # identity map, preventing ghost re-insertions on flush().
        for model in (
            AuditLog,
            Notification,
            InvoiceLineItem,
            Invoice,
            LaborEntry,
            Comment,
            WorkOrderDocument,
            MaintenanceReport,
            WorkOrder,
            MaintenanceSchedule,
            TechnicianSchedule,
            TechnicianProfile,
            Asset,
            Location,
            UserSiteScope,
            Contract,
            PricingProfile,
            Part,
            ReportTemplate,
            Site,
            User,
            TenantSubscription,
            Client,
            Tenant,
        ):
            db.query(model).delete()
        db.flush()
        return

    db.flush()


# ---------------------------------------------------------------------------
# User seed helper
# ---------------------------------------------------------------------------

@dataclass
class UserSeedSpec:
    email: str
    pw_local: str          # local part used with demo_password()
    role: UserRole
    full_name: str = ""
    username: Optional[str] = None
    phone: Optional[str] = None
    locale: str = "ar"
    is_platform: bool = False
    client_id: Optional[UUID] = None
    metadata_json: dict[str, Any] = field(default_factory=dict)


def create_seed_user(
    db: Session,
    tenant_id: UUID,
    spec: UserSeedSpec,
    password_hash: Optional[str] = None,
) -> User:
    """Insert a User from a UserSeedSpec. Caller must flush/commit.

    If *password_hash* is not provided the hash is derived via
    ``app.cli._demo_passwords.demo_password(spec.pw_local)``.
    """
    if password_hash is None:
        from app.cli._demo_passwords import demo_password
        password_hash = hash_password(demo_password(spec.pw_local))

    user = User(
        tenant_id=tenant_id,
        email=spec.email,
        password_hash=password_hash,
        full_name=spec.full_name or spec.email.split("@")[0].capitalize(),
        username=spec.username,
        phone=spec.phone,
        role=spec.role,
        locale=spec.locale,
        is_active=True,
        is_platform_admin=spec.is_platform,
        client_id=spec.client_id,
        metadata_json=spec.metadata_json,
    )
    db.add(user)
    return user
