import enum
import uuid
from datetime import date, datetime, timezone
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


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    super_user = "super_user"
    sw_dev = "sw_dev"
    super_admin = "super_admin"  # legacy; platform staff migrate to super_user
    company_admin = "company_admin"
    company_engineer = "company_engineer"
    client_admin = "client_admin"
    site_manager = "site_manager"
    technician = "technician"
    manager = "manager"


class WorkOrderStatus(str, enum.Enum):
    requested = "requested"
    declined = "declined"
    created = "created"
    assigned = "assigned"
    in_progress = "in_progress"
    on_hold = "on_hold"
    completed = "completed"
    verified = "verified"
    cancelled = "cancelled"
    closed = "closed"


class WorkOrderSource(str, enum.Enum):
    preventive = "preventive"
    corrective = "corrective"
    request = "request"


class Urgency(str, enum.Enum):
    normal = "normal"
    urgent = "urgent"
    emergency = "emergency"


class ReportStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"
    paid = "paid"
    void = "void"


class AssetLifecycleStatus(str, enum.Enum):
    active = "active"
    warning = "warning"
    end_of_life = "end_of_life"
    replaced = "replaced"



