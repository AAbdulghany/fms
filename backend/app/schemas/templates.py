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
class ObservationFieldDef(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    type: str = Field(default="textarea")
    label: str = Field(min_length=1, max_length=255)
    options: list[str] = Field(default_factory=list)
    required: bool = False
    rows: int = 4
class CategoryObservationsOut(BaseModel):
    categories: dict[str, list[ObservationFieldDef]]
class CategoryObservationsUpdate(BaseModel):
    fields: list[ObservationFieldDef]
class TemplateSyncResult(BaseModel):
    created: int = 0
    updated: int = 0
    unchanged: int = 0
