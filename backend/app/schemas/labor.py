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
