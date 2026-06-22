#!/usr/bin/env python3
"""Move src/pages/*.tsx into src/features/<feature>/pages/ with shims."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "src" / "pages"

PAGE_MAP: dict[str, str] = {
    "DashboardPage.tsx": "dashboard",
    "CompaniesPage.tsx": "companies",
    "CompanyDetailPage.tsx": "companies",
    "SiteDetailPage.tsx": "companies",
    "MaintenanceCompaniesPage.tsx": "platform",
    "AssetsPage.tsx": "assets",
    "AssetDetailPage.tsx": "assets",
    "WorkOrdersPage.tsx": "work-orders",
    "WorkOrderDetailPage.tsx": "work-orders",
    "InvoicesPage.tsx": "invoices",
    "InvoiceDetailPage.tsx": "invoices",
    "UsersPage.tsx": "users",
    "ProfilePage.tsx": "users",
    "PlatformPackagesPage.tsx": "platform",
    "SubscriptionPage.tsx": "platform",
    "ReportTemplatesPage.tsx": "reports",
    "LocationsPage.tsx": "locations",
    "LaborPage.tsx": "labor",
    "FeatureUnavailablePage.tsx": "shared",
}

DEFAULT_EXPORT_PAGES = {
    "CompaniesPage.tsx",
    "CompanyDetailPage.tsx",
    "SiteDetailPage.tsx",
    "UsersPage.tsx",
    "ReportTemplatesPage.tsx",
    "AssetsPage.tsx",
    "AssetDetailPage.tsx",
    "LocationsPage.tsx",
    "LaborPage.tsx",
}


def fix_imports(content: str) -> str:
    content = content.replace('from "../lib/', 'from "@/lib/')
    content = content.replace('from "../components/', 'from "@/components/')
    content = content.replace('from "../../lib/', 'from "@/lib/')
    content = content.replace('from "../../components/', 'from "@/components/')
    return content


def write_shim(src: Path, feature: str, page: str) -> None:
    base = page.removesuffix(".tsx")
    target = f"@/features/{feature}/pages/{base}"
    if page in DEFAULT_EXPORT_PAGES:
        src.write_text(
            f'/** @deprecated Import from `{target}` */\n'
            f'export {{ default }} from "{target}";\n',
            encoding="utf-8",
        )
    else:
        src.write_text(
            f'/** @deprecated Import from `{target}` */\n'
            f'export {{ {base} }} from "{target}";\n',
            encoding="utf-8",
        )


def main() -> None:
    for page, feature in PAGE_MAP.items():
        src = PAGES / page
        if not src.exists():
            print(f"skip missing {src}")
            continue
        # skip if already a shim
        text = src.read_text(encoding="utf-8")
        if text.lstrip().startswith("/** @deprecated"):
            print(f"skip shim {src}")
            continue
        dest_dir = ROOT / "src" / "features" / feature / "pages"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / page
        dest.write_text(fix_imports(text), encoding="utf-8")
        write_shim(src, feature, page)
        print(f"ok {page} -> features/{feature}/pages/")
    print("done")


if __name__ == "__main__":
    main()
