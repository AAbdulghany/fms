"""Smart asset label generation (Phase 3.1)."""

from __future__ import annotations

import os
import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Asset, Site


def _slug_code(value: str, max_len: int = 8) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value.upper())
    return (cleaned[:max_len] or "SITE")


def generate_label_code(db: Session, *, tenant_id: UUID, site_id: UUID, category: str) -> str:
    site = db.get(Site, site_id)
    site_part = _slug_code(site.name if site else "SITE")
    cat_part = _slug_code(category or "GEN", 6)
    prefix = f"{site_part}-{cat_part}-"
    count = db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(Asset.tenant_id == tenant_id, Asset.label_code.like(f"{prefix}%"))
    ) or 0
    return f"{prefix}{count + 1:03d}"


def qr_payload_for_asset(asset_id: UUID) -> str:
    base = os.environ.get("PUBLIC_APP_URL", "").rstrip("/")
    if base:
        return f"{base}/assets/{asset_id}"
    return f"/assets/{asset_id}"
