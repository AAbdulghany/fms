"""A1 — Vertical and asset-type models (tenant library + platform catalog)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models._base import _utcnow, _uuid


# ---------------------------------------------------------------------------
# Platform tables (no tenant_id; owned by seed code)
# ---------------------------------------------------------------------------


class Vertical(Base):
    """Platform vertical catalog: hospital, hotel, office, …"""

    __tablename__ = "verticals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # back-ref from join table
    template_verticals: Mapped[list["AssetTypeTemplateVertical"]] = relationship(
        back_populates="vertical"
    )
    asset_type_verticals: Mapped[list["AssetTypeVertical"]] = relationship(
        back_populates="vertical"
    )


class AssetTypeTemplate(Base):
    """Platform asset type catalog entry (seed-only in A1)."""

    __tablename__ = "asset_type_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)
    default_max_age_years: Mapped[Optional[int]] = mapped_column(Integer)
    default_max_repair_count: Mapped[Optional[int]] = mapped_column(Integer)
    default_criticality: Mapped[Optional[str]] = mapped_column(String(32))
    default_frequency: Mapped[Optional[str]] = mapped_column(String(32))
    default_report_template_code: Mapped[Optional[str]] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    template_verticals: Mapped[list["AssetTypeTemplateVertical"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class AssetTypeTemplateVertical(Base):
    """Join: asset_type_templates ↔ verticals (platform)."""

    __tablename__ = "asset_type_template_verticals"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset_type_templates.id"), primary_key=True
    )
    vertical_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verticals.id"), primary_key=True
    )

    template: Mapped["AssetTypeTemplate"] = relationship(back_populates="template_verticals")
    vertical: Mapped["Vertical"] = relationship(back_populates="template_verticals")


# ---------------------------------------------------------------------------
# Tenant tables
# ---------------------------------------------------------------------------


class AssetType(Base):
    """Tenant-owned asset type library entry (catalog copy, custom, or legacy)."""

    __tablename__ = "asset_types"

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_asset_type_tenant_code"),
        UniqueConstraint("tenant_id", "source_template_id", name="uq_asset_type_tenant_source"),
        Index("ix_asset_types_tenant_active", "tenant_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name_en: Mapped[str] = mapped_column(String(128), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(128), nullable=False)
    default_max_age_years: Mapped[Optional[int]] = mapped_column(Integer)
    default_max_repair_count: Mapped[Optional[int]] = mapped_column(Integer)
    default_criticality: Mapped[Optional[str]] = mapped_column(String(32))
    default_frequency: Mapped[Optional[str]] = mapped_column(String(32))
    default_report_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("report_templates.id")
    )
    # origin: 'catalog' | 'custom' | 'legacy'
    origin: Mapped[str] = mapped_column(String(16), nullable=False, default="custom")
    source_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asset_type_templates.id"), nullable=True
    )
    source_version: Mapped[Optional[int]] = mapped_column(Integer)
    adopted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    asset_type_verticals: Mapped[list["AssetTypeVertical"]] = relationship(
        back_populates="asset_type", cascade="all, delete-orphan"
    )
    source_template: Mapped[Optional["AssetTypeTemplate"]] = relationship(foreign_keys=[source_template_id])


class AssetTypeVertical(Base):
    """Join: asset_types ↔ verticals (tenant, editable)."""

    __tablename__ = "asset_type_verticals"

    asset_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("asset_types.id", ondelete="CASCADE"),
        primary_key=True,
    )
    vertical_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verticals.id"), primary_key=True
    )

    asset_type: Mapped["AssetType"] = relationship(back_populates="asset_type_verticals")
    vertical: Mapped["Vertical"] = relationship(back_populates="asset_type_verticals")
