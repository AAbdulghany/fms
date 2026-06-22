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

class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    location_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("locations.id"))
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"))
    source: Mapped[WorkOrderSource] = mapped_column(
        Enum(WorkOrderSource, name="work_order_source", native_enum=False), default=WorkOrderSource.corrective
    )
    category: Mapped[str] = mapped_column(String(64), default="general")
    urgency: Mapped[Urgency] = mapped_column(Enum(Urgency, name="urgency", native_enum=False), default=Urgency.normal)
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus, name="work_order_status", native_enum=False), default=WorkOrderStatus.created
    )
    title: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"))
    assignee_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sla_resolution_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # P2-F3: Maintenance Tags
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    creator_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )
    assignee_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assignee_user_id],
    )
    client: Mapped["Client"] = relationship("Client", foreign_keys=[client_id])
    site: Mapped["Site"] = relationship("Site", foreign_keys=[site_id])
    asset: Mapped[Optional["Asset"]] = relationship("Asset", foreign_keys=[asset_id])
    location: Mapped[Optional["Location"]] = relationship("Location", foreign_keys=[location_id])

    report: Mapped[Optional["MaintenanceReport"]] = relationship(
        back_populates="work_order", uselist=False, cascade="all, delete-orphan"
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(back_populates="work_order", uselist=False)
    comments: Mapped[list["Comment"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")
    documents: Mapped[list["WorkOrderDocument"]] = relationship(back_populates="work_order", cascade="all, delete-orphan")

class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), unique=True)
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("report_templates.id"), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    template_snapshot_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    answers_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status", native_enum=False), default=ReportStatus.draft
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="report")

class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="comments")

class WorkOrderDocument(Base):
    __tablename__ = "work_order_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_user_id])
    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="documents")

