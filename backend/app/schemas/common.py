from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.work_orders import WorkOrderOut


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
