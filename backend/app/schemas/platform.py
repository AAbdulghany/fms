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
