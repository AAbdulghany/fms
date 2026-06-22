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
    site_name: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    timezone: str = Field(default="Asia/Riyadh", min_length=1, max_length=64)
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
    sites_count: int = 0
    active_wo_count: int = 0
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
class ClientSummaryOut(ClientOut):
    """Alias for list view; aggregates already included in ClientOut (NT-P5-B4)."""
    pass
class SiteCreate(BaseModel):
    client_id: UUID
    name: str
    timezone: str = "Asia/Riyadh"
    address_json: dict[str, Any] = Field(default_factory=dict)
class SiteUpdate(BaseModel):
    """Payload for PATCH /sites/{site_id} (NT-P5-S01)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    timezone: Optional[str] = Field(None, max_length=64)
    address: Optional[str] = Field(None, max_length=512)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=32)
class SiteAssignManagerRequest(BaseModel):
    """Payload for POST /sites/{site_id}/assign-manager (NT-P5-S02)."""

    manager_full_name: str = Field(..., min_length=1, max_length=255)
class SiteAssignManagerResponse(BaseModel):
    """Response for POST /sites/{site_id}/assign-manager (NT-P5-S02)."""

    manager_username: str
    manager_email: str
    initial_password: str
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
