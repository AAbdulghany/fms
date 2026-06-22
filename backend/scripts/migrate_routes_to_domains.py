#!/usr/bin/env python3
"""One-shot: move api/routes/*.py into app/domains/* with backward-compatible shims."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"
ROUTES = ROOT / "api" / "routes"

# route_module -> (domain_package, module_name under domain)
MIGRATIONS: dict[str, tuple[str, str]] = {
    "users": ("users", "router"),
    "clients": ("clients", "router"),
    "sites": ("clients", "sites"),
    "locations": ("clients", "locations"),
    "assets": ("assets", "router"),
    "work_orders": ("work_orders", "router"),
    "reports": ("reports", "router"),
    "templates": ("reports", "templates"),
    "invoices": ("billing", "invoices"),
    "billing_actions": ("billing", "billing_actions"),
    "catalog": ("billing", "catalog"),
    "labor": ("billing", "labor"),
    "dashboard": ("dashboard", "router"),
    "notifications": ("notifications", "router"),
    "tenants": ("platform", "tenants"),
    "platform": ("platform", "router"),
}


def shim(domain: str, module: str, route_name: str) -> str:
    target = f"app.domains.{domain}.{module}"
    return (
        f'"""Re-export — canonical implementation in {target}."""\n\n'
        f"from {target} import router\n\n"
        f'__all__ = ["router"]\n'
    )


def main() -> None:
    for route_name, (domain, module) in MIGRATIONS.items():
        src = ROUTES / f"{route_name}.py"
        if not src.exists():
            print(f"skip missing {src}")
            continue
        domain_dir = ROOT / "domains" / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        dest = domain_dir / f"{module}.py"
        if dest.exists():
            print(f"skip exists {dest}")
            continue
        content = src.read_text(encoding="utf-8")
        dest.write_text(content, encoding="utf-8")
        src.write_text(shim(domain, module, route_name), encoding="utf-8")
        init = domain_dir / "__init__.py"
        if not init.exists():
            init.write_text('"""Domain package."""\n', encoding="utf-8")
        print(f"ok {route_name} -> domains/{domain}/{module}.py")

    print("done")


if __name__ == "__main__":
    main()
