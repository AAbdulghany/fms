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
