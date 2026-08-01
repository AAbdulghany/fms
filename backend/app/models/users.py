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

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        UniqueConstraint("tenant_id", "username", name="uq_user_tenant_username"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id"))
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role", native_enum=False), nullable=False)
    locale: Mapped[str] = mapped_column(String(8), default="ar")
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    site_scopes: Mapped[list["UserSiteScope"]] = relationship(back_populates="user")

class UserSiteScope(Base):
    __tablename__ = "user_site_scopes"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="site_scopes")

