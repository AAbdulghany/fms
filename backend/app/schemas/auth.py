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
    phone: Optional[str] = None
    job_title: Optional[str] = None
    accreditation: Optional[str] = None
class UserMeOut(UserPublic):
    """Authenticated user profile including tenant subscription features."""

    features: list[str] = Field(default_factory=list)
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
    phone: Optional[str] = Field(None, max_length=64)
    job_title: Optional[str] = Field(None, max_length=128)
    accreditation: Optional[str] = Field(None, max_length=128)
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
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=64)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None
    locale: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=64)
    email: Optional[str] = Field(None, max_length=320)
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
