import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    company_admin = "company_admin"
    client_admin = "client_admin"
    site_manager = "site_manager"
    technician = "technician"
    manager = "manager"


class WorkOrderStatus(str, enum.Enum):
    requested = "requested"
    declined = "declined"
    created = "created"
    assigned = "assigned"
    in_progress = "in_progress"
    on_hold = "on_hold"
    completed = "completed"
    verified = "verified"
    cancelled = "cancelled"
    closed = "closed"


class WorkOrderSource(str, enum.Enum):
    preventive = "preventive"
    corrective = "corrective"
    request = "request"


class Urgency(str, enum.Enum):
    normal = "normal"
    urgent = "urgent"
    emergency = "emergency"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"
    paid = "paid"
    void = "void"


class AssetLifecycleStatus(str, enum.Enum):
    active = "active"
    warning = "warning"
    end_of_life = "end_of_life"
    replaced = "replaced"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    users: Mapped[list["User"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=False), nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="ar")
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    site_scopes: Mapped[list["UserSiteScope"]] = relationship(back_populates="user")


class UserSiteScope(Base):
    __tablename__ = "user_site_scopes"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="site_scopes")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")
    billing_email: Mapped[Optional[str]] = mapped_column(String(320))
    activity_type: Mapped[Optional[str]] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    sites: Mapped[list["Site"]] = relationship(back_populates="client")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="client")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Riyadh")
    address_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="active")

    client: Mapped["Client"] = relationship(back_populates="sites")
    assets: Mapped[list["Asset"]] = relationship(back_populates="site")
    locations: Mapped[list["Location"]] = relationship(back_populates="site")


class Location(Base):
    """P2-F5: Hierarchical physical locations under a site (Region → Building → … → Room)."""

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[str] = mapped_column(String(32), default="other")  # region, building, floor, zone, room, other
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    site: Mapped["Site"] = relationship(back_populates="locations")
    parent: Mapped[Optional["Location"]] = relationship(
        remote_side="Location.id",
        back_populates="children",
    )
    children: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="parent",
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    parent_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")
    model: Mapped[Optional[str]] = mapped_column(String(255))
    serial: Mapped[Optional[str]] = mapped_column(String(255))
    installed_on: Mapped[Optional[date]] = mapped_column(Date)
    warranty_until: Mapped[Optional[date]] = mapped_column(Date)
    qr_payload: Mapped[Optional[str]] = mapped_column(String(512))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # P2-F2: Asset Lifecycle Management
    max_repair_count: Mapped[Optional[int]] = mapped_column(Integer)
    max_age_years: Mapped[Optional[int]] = mapped_column(Integer)
    current_repair_count: Mapped[int] = mapped_column(Integer, default=0)
    lifecycle_status: Mapped[AssetLifecycleStatus] = mapped_column(
        Enum(AssetLifecycleStatus, name="asset_lifecycle_status", native_enum=False), 
        default=AssetLifecycleStatus.active
    )

    site: Mapped["Site"] = relationship(back_populates="assets")
    location: Mapped[Optional["Location"]] = relationship()
    schedules: Mapped[list["MaintenanceSchedule"]] = relationship(back_populates="asset")


class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    
    frequency: Mapped[str] = mapped_column(String(32), nullable=False) # 'daily', 'weekly', 'monthly', 'yearly'
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="schedules")

class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    schema_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    maintenance_types: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    source: Mapped[WorkOrderSource] = mapped_column(
        Enum(WorkOrderSource, name="work_order_source", native_enum=False), default=WorkOrderSource.corrective
    )
    category: Mapped[str] = mapped_column(String(64), default="general")
    urgency: Mapped[Urgency] = mapped_column(Enum(Urgency, name="urgency", native_enum=False), default=Urgency.normal)
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, name="work_order_status", native_enum=False), default=WorkOrderStatus.created
    )
    title: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"))
    assignee_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # P2-F3: Maintenance Tags
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    creator_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )
    assignee_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_user_id],
    )
    client: Mapped["Client"] = relationship("Client", foreign_keys=[client_id])
    site: Mapped["Site"] = relationship("Site", foreign_keys=[site_id])

    report: Mapped[Optional["MaintenanceReport"]] = relationship(
        back_populates="work_order", uselist=False, cascade="all, delete-orphan"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="work_order", uselist=False)
    comments: Mapped[list["Comment"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")
    documents: Mapped[list["WorkOrderDocument"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")


class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), unique=True)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    template_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    answers_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status", native_enum=False), default=ReportStatus.draft
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="report")


class PricingProfile(Base):
    __tablename__ = "pricing_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hourly_rate_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    parts_markup_percent: Mapped[Any] = mapped_column(Numeric(6, 2), default=0)
    default_service_fee_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    emergency_surcharge_percent: Mapped[Any] = mapped_column(Numeric(6, 2), default=0)


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    pricing_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pricing_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), default="Default")
    effective_from: Mapped[Optional[date]] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(8), default="SAR")
    status: Mapped[str] = mapped_column(String(32), default="active")

    client: Mapped["Client"] = relationship(back_populates="contracts")


class Part(Base):
    __tablename__ = "parts_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")
    unit_cost_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)

    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_part_tenant_sku"),)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), unique=True)
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status", native_enum=False), default=InvoiceStatus.draft
    )
    subtotal_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    tax_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    total_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="SAR")
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="invoice")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("tenant_id", "number", name="uq_invoice_tenant_number"),)


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    line_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="")
    quantity: Mapped[Any] = mapped_column(Numeric(14, 4), default=1)
    unit_price_sar: Mapped[Any] = mapped_column(Numeric(14, 4), default=0)
    amount_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    source_ref: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    invoice: Mapped["Invoice"] = relationship(back_populates="line_items")


class TechnicianProfile(Base):
    """P2-F4: Hourly rates and skills for technicians."""

    __tablename__ = "technician_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tech_profile_tenant_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    hourly_rate_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    overtime_multiplier: Mapped[Any] = mapped_column(Numeric(6, 4), default=1.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    skills_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class LaborEntry(Base):
    """P2-F4: Logged hours against a work order."""

    __tablename__ = "labor_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_regular: Mapped[Any] = mapped_column(Numeric(8, 2), nullable=False)
    hours_overtime: Mapped[Any] = mapped_column(Numeric(8, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TechnicianSchedule(Base):
    """P2-F4: Weekly availability window per technician."""

    __tablename__ = "technician_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "day_of_week", name="uq_tech_schedule_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday (ISO-like)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="comments")


class WorkOrderDocument(Base):
    __tablename__ = "work_order_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_user_id])
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="documents")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64))
    before_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    after_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    actor_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[actor_user_id])
