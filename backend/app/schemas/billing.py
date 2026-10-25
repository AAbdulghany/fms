from __future__ import annotations

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
    issued_at: Optional[datetime] = None
    billing_email: Optional[str] = None
    notes: str = ""
    work_order_title: str = ""
    client_name: Optional[str] = None
    labor_hours: Decimal = Decimal("0")
    labor_rate_sar: Decimal = Decimal("0")
    labor_amount_sar: Decimal = Decimal("0")
    service_fee_sar: Decimal = Decimal("0")
    line_items: list[InvoiceLineOut] = []
class GenerateInvoiceBody(BaseModel):
    """Optional currency when generating invoice from work order (Phase 3)."""

    currency: Optional[str] = None  # EGP, SAR, USD, EUR
class InvoicePreviewOut(BaseModel):
    work_order_id: UUID
    work_order_title: str
    client_name: str
    site_name: str
    technician_name: Optional[str] = None
    completion_date: Optional[date] = None
    currency: str
    labor_hours: Decimal
    labor_rate_sar: Decimal = Decimal("0")
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
class InvoicePatchBody(BaseModel):
    due_date: Optional[date] = None
    issued_at: Optional[date] = None
    currency: Optional[str] = None
    billing_email: Optional[str] = None
    notes: Optional[str] = None
    work_order_title: Optional[str] = None
    labor_hours: Optional[Decimal] = None
    labor_rate_sar: Optional[Decimal] = None
    service_fee_sar: Optional[Decimal] = None
class PartCreate(BaseModel):
    sku: str
    name: str = ""
    name_en: str = ""
    name_ar: str = ""
    unit_cost_sar: Decimal = Decimal("0")
    kind: str = "part"  # part | raw_material
    qty_on_hand: Decimal = Decimal("0")

    @model_validator(mode="after")
    def _fill_localized_names(self) -> "PartCreate":
        en = (self.name_en or self.name or "").strip()
        ar = (self.name_ar or self.name or "").strip()
        self.name_en = en
        self.name_ar = ar
        if not self.name:
            self.name = en or ar
        k = (self.kind or "part").strip().lower().replace("-", "_").replace(" ", "_")
        if k in ("raw", "raw_material", "material"):
            self.kind = "raw_material"
        elif k in ("spare_asset", "spare", "asset", "whole_asset"):
            self.kind = "spare_asset"
        else:
            self.kind = "part"
        return self


class PartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    name: str
    name_en: str = ""
    name_ar: str = ""
    unit_cost_sar: Decimal
    kind: str = "part"
    qty_on_hand: Decimal = Decimal("0")


class PartUpdate(BaseModel):
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    unit_cost_sar: Optional[Decimal] = None
    kind: Optional[str] = None
    qty_on_hand: Optional[Decimal] = None


class PartBulkItem(BaseModel):
    sku: str
    name_en: str = ""
    name_ar: str = ""
    name: str = ""
    unit_cost_sar: Decimal = Decimal("0")
    kind: str = "part"
    qty_on_hand: Decimal = Decimal("0")


class PartBulkRequest(BaseModel):
    items: list[PartBulkItem] = Field(default_factory=list, min_length=1)


class PartBulkResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = Field(default_factory=list)
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
    tax_rate_percent: Optional[Decimal] = None
    tax_inclusive: bool = False


class ContractUpdate(BaseModel):
    pricing_profile_id: Optional[UUID] = None
    name: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    tax_rate_percent: Optional[Decimal] = None
    tax_inclusive: Optional[bool] = None


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    pricing_profile_id: UUID
    name: str
    currency: str
    status: str
    tax_rate_percent: Optional[Decimal] = None
    tax_inclusive: bool = False


class TaxProfileCreate(BaseModel):
    name: str = "Standard VAT"
    rate_percent: Decimal = Decimal("15")
    tax_inclusive: bool = False
    rounding: str = "HALF_UP"
    is_default: bool = True


class TaxProfileUpdate(BaseModel):
    name: Optional[str] = None
    rate_percent: Optional[Decimal] = None
    tax_inclusive: Optional[bool] = None
    rounding: Optional[str] = None
    is_default: Optional[bool] = None


class TaxProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    rate_percent: Decimal
    tax_inclusive: bool
    rounding: str
    is_default: bool


class WorkOrderPartCreate(BaseModel):
    part_id: UUID
    quantity: Decimal = Decimal("1")


class WorkOrderPartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    part_id: UUID
    quantity: Decimal
    unit_cost_sar: Decimal
    part_sku: Optional[str] = None
    part_name: Optional[str] = None
