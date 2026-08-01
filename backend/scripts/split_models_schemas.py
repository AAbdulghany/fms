"""One-off Wave 6 split: models.py and schemas.py into domain packages."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def split_models() -> None:
    models_py = (APP / "models.py").read_text(encoding="utf-8")
    (APP / "models").mkdir(exist_ok=True)

    header_end = models_py.index("class Tenant(Base)")
    header = models_py[:header_end]
    (APP / "models" / "_base.py").write_text(header + "\n", encoding="utf-8")

    parts = re.split(r"\n(?=class \w+)", models_py[header_end:])
    chunks: dict[str, str] = {}
    for part in parts:
        m = re.match(r"class (\w+)", part)
        if m:
            chunks[m.group(1)] = part

    groups = {
        "platform.py": ["Tenant", "SubscriptionPackage", "TenantSubscription", "PlatformSettings"],
        "users.py": ["User", "UserSiteScope"],
        "clients.py": ["Client", "Site", "Location"],
        "assets.py": ["Asset", "MaintenanceSchedule"],
        "templates.py": ["ReportTemplate"],
        "work_orders.py": ["WorkOrder", "MaintenanceReport", "Comment", "WorkOrderDocument"],
        "billing.py": ["PricingProfile", "Contract", "Part", "Invoice", "InvoiceLineItem"],
        "labor.py": ["TechnicianProfile", "LaborEntry", "TechnicianSchedule"],
        "notifications.py": ["Notification"],
        "audit.py": ["AuditLog"],
    }

    domain_imports = """from __future__ import annotations

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

"""

    for fname, names in groups.items():
        body = "".join(chunks[n] for n in names if n in chunks)
        (APP / "models" / fname).write_text(domain_imports + body, encoding="utf-8")

    init = '''"""SQLAlchemy ORM models — split by domain (Wave 6)."""

from app.models._base import *  # noqa: F403
from app.models.platform import *  # noqa: F403
from app.models.users import *  # noqa: F403
from app.models.clients import *  # noqa: F403
from app.models.assets import *  # noqa: F403
from app.models.templates import *  # noqa: F403
from app.models.work_orders import *  # noqa: F403
from app.models.billing import *  # noqa: F403
from app.models.labor import *  # noqa: F403
from app.models.notifications import *  # noqa: F403
from app.models.audit import *  # noqa: F403

__all__ = [
    "UserRole", "WorkOrderStatus", "WorkOrderSource", "Urgency", "ReportStatus",
    "InvoiceStatus", "AssetLifecycleStatus",
    "Tenant", "SubscriptionPackage", "TenantSubscription", "PlatformSettings",
    "User", "UserSiteScope", "Client", "Site", "Location",
    "Asset", "MaintenanceSchedule", "ReportTemplate",
    "WorkOrder", "MaintenanceReport", "Comment", "WorkOrderDocument",
    "PricingProfile", "Contract", "Part", "Invoice", "InvoiceLineItem",
    "TechnicianProfile", "LaborEntry", "TechnicianSchedule",
    "Notification", "AuditLog",
]
'''
    (APP / "models" / "__init__.py").write_text(init, encoding="utf-8")
    (APP / "models.py.bak").write_text(models_py, encoding="utf-8")
    (APP / "models.py").unlink()
    print("models split OK")


def split_schemas() -> None:
    schemas_py = (APP / "schemas.py").read_text(encoding="utf-8")
    (APP / "schemas").mkdir(exist_ok=True)

    header = """from __future__ import annotations

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

"""
    body_start = schemas_py.index("class UserPublic")
    class_pattern = re.compile(r"^class (\w+)\(", re.MULTILINE)
    matches = list(class_pattern.finditer(schemas_py, body_start))
    chunks: dict[str, str] = {}
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(schemas_py)
        chunks[match.group(1)] = schemas_py[start:end].rstrip() + "\n"

    groups = {
        "auth.py": [
            "UserPublic", "UserMeOut", "UserListOut", "UserPatchMe", "UserCreateBody",
            "UserCreateResponse", "UserPatchBody", "UserBrief", "LoginRequest",
            "TokenResponse", "RefreshRequest",
        ],
        "clients.py": [
            "ClientCreate", "ClientProvisionRequest", "ClientProvisionResponse", "ClientUpdate",
            "ClientOut", "ClientSummaryOut", "SiteCreate", "SiteUpdate", "SiteAssignManagerRequest",
            "SiteAssignManagerResponse", "SiteOut", "SiteProvisionRequest", "SiteProvisionResponse",
        ],
        "assets.py": [
            "MaintenanceScheduleCreate", "MaintenanceScheduleOut", "MaintenanceCalendarEventOut",
            "AiSchedulingStubOut", "AssetCreate", "AssetUpdate", "AssetOut",
            "AssetImportRow", "AssetImportPreview",
        ],
        "templates.py": [
            "ReportTemplateCreate", "ReportTemplateOut", "ObservationFieldDef",
            "CategoryObservationsOut", "CategoryObservationsUpdate", "TemplateSyncResult",
        ],
        "work_orders.py": [
            "WorkOrderCreate", "WorkOrderUpdate", "WorkOrderOut", "AssignBody", "DeclineRequestBody",
            "ReportAnswersUpdate", "MaintenanceReportOut", "ApproveReportBody", "RejectReportBody",
            "CommentCreate", "CommentOut", "DocumentCreate", "DocumentOut",
        ],
        "billing.py": [
            "InvoiceLineOut", "InvoiceOut", "GenerateInvoiceBody", "InvoicePreviewOut",
            "SendInvoiceBody", "InvoicePatchBody", "PartCreate", "PartOut",
            "PricingProfileCreate", "PricingProfileOut", "ContractCreate", "ContractOut",
        ],
        "notifications.py": ["NotificationOut"],
        "platform.py": [
            "SubscriptionOut", "SubscriptionUpdate", "TenantBriefOut", "SubscriptionPackageCreate",
            "SubscriptionPackageUpdate", "SubscriptionPackageOut", "TenantLicenseAssign",
            "PlatformClientBrief", "MaintenanceCompanyOut", "TenantProvisionBody", "TenantProvisionOut",
            "PlatformClientCreate", "PlatformUserCreate", "PlatformUserCreateOut",
        ],
        "labor.py": [
            "TechnicianProfileCreate", "TechnicianProfileUpdate", "TechnicianProfileOut",
            "LaborEntryCreate", "LaborEntryOut", "TechnicianScheduleCreate", "TechnicianScheduleOut",
        ],
        "locations.py": ["LocationCreate", "LocationUpdate", "LocationOut", "LocationTreeNode"],
        "dashboard.py": ["DashboardSummaryOut"],
        "common.py": ["PaginatedMeta", "PaginatedWorkOrders", "AuditLogOut"],
    }

    for fname, names in groups.items():
        body = "".join(chunks[n] for n in names if n in chunks)
        (APP / "schemas" / fname).write_text(header + body, encoding="utf-8")

    init_parts = [
        "auth", "clients", "assets", "templates", "work_orders", "billing",
        "notifications", "platform", "labor", "locations", "dashboard", "common",
    ]
    init_lines = ['"""Pydantic schemas — split by domain (Wave 6)."""', ""]
    for mod in init_parts:
        init_lines.append(f"from app.schemas.{mod} import *  # noqa: F403")
    init_lines.append("")
    init_lines.append("__all__ = [")
    for name in sorted(chunks.keys()):
        init_lines.append(f'    "{name}",')
    init_lines.append("]")
    (APP / "schemas" / "__init__.py").write_text("\n".join(init_lines) + "\n", encoding="utf-8")
    (APP / "schemas.py.bak").write_text(schemas_py, encoding="utf-8")
    (APP / "schemas.py").unlink()
    print("schemas split OK", len(chunks), "classes")


if __name__ == "__main__":
    if (APP / "models.py").exists():
        split_models()
    elif not (APP / "models" / "__init__.py").exists() and (APP / "models.py.bak").exists():
        (APP / "models.py").write_text((APP / "models.py.bak").read_text(encoding="utf-8"), encoding="utf-8")
        split_models()
    if (APP / "schemas.py").exists():
        split_schemas()
    elif (APP / "schemas.py.bak").exists():
        (APP / "schemas.py").write_text((APP / "schemas.py.bak").read_text(encoding="utf-8"), encoding="utf-8")
        split_schemas()
