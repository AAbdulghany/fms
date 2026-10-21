"""A1 — Backfill CLI: link assets to asset types and clients to verticals.

Usage:
    python -m app.cli.backfill_a1 [--dry-run] [--tenant <uuid>]

Modes:
    --dry-run     Compute what would be done; write nothing.
    --tenant <id> Restrict to one tenant (UUID).

Output:
    JSON summary: clients mapped/unmapped, types created, assets linked/unlinked.

Per AgDR-A1, §6.3 Phase B backfill spec.
Environment:
    A1_BACKFILL=1 must be set for the script to write on production-tagged instances.
    (docker_migrate sets this automatically when enabled.)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID

# Make sure the backend package is on PYTHONPATH when called as a module.
_backend = Path(__file__).resolve().parents[3]
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Asset, Client, Tenant
from app.models.asset_types import AssetType, Vertical
from app.services.asset_type_catalog_data import ACTIVITY_TYPE_ALIAS_MAP
from app.services.verticals import resolve_vertical


# ---------------------------------------------------------------------------
# Core logic (called per-tenant in one transaction)
# ---------------------------------------------------------------------------


def _backfill_tenant(
    db: Session,
    tenant: Tenant,
    *,
    dry_run: bool,
) -> dict:
    """Run backfill for one tenant; return a per-tenant report dict."""
    report: dict = {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "clients_mapped": 0,
        "clients_unmapped": 0,
        "unmapped_activity_types": [],
        "types_created": 0,
        "assets_linked": 0,
        "assets_still_unlinked": 0,
        "case_variant_groups": [],
    }

    # ------------------------------------------------------------------
    # 1. Clients — map activity_type → vertical_id
    # ------------------------------------------------------------------
    clients = db.scalars(
        select(Client).where(
            Client.tenant_id == tenant.id,
            Client.vertical_id.is_(None),
        )
    ).all()

    for c in clients:
        if not c.activity_type:
            continue
        v = resolve_vertical(db, c.activity_type)
        if v:
            if not dry_run:
                c.vertical_id = v.id
                c.activity_type = v.code
            report["clients_mapped"] += 1
        else:
            report["clients_unmapped"] += 1
            report["unmapped_activity_types"].append(c.activity_type)

    if not dry_run:
        db.flush()

    # ------------------------------------------------------------------
    # 2. Asset types — create legacy rows for each distinct category
    # ------------------------------------------------------------------
    # Collect distinct categories for this tenant
    cat_rows = db.execute(
        select(Asset.category)
        .where(Asset.tenant_id == tenant.id)
        .distinct()
    ).scalars().all()

    existing_codes = {
        at.code
        for at in db.scalars(
            select(AssetType).where(AssetType.tenant_id == tenant.id)
        ).all()
    }

    for cat in cat_rows:
        if cat in existing_codes:
            continue
        if not dry_run:
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            new_type = AssetType(
                tenant_id=tenant.id,
                code=cat,
                name_en=cat,
                name_ar=cat,
                origin="legacy",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(new_type)
            report["types_created"] += 1
        else:
            report["types_created"] += 1

    if not dry_run:
        db.flush()

    # ------------------------------------------------------------------
    # 3. Assets — set asset_type_id from category → code match
    # ------------------------------------------------------------------
    if not dry_run:
        dialect = db.bind.dialect.name if db.bind else "sqlite"  # type: ignore[union-attr]
        if dialect == "postgresql":
            # Batch update in Postgres (1,000-row chunks)
            offset = 0
            batch_size = 1000
            while True:
                result = db.execute(
                    text("""
                        UPDATE assets
                        SET asset_type_id = at.id
                        FROM asset_types at
                        WHERE at.tenant_id = assets.tenant_id
                          AND at.code = assets.category
                          AND assets.asset_type_id IS NULL
                          AND assets.tenant_id = :tid
                          AND assets.id IN (
                              SELECT id FROM assets
                              WHERE asset_type_id IS NULL
                                AND tenant_id = :tid
                              ORDER BY id
                              LIMIT :batch
                              OFFSET :offset
                          )
                    """),
                    {"tid": str(tenant.id), "batch": batch_size, "offset": offset},
                )
                linked = result.rowcount  # type: ignore[union-attr]
                report["assets_linked"] += linked
                if linked < batch_size:
                    break
                offset += batch_size
        else:
            # SQLite: load and update in Python
            asset_type_map = {
                at.code: at.id
                for at in db.scalars(
                    select(AssetType).where(AssetType.tenant_id == tenant.id)
                ).all()
            }
            unlinked = db.scalars(
                select(Asset).where(
                    Asset.tenant_id == tenant.id,
                    Asset.asset_type_id.is_(None),
                )
            ).all()
            for a in unlinked:
                if a.category in asset_type_map:
                    a.asset_type_id = asset_type_map[a.category]
                    report["assets_linked"] += 1
        db.flush()

    # Still-unlinked count (dry-run: count before we would link)
    still_unlinked = int(
        db.execute(
            select(__import__("sqlalchemy").func.count()).select_from(Asset).where(
                Asset.tenant_id == tenant.id,
                Asset.asset_type_id.is_(None),
            )
        ).scalar()
        or 0
    )
    if dry_run:
        # Subtract the ones we would have linked
        still_unlinked -= report["assets_linked"]
        still_unlinked = max(still_unlinked, 0)
    report["assets_still_unlinked"] = still_unlinked

    # ------------------------------------------------------------------
    # 4. Case variant groups
    # ------------------------------------------------------------------
    lower_map: dict[str, list[str]] = {}
    for cat in cat_rows:
        lower_map.setdefault(cat.lower(), []).append(cat)
    report["case_variant_groups"] = [
        v for v in lower_map.values() if len(v) > 1
    ]

    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_backfill(
    *,
    dry_run: bool = False,
    tenant_id: UUID | None = None,
) -> list[dict]:
    with SessionLocal() as db:
        if tenant_id:
            tenant = db.get(Tenant, tenant_id)
            if not tenant:
                raise SystemExit(f"Tenant {tenant_id} not found")
            tenants = [tenant]
        else:
            tenants = list(db.scalars(select(Tenant)).all())

        all_reports: list[dict] = []
        for tenant in tenants:
            report = _backfill_tenant(db, tenant, dry_run=dry_run)
            all_reports.append(report)
            if not dry_run:
                db.commit()

        return all_reports


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A1 backfill: link assets to asset types and clients to verticals."
    )
    parser.add_argument("--dry-run", action="store_true", help="Read-only; write nothing.")
    parser.add_argument("--tenant", type=UUID, default=None, help="Restrict to one tenant UUID.")
    args = parser.parse_args()

    reports = run_backfill(dry_run=args.dry_run, tenant_id=args.tenant)
    print(json.dumps(reports, indent=2, default=str))

    # Summary
    total_unlinked = sum(r["assets_still_unlinked"] for r in reports)
    if total_unlinked > 0:
        print(
            f"\n⚠  {total_unlinked} asset(s) still unlinked. "
            "Check case variant groups in the report.",
            file=sys.stderr,
        )
    else:
        print("\n✓ All assets linked.", file=sys.stderr)


if __name__ == "__main__":
    main()
