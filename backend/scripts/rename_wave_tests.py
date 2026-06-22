#!/usr/bin/env python3
"""Rename wave-prefixed domain tests to domain names (NT-CLEAN-23)."""

from __future__ import annotations

import shutil
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1] / "tests"

RENAMES: dict[str, tuple[str, str]] = {
    "domains/platform/test_wave0_app_env.py": "domains/platform/test_app_env.py",
    "domains/platform/test_wave0_migration.py": "domains/platform/test_migration_chain.py",
    "domains/platform/test_wave0_schema.py": "domains/platform/test_schema_bootstrap.py",
    "domains/platform/test_wave1_platform.py": "domains/platform/test_platform_licensing.py",
    "domains/platform/test_wave2_demo.py": "domains/platform/test_demo_environment.py",
    "domains/assets/test_wave3_assets.py": "domains/assets/test_assets_module.py",
    "domains/assets/test_wave4_schedule_anchor.py": "domains/assets/test_schedule_anchor.py",
    "domains/billing/test_wave4_invoices.py": "domains/billing/test_invoices_acceptance.py",
    "domains/clients/test_wave5_provision.py": "domains/clients/test_provision_acceptance.py",
    "domains/work_orders/test_wave5_work_orders.py": "domains/work_orders/test_work_orders_acceptance.py",
}

# Orphan duplicates at tests/ root (pre-domain-move)
ORPHANS = [
    "test_wave0_app_env.py",
    "test_wave0_migration.py",
    "test_wave0_schema.py",
    "test_wave1_platform.py",
    "test_wave2_demo.py",
    "test_wave3_assets.py",
    "test_wave4_schedule_anchor.py",
    "test_wave4_invoices.py",
    "test_wave5_provision.py",
    "test_wave5_work_orders.py",
]


def main() -> None:
    for old_rel, new_rel in RENAMES.items():
        old = TESTS / old_rel
        new = TESTS / new_rel
        if old.exists() and not new.exists():
            shutil.move(str(old), str(new))
            print(f"renamed {old_rel} -> {new_rel}")
        elif new.exists():
            print(f"skip exists {new_rel}")

    for name in ORPHANS:
        path = TESTS / name
        if path.exists():
            path.unlink()
            print(f"removed orphan {name}")

    print("done")


if __name__ == "__main__":
    main()
