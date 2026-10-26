from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserBrief
from app.schemas.work_orders import (
    CommentOut,
    DocumentOut,
    MaintenanceReportOut,
    WorkOrderOut,
)


class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PaginatedWorkOrders(BaseModel):
    data: list[WorkOrderOut]
    meta: PaginatedMeta


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_user_id: Optional[UUID] = None
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    before_json: Optional[dict[str, Any]] = None
    after_json: Optional[dict[str, Any]] = None
    created_at: datetime


class WorkOrderDetailOut(BaseModel):
    """Single-round-trip payload for the work-order detail page (P9)."""

    work_order: WorkOrderOut
    history: list[AuditLogOut]
    comments: list[CommentOut]
    assignable_users: list[UserBrief]
    documents: list[DocumentOut]
    report: Optional[MaintenanceReportOut] = None
