from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import (
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
    model: Optional[str] = None
    serial: Optional[str] = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    site_id: UUID
    name: str
    category: str


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
    source: WorkOrderSource = WorkOrderSource.corrective
    category: str = "general"
    urgency: Urgency = Urgency.normal
    title: str = ""
    description: str = ""
    template_id: Optional[UUID] = None


class WorkOrderUpdate(BaseModel):
    status: Optional[WorkOrderStatus] = None
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[Urgency] = None
    template_id: Optional[UUID] = None
    assignee_user_id: Optional[UUID] = None


class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    site_id: UUID
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
