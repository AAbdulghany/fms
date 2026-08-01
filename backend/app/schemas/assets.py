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

class MaintenanceScheduleCreate(BaseModel):
    template_id: UUID
    frequency: str = "monthly"
    custom_days: Optional[int] = None
    last_maintenance_date: Optional[date] = None
class MaintenanceScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    template_id: UUID
    frequency: str
    next_due_at: datetime
    is_active: bool
    ai_meta_json: dict[str, Any] = Field(default_factory=dict)
class MaintenanceCalendarEventOut(BaseModel):
    asset_id: UUID
    asset_name: str
    site_id: UUID
    client_id: UUID
    schedule_id: UUID
    frequency: str
    due_at: datetime
    bucket: str
    year: int
    view: str
class AiSchedulingStubOut(BaseModel):
    status: str = "not_implemented"
    message: str = "AI scheduling is a future-phase placeholder."
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
    floor: Optional[str] = Field(None, max_length=64)
    room: Optional[str] = Field(None, max_length=64)
    smart_labels: list[str] = Field(default_factory=list)
    criticality: Optional[str] = Field(None, max_length=32)
    last_maintenance_date: Optional[date] = None
    is_spare: bool = False
    schedule: Optional[MaintenanceScheduleCreate] = None
class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=64)
    model: Optional[str] = None
    serial: Optional[str] = None
    installed_on: Optional[date] = None
    warranty_until: Optional[date] = None
    max_repair_count: Optional[int] = None
    max_age_years: Optional[int] = None
    floor: Optional[str] = Field(None, max_length=64)
    room: Optional[str] = Field(None, max_length=64)
    smart_labels: Optional[list[str]] = None
    criticality: Optional[str] = Field(None, max_length=32)
    last_maintenance_date: Optional[date] = None
    lifecycle_status: Optional[AssetLifecycleStatus] = None
    is_spare: Optional[bool] = None
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
    floor: Optional[str] = None
    room: Optional[str] = None
    smart_labels: list[str] = Field(default_factory=list)
    criticality: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    schedules: list["MaintenanceScheduleOut"] = Field(default_factory=list)
    company_name: Optional[str] = None
    site_name: Optional[str] = None
    expected_eol_date: Optional[date] = None
    is_spare: bool = False
    photo_url: Optional[str] = None
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
