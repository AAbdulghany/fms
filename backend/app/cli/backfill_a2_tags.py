"""A2 — Mint AssetTag rows for assets missing an active tag; rewrite qr_payload.

Usage:
    python -m app.cli.backfill_a2_tags [--dry-run] [--tenant <uuid>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import UUID

_backend = Path(__file__).resolve().parents[3]
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Asset, Tenant
from app.models.asset_tags import AssetTag
from app.services.asset_tags import ensure_active_tag


def _backfill_tenant(db: Session, tenant: Tenant, *, dry_run: bool) -> dict:
    assets = list(db.scalars(select(Asset).where(Asset.tenant_id == tenant.id)).all())
    minted = 0
    skipped = 0
    for asset in assets:
        has_active = db.scalar(
            select(AssetTag).where(
                AssetTag.asset_id == asset.id,
                AssetTag.status == "active",
            )
        )
        if has_active and asset.qr_payload and "/a/" in (asset.qr_payload or ""):
            skipped += 1
            continue
        if dry_run:
            minted += 1
            continue
        ensure_active_tag(db, asset)
        minted += 1
    if not dry_run:
        db.commit()
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "assets_total": len(assets),
        "minted_or_rewritten": minted,
        "already_ok": skipped,
        "dry_run": dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="A2 backfill asset QR tags")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--tenant", type=str, default=None)
    args = parser.parse_args()

    reports = []
    with SessionLocal() as db:
        q = select(Tenant)
        if args.tenant:
            q = q.where(Tenant.id == UUID(args.tenant))
        tenants = list(db.scalars(q).all())
        for tenant in tenants:
            reports.append(_backfill_tenant(db, tenant, dry_run=args.dry_run))
    print(json.dumps({"tenants": reports}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
