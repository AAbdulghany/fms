"""SQLAlchemy ORM models — split by domain (Wave 6)."""

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
from app.models.asset_types import *  # noqa: F403  # A1: verticals + asset type library
from app.models.asset_tags import *  # noqa: F403  # A2: opaque QR tags

__all__ = [
    "UserRole", "WorkOrderStatus", "WorkOrderSource", "Urgency", "ReportStatus",
    "InvoiceStatus", "AssetLifecycleStatus",
    "Tenant", "SubscriptionPackage", "TenantSubscription", "PlatformSettings",
    "User", "UserSiteScope", "Client", "Site", "Location",
    "Asset", "MaintenanceSchedule", "ReportTemplate",
    "WorkOrder", "MaintenanceReport", "Comment", "WorkOrderDocument",
    "PricingProfile", "Contract", "Part", "Invoice", "InvoiceLineItem",
    "TaxProfile", "WorkOrderPart",
    "TechnicianProfile", "LaborEntry", "TechnicianSchedule",
    "Notification", "AuditLog",
    # A1
    "Vertical", "AssetTypeTemplate", "AssetTypeTemplateVertical",
    "AssetType", "AssetTypeVertical",
    "AssetTag",
]
