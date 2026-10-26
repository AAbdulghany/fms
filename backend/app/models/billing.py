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
    Index,
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

class PricingProfile(Base):
    __tablename__ = "pricing_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hourly_rate_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    parts_markup_percent: Mapped[Any] = mapped_column(Numeric(6, 2), default=0)
    default_service_fee_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    emergency_surcharge_percent: Mapped[Any] = mapped_column(Numeric(6, 2), default=0)

class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    pricing_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pricing_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), default="Default")
    effective_from: Mapped[Optional[date]] = mapped_column(Date)
    effective_to: Mapped[Optional[date]] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(8), default="SAR")
    status: Mapped[str] = mapped_column(String(32), default="active")
    # Per-client tax override (Commercial Terms) — null → tenant default TaxProfile
    tax_rate_percent: Mapped[Optional[Any]] = mapped_column(Numeric(6, 3), nullable=True)
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=False)

    client: Mapped["Client"] = relationship(back_populates="contracts")

class Part(Base):
    __tablename__ = "parts_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")  # legacy / display fallback
    name_en: Mapped[str] = mapped_column(String(255), default="")
    name_ar: Mapped[str] = mapped_column(String(255), default="")  # Egyptian Arabic preferred
    unit_cost_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)
    # Inventory: spare part for repairs vs raw material consumed by assets
    kind: Mapped[str] = mapped_column(String(32), default="part")  # part | raw_material
    qty_on_hand: Mapped[Any] = mapped_column(Numeric(14, 4), default=0)

    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_part_tenant_sku"),)

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("work_orders.id"), unique=True)
    contract_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status", native_enum=False), default=InvoiceStatus.draft
    )
    subtotal_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    tax_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    total_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    currency: Mapped[str] = mapped_column(String(8), default="SAR")
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    work_order: Mapped["WorkOrder"] = relationship(back_populates="invoice")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "number", name="uq_invoice_tenant_number"),
        Index("ix_invoices_tenant_status", "tenant_id", "status"),
        Index("ix_invoices_tenant_issued", "tenant_id", "issued_at"),
        Index("ix_invoices_tenant_client", "tenant_id", "client_id"),
    )


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    line_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="")
    quantity: Mapped[Any] = mapped_column(Numeric(14, 4), default=1)
    unit_price_sar: Mapped[Any] = mapped_column(Numeric(14, 4), default=0)
    amount_sar: Mapped[Any] = mapped_column(Numeric(14, 2), default=0)
    source_ref: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    invoice: Mapped["Invoice"] = relationship(back_populates="line_items")


class TaxProfile(Base):
    """Per-tenant VAT / tax policy (AgDR-A3)."""

    __tablename__ = "tax_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Standard VAT")
    rate_percent: Mapped[Any] = mapped_column(Numeric(6, 3), default=15)
    tax_inclusive: Mapped[bool] = mapped_column(Boolean, default=False)
    rounding: Mapped[str] = mapped_column(String(16), default="HALF_UP")
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkOrderPart(Base):
    """Catalog part consumption on a work order (A3)."""

    __tablename__ = "work_order_parts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_orders.id"), nullable=False
    )
    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parts_catalog.id"), nullable=False
    )
    quantity: Mapped[Any] = mapped_column(Numeric(14, 4), default=1)
    unit_cost_sar: Mapped[Any] = mapped_column(Numeric(12, 2), default=0)

