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

class NotificationOut(BaseModel):
    id: UUID
    type: str
    title: str
    work_order_id: Optional[UUID] = None
    action: Optional[str] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    created_at: datetime
    read: bool

    @classmethod
    def from_model(cls, row) -> "NotificationOut":
        payload = row.payload_json or {}
        wo_id = payload.get("work_order_id")
        return cls(
            id=row.id,
            type=row.type,
            title=row.title,
            work_order_id=UUID(wo_id) if wo_id else None,
            action=payload.get("action"),
            old_status=payload.get("old_status"),
            new_status=payload.get("new_status"),
            created_at=row.created_at,
            read=row.read_at is not None,
        )
