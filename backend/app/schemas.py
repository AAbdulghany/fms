from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    full_name: str
    role: UserRole
    locale: str
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str


class ClientCreate(BaseModel):
    legal_name: str
    code: str = ""
    billing_email: Optional[EmailStr] = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    code: str
    billing_email: Optional[str]


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


class AssetCreate(BaseModel):
    site_id: UUID
    name: str
    category: str = "general"
    parent_asset_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    max_repair_count: Optional[int] = None
    max_age_years: Optional[int] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    location_id: Optional[UUID] = None
    name: str
    category: str
    max_repair_count: Optional[int] = None
    max_age_years: Optional[int] = None
    current_repair_count: int = 0
    lifecycle_status: AssetLifecycleStatus = AssetLifecycleStatus.active


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
    assignee_user_id: Optional[UUID]
    opened_at: datetime
    closed_at: Optional[datetime]
    tags: list[str] = []


class AssignBody(BaseModel):
    assignee_user_id: UUID


class ReportAnswersUpdate(BaseModel):
    answers: dict[str, Any]


class MaintenanceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    template_id: UUID
    template_version: int
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
