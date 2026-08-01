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

class DashboardSummaryOut(BaseModel):
    role: str
    clients_count: Optional[int] = None
    sites_count: Optional[int] = None
    assets_count: Optional[int] = None
    open_work_orders: int = 0
    operational_users_count: Optional[int] = None
    pending_invoices_draft: Optional[int] = None
    my_assigned_open: Optional[int] = None
    my_in_progress: Optional[int] = None
    completed_this_week: int = 0
    assets_at_eol: Optional[int] = None


# --- Comments ---
