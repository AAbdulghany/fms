#!/usr/bin/env python3
"""Rewrite component shims — `export *` plus default re-export where needed."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMP = ROOT / "src" / "components"

# name -> (target, has_default_export)
TARGETS: dict[str, tuple[str, bool]] = {
    "Layout.tsx": ("@/shared/components/Layout", False),
    "Sidebar.tsx": ("@/shared/components/Sidebar", False),
    "EmptyState.tsx": ("@/shared/components/EmptyState", False),
    "FilterBar.tsx": ("@/shared/components/FilterBar", False),
    "OrbitLogo.tsx": ("@/shared/components/OrbitLogo", False),
    "ProtectedRoute.tsx": ("@/shared/components/ProtectedRoute", False),
    "FeatureRoute.tsx": ("@/shared/components/FeatureRoute", False),
    "NotificationBell.tsx": ("@/shared/components/NotificationBell", True),
    "StatsCard.tsx": ("@/shared/components/StatsCard", False),
    "ClockWidget.tsx": ("@/shared/components/ClockWidget", True),
    "UserRoleBadge.tsx": ("@/shared/components/UserRoleBadge", False),
    "LocationTree.tsx": ("@/shared/components/LocationTree", False),
    "CategoryObservationsEditor.tsx": ("@/shared/components/CategoryObservationsEditor", False),
    "CompanyCreateModal.tsx": ("@/features/companies/components/CompanyCreateModal", False),
    "CompanyEditModal.tsx": ("@/features/companies/components/CompanyEditModal", False),
    "SiteProvisionModal.tsx": ("@/features/companies/components/SiteProvisionModal", False),
    "SiteEditModal.tsx": ("@/features/companies/components/SiteEditModal", False),
    "SiteQrModal.tsx": ("@/features/companies/components/SiteQrModal", False),
    "SiteAssignManagerModal.tsx": ("@/features/companies/components/SiteAssignManagerModal", False),
    "ProvisionCredentialsModal.tsx": ("@/features/companies/components/ProvisionCredentialsModal", False),
    "AssetImportModal.tsx": ("@/features/assets/components/AssetImportModal", False),
    "AssetEditModal.tsx": ("@/features/assets/components/AssetEditModal", False),
    "AssetRegisterModal.tsx": ("@/features/assets/components/AssetRegisterModal", False),
    "AssetLifecycleBadge.tsx": ("@/features/assets/components/AssetLifecycleBadge", False),
    "AssetLifecycleTimeline.tsx": ("@/features/assets/components/AssetLifecycleTimeline", False),
    "AssetWorkOrderPanel.tsx": ("@/features/assets/components/AssetWorkOrderPanel", False),
    "MaintenanceCalendar.tsx": ("@/features/assets/components/MaintenanceCalendar", False),
    "WorkOrderRequestReviewModal.tsx": ("@/features/work-orders/components/WorkOrderRequestReviewModal", False),
    "InvoicePreviewModal.tsx": ("@/features/invoices/components/InvoicePreviewModal", False),
}


def main() -> None:
    for name, (target, has_default) in TARGETS.items():
        lines = [
            f'/** @deprecated Import from `{target}` */',
            f'export * from "{target}";',
        ]
        if has_default:
            lines.append(f'export {{ default }} from "{target}";')
        (COMP / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("done", len(TARGETS))


if __name__ == "__main__":
    main()
