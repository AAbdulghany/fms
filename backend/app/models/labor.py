from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._base import (
    AssetLifecycleStatus,
    InvoiceStatus,
    ReportStatus,
    Urgency,
    UserRole,
    WorkOrderSource,
    WorkOrderStatus,
    _utcnow,
    _uuid,
)

class TechnicianProfile(Base):
    """P2-F4: Hourly rates and skills for technicians."""

    __tablename__ = "technician_profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tech_profile_tenant_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    hourly_rate_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    overtime_multiplier: Mapped[Any] = mapped_column(Numeric(6, 4), default=1.5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    skills_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class LaborEntry(Base):
    """P2-F4: Logged hours against a work order."""

    __tablename__ = "labor_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_regular: Mapped[Any] = mapped_column(Numeric(8, 2), nullable=False)
    hours_overtime: Mapped[Any] = mapped_column(Numeric(8, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

class TechnicianSchedule(Base):
    """P2-F4: Weekly availability window per technician."""

    __tablename__ = "technician_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "day_of_week", name="uq_tech_schedule_day"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday .. 6=Sunday (ISO-like)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

