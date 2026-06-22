#!/usr/bin/env python3
"""Move components into features/*/components or shared/components with shims."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMP = ROOT / "src" / "components"

SHARED = {
    "Layout.tsx",
    "Sidebar.tsx",
    "EmptyState.tsx",
    "FilterBar.tsx",
    "OrbitLogo.tsx",
    "ProtectedRoute.tsx",
    "FeatureRoute.tsx",
    "NotificationBell.tsx",
    "StatsCard.tsx",
    "ClockWidget.tsx",
    "UserRoleBadge.tsx",
    "LocationTree.tsx",
    "CategoryObservationsEditor.tsx",
}

FEATURE_MAP: dict[str, str] = {
    "CompanyCreateModal.tsx": "companies",
    "CompanyEditModal.tsx": "companies",
    "SiteProvisionModal.tsx": "companies",
    "SiteEditModal.tsx": "companies",
    "SiteQrModal.tsx": "companies",
    "SiteAssignManagerModal.tsx": "companies",
    "ProvisionCredentialsModal.tsx": "companies",
    "AssetImportModal.tsx": "assets",
    "AssetEditModal.tsx": "assets",
    "AssetRegisterModal.tsx": "assets",
    "AssetLifecycleBadge.tsx": "assets",
    "AssetLifecycleTimeline.tsx": "assets",
    "AssetWorkOrderPanel.tsx": "assets",
    "MaintenanceCalendar.tsx": "assets",
    "WorkOrderRequestReviewModal.tsx": "work-orders",
    "InvoicePreviewModal.tsx": "invoices",
}


def fix_imports(content: str) -> str:
    content = content.replace('from "../lib/', 'from "@/lib/')
    content = content.replace('from "../components/', 'from "@/components/')
    content = content.replace('from "./', 'from "@/components/')
    return content


def write_shim(src: Path, target: str, named: str) -> None:
    src.write_text(
        f'/** @deprecated Import from `{target}` */\n'
        f'export {{ {named} }} from "{target}";\n',
        encoding="utf-8",
    )


def write_default_shim(src: Path, target: str) -> None:
    src.write_text(
        f'/** @deprecated Import from `{target}` */\n'
        f'export {{ default }} from "{target}";\n',
        encoding="utf-8",
    )


def migrate_file(name: str, dest_dir: Path, shim_target: str) -> None:
    src = COMP / name
    if not src.exists():
        print(f"skip missing {name}")
        return
    text = src.read_text(encoding="utf-8")
    if text.lstrip().startswith("/** @deprecated"):
        print(f"skip shim {name}")
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / name
    dest.write_text(fix_imports(text), encoding="utf-8")
    base = name.removesuffix(".tsx")
    if "export default" in text:
        write_default_shim(src, shim_target)
    else:
        write_shim(src, shim_target, base)
    print(f"ok {name} -> {dest_dir.relative_to(ROOT)}")


def main() -> None:
    for name in SHARED:
        migrate_file(name, ROOT / "src" / "shared" / "components", f"@/shared/components/{name.removesuffix('.tsx')}")

    for name, feature in FEATURE_MAP.items():
        migrate_file(name, ROOT / "src" / "features" / feature / "components", f"@/features/{feature}/components/{name.removesuffix('.tsx')}")

    print("done")


if __name__ == "__main__":
    main()
