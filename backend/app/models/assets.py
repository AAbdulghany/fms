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

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    parent_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="general")
    model: Mapped[Optional[str]] = mapped_column(String(255))
    serial: Mapped[Optional[str]] = mapped_column(String(255))
    installed_on: Mapped[Optional[date]] = mapped_column(Date)
    warranty_until: Mapped[Optional[date]] = mapped_column(Date)
    qr_payload: Mapped[Optional[str]] = mapped_column(String(512))
    label_code: Mapped[Optional[str]] = mapped_column(String(64))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    # P2-F2: Asset Lifecycle Management
    max_repair_count: Mapped[Optional[int]] = mapped_column(Integer)
    max_age_years: Mapped[Optional[int]] = mapped_column(Integer)
    current_repair_count: Mapped[int] = mapped_column(Integer, default=0)
    lifecycle_status: Mapped[AssetLifecycleStatus] = mapped_column(
        Enum(AssetLifecycleStatus, name="asset_lifecycle_status", native_enum=False), 
        default=AssetLifecycleStatus.active
    )

    site: Mapped["Site"] = relationship(back_populates="assets")
    location: Mapped[Optional["Location"]] = relationship()
    schedules: Mapped[list["MaintenanceSchedule"]] = relationship(back_populates="asset")

class MaintenanceSchedule(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    
    frequency: Mapped[str] = mapped_column(String(32), nullable=False) # 'daily', 'weekly', 'monthly', 'yearly'
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_meta_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    asset: Mapped["Asset"] = relationship(back_populates="schedules")
