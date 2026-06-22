#!/usr/bin/env python3
"""Fix api/routes shims to re-export all symbols (tests import handlers directly)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app"
ROUTES = ROOT / "api" / "routes"

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


def main() -> None:
    for route_name, (domain, module) in MIGRATIONS.items():
        target = f"app.domains.{domain}.{module}"
        shim = (
            f'"""Re-export — canonical implementation in {target}."""\n\n'
            f"from {target} import *  # noqa: F403\n"
        )
        (ROUTES / f"{route_name}.py").write_text(shim, encoding="utf-8")
        print(f"fixed {route_name}")
    print("done")


if __name__ == "__main__":
    main()
