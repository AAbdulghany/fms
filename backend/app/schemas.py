from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import (
    AssetLifecycleStatus,
    InvoiceStatus,
    ReportStatus,
    Urgency,
    UserRole,
    WorkOrderSource,
    WorkOrderStatus,
)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: Optional[UUID] = None
    email: str
    username: Optional[str] = None
    full_name: str
    role: UserRole
    locale: str
    is_active: bool
    is_platform_admin: bool = False


class UserListOut(BaseModel):
    """Extended user representation used in list / admin views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: Optional[UUID] = None
    email: str
    username: Optional[str] = None
    full_name: str
    role: UserRole
    locale: str
    status: str = "active"
    last_login_at: Optional[datetime] = None

    @classmethod
    def from_user(cls, user: Any) -> "UserListOut":
        return cls(
            id=user.id,
            tenant_id=user.tenant_id,
            client_id=user.client_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            locale=user.locale,
            status="active" if user.is_active else "inactive",
            last_login_at=user.last_login_at,
        )


class UserPatchMe(BaseModel):
    """Payload for PATCH /users/me. Username is intentionally excluded."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=128)


class UserCreateBody(BaseModel):
    """company_admin or super_admin creating a new user."""

    email: str
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    locale: str = "ar"
    phone: Optional[str] = None
    client_id: Optional[UUID] = None


class UserCreateResponse(BaseModel):
    user: UserPublic
    initial_password: Optional[str] = None


class UserPatchBody(BaseModel):
    """Payload for PATCH /users/{id}."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    locale: Optional[str] = None


class UserBrief(BaseModel):
    """Minimal user info for work order creator/assignee (Phase 3)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: Optional[str] = None
    full_name: str
    role: UserRole


class LoginRequest(BaseModel):
    """Login with username or email (email kept for backward compatibility)."""

    password: str
    identifier: Optional[str] = None
    email: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _merge_identifier(cls, data: object) -> object:
        if isinstance(data, dict):
            ident = data.get("identifier")
            em = data.get("email")
            if ident in (None, "") and em not in (None, ""):
                data["identifier"] = em
        return data


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserPublic
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


class ClientCreate(BaseModel):
    legal_name: str
    code: str = ""
    billing_email: Optional[EmailStr] = None
    activity_type: Optional[str] = Field(None, max_length=64)


class ClientProvisionRequest(BaseModel):
    """Super admin: create company + client admin with generated credentials."""

    legal_name: str = Field(..., min_length=1, max_length=255)
    manager_full_name: str = Field(..., min_length=1, max_length=255)
    activity_type: Optional[str] = Field(None, max_length=64)


class ClientProvisionResponse(BaseModel):
    client: "ClientOut"
    company_id: UUID
    company_code: str
    manager_username: str
    manager_email: str
    initial_password: str


class ClientUpdate(BaseModel):
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=64)


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    code: str
    billing_email: Optional[str]
    status: str = "active"
    activity_type: Optional[str] = None


class SiteCreate(BaseModel):
    client_id: UUID
    name: str
    timezone: str = "Asia/Riyadh"
    address_json: dict[str, Any] = Field(default_factory=dict)


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    name: str
    timezone: str
    status: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    company_name: Optional[str] = None


class SiteProvisionRequest(BaseModel):
    client_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    manager_full_name: str = Field(..., min_length=1, max_length=255)
    timezone: str = "Asia/Riyadh"
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)


class SiteProvisionResponse(BaseModel):
    site: SiteOut
    manager_username: str
    manager_email: str
    initial_password: str


class MaintenanceScheduleCreate(BaseModel):
    template_id: UUID
    frequency: str = "monthly"
    custom_days: Optional[int] = None


class MaintenanceScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    template_id: UUID
    frequency: str
    next_due_at: datetime
    is_active: bool


class AssetCreate(BaseModel):
    site_id: UUID
    name: str
    category: str = "general"
    parent_asset_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    installed_on: Optional[date] = None
    warranty_until: Optional[date] = None
    max_repair_count: Optional[int] = None
    max_age_years: Optional[int] = None
    schedule: Optional[MaintenanceScheduleCreate] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    location_id: Optional[UUID] = None
    name: str
    category: str
    model: Optional[str] = None
    serial: Optional[str] = None
    installed_on: Optional[date] = None
    warranty_until: Optional[date] = None
    max_repair_count: Optional[int] = None
    max_age_years: Optional[int] = None
    current_repair_count: int = 0
    lifecycle_status: AssetLifecycleStatus = AssetLifecycleStatus.active
    label_code: Optional[str] = None
    qr_payload: Optional[str] = None
    next_due_at: Optional[datetime] = None
    schedules: list["MaintenanceScheduleOut"] = Field(default_factory=list)


class ReportTemplateCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    code: str = ""
    definition: dict[str, Any] = Field(validation_alias="schema_json", serialization_alias="schema_json")
    maintenance_types: list[Any] = Field(default_factory=list)


class ReportTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    code: str
    version: int
    definition: dict[str, Any] = Field(validation_alias="schema_json", serialization_alias="schema_json")
    maintenance_types: list[Any]
    is_active: bool


class WorkOrderCreate(BaseModel):
    client_id: UUID
    site_id: UUID
    asset_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    source: WorkOrderSource = WorkOrderSource.corrective
    category: str = "general"
    urgency: Urgency = Urgency.normal
    title: str = ""
    description: str = ""
    template_id: Optional[UUID] = None
    tags: list[str] = Field(default_factory=list)


class WorkOrderUpdate(BaseModel):
    status: Optional[WorkOrderStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[Urgency] = None
    template_id: Optional[UUID] = None
    assignee_user_id: Optional[UUID] = None
    tags: Optional[list[str]] = None


class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    site_id: UUID
    location_id: Optional[UUID] = None
    asset_id: Optional[UUID]
    source: WorkOrderSource
    category: str
    urgency: Urgency
    status: WorkOrderStatus
    title: str
    description: str
    template_id: Optional[UUID]
    created_by_user_id: Optional[UUID] = None
    assignee_user_id: Optional[UUID]
    creator: Optional[UserBrief] = None
    assignee: Optional[UserBrief] = None
    company_name: Optional[str] = None
    site_name: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime]
    tags: list[str] = []


class AssignBody(BaseModel):
    assignee_user_id: UUID


class DeclineRequestBody(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)


class ReportAnswersUpdate(BaseModel):
    answers: dict[str, Any]


class MaintenanceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    template_id: UUID
    template_version: int
    template_snapshot_json: dict[str, Any]
    answers_json: dict[str, Any]
    status: ReportStatus


class ApproveReportBody(BaseModel):
    pass


class RejectReportBody(BaseModel):
    reason: str = ""


class InvoiceLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    line_type: str
    description: str
    quantity: Decimal
    unit_price_sar: Decimal
    amount_sar: Decimal


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    work_order_id: UUID
    number: str
    status: InvoiceStatus
    subtotal_sar: Decimal
    tax_sar: Decimal
    total_sar: Decimal
    currency: str
    due_date: Optional[date]
    line_items: list[InvoiceLineOut] = []


class GenerateInvoiceBody(BaseModel):
    """Optional currency when generating invoice from work order (Phase 3)."""

    currency: Optional[str] = None  # EGP, SAR, USD, EUR


class NotificationOut(BaseModel):
    id: UUID
    type: str
    title: str
    work_order_id: Optional[UUID] = None
    action: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: datetime
    read: bool

    @classmethod
    def from_model(cls, row) -> "NotificationOut":
        payload = row.payload_json or {}
        wo_id = payload.get("work_order_id")
        return cls(
            id=row.id,
            type=row.type,
            title=row.title,
            work_order_id=UUID(wo_id) if wo_id else None,
            action=payload.get("action"),
            old_status=payload.get("old_status"),
            new_status=payload.get("new_status"),
            created_at=row.created_at,
            read=row.read_at is not None,
        )


class InvoicePreviewOut(BaseModel):
    work_order_id: UUID
    work_order_title: str
    client_name: str
    site_name: str
    technician_name: Optional[str] = None
    completion_date: Optional[date] = None
    currency: str
    labor_hours: Decimal
    labor_amount_sar: Decimal
    parts: list[dict[str, Any]] = Field(default_factory=list)
    service_fee_sar: Decimal = Decimal("0")
    emergency_surcharge_sar: Decimal = Decimal("0")
    subtotal_sar: Decimal
    tax_sar: Decimal
    total_sar: Decimal
    work_summary: str = ""


class SendInvoiceBody(BaseModel):
    recipient_email: Optional[str] = None


class AssetImportRow(BaseModel):
    row: int
    site_code: str
    name: str
    category: str = "general"
    serial: Optional[str] = None
    status: str = "ok"
    errors: list[str] = Field(default_factory=list)


class AssetImportPreview(BaseModel):
    valid_count: int
    error_count: int
    rows: list[AssetImportRow]


class SubscriptionOut(BaseModel):
    plan: str = "trial"
    package_id: Optional[UUID] = None
    status: str = "active"
    valid_until: Optional[date] = None
    max_sites: int = 10
    max_users: int = 25
    features: list[str] = Field(default_factory=list)


class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    package_id: Optional[UUID] = None
    status: Optional[str] = None
    valid_until: Optional[date] = None
    max_sites: Optional[int] = None
    max_users: Optional[int] = None
    features: Optional[list[str]] = None


class TenantBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str


class SubscriptionPackageCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    features_json: list[str] = Field(default_factory=list)
    limits_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class SubscriptionPackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    features_json: Optional[list[str]] = None
    limits_json: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class SubscriptionPackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    features_json: list[str] = Field(default_factory=list)
    limits_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool


class TenantLicenseAssign(BaseModel):
    package_id: UUID
    status: str = "active"
    valid_until: Optional[date] = None
    overrides_json: dict[str, Any] = Field(default_factory=dict)


class PlatformClientBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    code: str
    status: str = "active"


class MaintenanceCompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    client_count: int = 0
    clients: list[PlatformClientBrief] = Field(default_factory=list)
    subscription: Optional[SubscriptionOut] = None


class TenantProvisionBody(BaseModel):
    tenant_name: str = Field(..., min_length=1, max_length=255)
    admin_email: EmailStr
    admin_full_name: str = Field(..., min_length=1, max_length=255)
    admin_password: Optional[str] = Field(None, min_length=6)
    package_id: UUID
    license_status: str = "active"
    valid_until: Optional[date] = None


class TenantProvisionOut(BaseModel):
    tenant_id: UUID
    admin_user_id: UUID
    initial_password: Optional[str] = None
    subscription: SubscriptionOut


class PlatformClientCreate(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=64)
    billing_email: Optional[EmailStr] = None
    activity_type: Optional[str] = None


class PlatformUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole
    password: Optional[str] = Field(None, min_length=6)
    client_id: Optional[UUID] = None


class PlatformUserCreateOut(BaseModel):
    user_id: UUID
    initial_password: Optional[str] = None


class PartCreate(BaseModel):
    sku: str
    name: str = ""
    unit_cost_sar: Decimal = Decimal("0")


class PartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    unit_cost_sar: Decimal


class PricingProfileCreate(BaseModel):
    name: str
    hourly_rate_sar: Decimal = Decimal("0")
    parts_markup_percent: Decimal = Decimal("0")
    default_service_fee_sar: Decimal = Decimal("0")
    emergency_surcharge_percent: Decimal = Decimal("0")


class PricingProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    hourly_rate_sar: Decimal
    parts_markup_percent: Decimal
    default_service_fee_sar: Decimal
    emergency_surcharge_percent: Decimal


class ContractCreate(BaseModel):
    client_id: UUID
    pricing_profile_id: UUID
    name: str = "Default"
    currency: str = "SAR"


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    pricing_profile_id: UUID
    name: str
    currency: str
    status: str


class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PaginatedWorkOrders(BaseModel):
    data: list[WorkOrderOut]
    meta: PaginatedMeta


# --- P2-F5 Locations ---
class LocationCreate(BaseModel):
    site_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    location_type: str = "other"
    sort_order: int = 0
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None
    location_type: Optional[str] = None
    sort_order: Optional[int] = None
    metadata_json: Optional[dict[str, Any]] = None


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    parent_id: Optional[UUID]
    name: str
    location_type: str
    sort_order: int


class LocationTreeNode(BaseModel):
    id: UUID
    site_id: UUID
    parent_id: Optional[UUID]
    name: str
    location_type: str
    sort_order: int
    children: list["LocationTreeNode"] = Field(default_factory=list)


LocationTreeNode.model_rebuild()


# --- P2-F4 Labor ---
class TechnicianProfileCreate(BaseModel):
    user_id: UUID
    hourly_rate_sar: Decimal = Decimal("0")
    overtime_multiplier: Decimal = Decimal("1.5")
    is_active: bool = True
    skills_json: dict[str, Any] = Field(default_factory=dict)


class TechnicianProfileUpdate(BaseModel):
    hourly_rate_sar: Optional[Decimal] = None
    overtime_multiplier: Optional[Decimal] = None
    is_active: Optional[bool] = None
    skills_json: Optional[dict[str, Any]] = None


class TechnicianProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    hourly_rate_sar: Decimal
    overtime_multiplier: Decimal
    is_active: bool


class LaborEntryCreate(BaseModel):
    work_order_id: UUID
    user_id: UUID
    work_date: date
    hours_regular: Decimal
    hours_overtime: Decimal = Decimal("0")
    notes: str = ""


class LaborEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    user_id: UUID
    work_date: date
    hours_regular: Decimal
    hours_overtime: Decimal
    notes: str


class TechnicianScheduleCreate(BaseModel):
    user_id: UUID
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = "09:00"
    end_time: str = "17:00"
    is_active: bool = True


class TechnicianScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    day_of_week: int
    start_time: str
    end_time: str
    is_active: bool


# --- P2-F6 Dashboard ---
class DashboardSummaryOut(BaseModel):
    role: str
    clients_count: Optional[int] = None
    sites_count: Optional[int] = None
    assets_count: Optional[int] = None
    open_work_orders: int = 0
    technicians_count: Optional[int] = None
    pending_invoices_draft: Optional[int] = None
    my_assigned_open: Optional[int] = None
    my_in_progress: Optional[int] = None
    completed_this_week: int = 0
    assets_at_eol: Optional[int] = None


# --- Comments ---
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime


# --- Work Order Documents ---
class DocumentCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_size: int = Field(gt=0)
    file_type: str = Field(min_length=1, max_length=100)
    file_url: str = Field(min_length=1, max_length=512)
    description: Optional[str] = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    uploaded_by_user_id: UUID
    uploaded_by_name: Optional[str] = None
    file_name: str
    file_size: int
    file_type: str
    file_url: str
    description: Optional[str] = None
    created_at: datetime


# --- Audit Logs ---
class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    before_json: Optional[dict[str, Any]] = None
    after_json: Optional[dict[str, Any]] = None
    created_at: datetime
