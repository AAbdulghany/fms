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

class WorkOrderCreate(BaseModel):
    client_id: UUID
    site_id: UUID
    asset_id: UUID
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
    hold_reason: Optional[str] = Field(None, min_length=1, max_length=2000)
    cancellation_reason: Optional[str] = Field(None, min_length=1, max_length=2000)
class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
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
    created_by_user_id: Optional[UUID] = None
    assignee_user_id: Optional[UUID]
    creator: Optional[UserBrief] = None
    assignee: Optional[UserBrief] = None
    company_name: Optional[str] = None
    site_name: Optional[str] = None
    asset_name: Optional[str] = None
    asset_category: Optional[str] = None
    asset_serial: Optional[str] = None
    asset_label_code: Optional[str] = None
    asset_model: Optional[str] = None
    site_address: Optional[str] = None
    site_city: Optional[str] = None
    site_country: Optional[str] = None
    location_name: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime]
    tags: list[str] = []
class AssignBody(BaseModel):
    assignee_user_id: UUID
class DeclineRequestBody(BaseModel):
    reason: str = Field(..., min_length=1, max_length=2000)
class ReportAnswersUpdate(BaseModel):
    answers: dict[str, Any]
    pdf_lang: Optional[str] = None
class MaintenanceReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    template_id: UUID
    template_version: int
    template_snapshot_json: dict[str, Any]
    answers_json: dict[str, Any]
    status: ReportStatus
class ApproveReportBody(BaseModel):
    pass
class RejectReportBody(BaseModel):
    reason: str = ""
class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    user_id: UUID
    user_name: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime


# --- Work Order Documents ---
class DocumentCreate(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_size: int = Field(gt=0)
    file_type: str = Field(min_length=1, max_length=100)
    file_url: str = Field(min_length=1, max_length=512)
    description: Optional[str] = None
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    work_order_id: UUID
    uploaded_by_user_id: UUID
    uploaded_by_name: Optional[str] = None
    file_name: str
    file_size: int
    file_type: str
    file_url: str
    description: Optional[str] = None
    created_at: datetime


from app.schemas.auth import UserBrief  # noqa: E402

WorkOrderOut.model_rebuild()
