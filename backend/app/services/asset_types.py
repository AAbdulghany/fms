"""A1 — Thin facade re-exporting asset type and vertical helpers.

The clients router and assets router import from this module.
Business logic lives in ``asset_types_service.py`` and ``verticals.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Client
from app.models.asset_types import AssetType
from app.services.verticals import resolve_vertical

# Re-export all service helpers so existing imports keep working
from app.services.asset_types_service import (  # noqa: F401
    ALLOWED_FREQUENCIES,
    adopt_templates,
    apply_type_defaults_to_asset,
    count_assets_for_type,
    create_asset_type,
    get_asset_type_or_404,
    resolve_asset_type_for_category,
    update_asset_type,
)


# ---------------------------------------------------------------------------
# Client vertical helpers (used by clients router)
# ---------------------------------------------------------------------------


def apply_client_vertical(
    db: Session,
    client: Client,
    *,
    vertical_code: str | None,
    activity_type: str | None,
) -> None:
    """Dual-write vertical_id and activity_type on *client* (phase D, §6.4).

    Resolution order:
    1. If *vertical_code* is set, it wins.  Unknown code raises 400.
    2. Else if *activity_type* is set, resolve through the alias map.
    3. If neither resolves, leave existing values unchanged.
    """
    # Determine the effective code to resolve
    effective: str | None = vertical_code or activity_type

    if not effective:
        return  # nothing to do

    v = resolve_vertical(db, effective)

    if vertical_code and not v:
        # Explicit vertical_code that is unknown is an error
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_VERTICAL")

    if v:
        client.vertical_id = v.id
        # Always keep activity_type in sync (dual-write)
        client.activity_type = v.code
    elif activity_type:
        # Unknown alias: store as-is; CLI report will flag it
        client.activity_type = activity_type


# ---------------------------------------------------------------------------
# Asset write helpers (used by assets router)
# ---------------------------------------------------------------------------


@dataclass
class ResolvedAssetType:
    """Result of ``resolve_asset_type_for_write``."""
    category: str
    asset_type: Optional[AssetType]


def resolve_asset_type_for_write(
    db: Session,
    *,
    tenant_id: UUID,
    asset_type_id: Optional[UUID],
    category: str,
    asset_type_name: Optional[str] = None,
) -> ResolvedAssetType:
    """Resolve asset type and enforce I1 for an asset create operation.

    Resolution order:
    1. ``asset_type_id`` if set (existing library pick).
    2. ``asset_type_name`` — find or create by typed label (preferred register path).
    3. Else silent link by ``category`` code.
    """
    if asset_type_id is not None:
        at = db.get(AssetType, asset_type_id)
        if not at or at.tenant_id != tenant_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSET_TYPE")
        if not at.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_ARCHIVED")
        if category and category != "general" and category != at.code:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_CATEGORY_MISMATCH"
            )
        return ResolvedAssetType(category=at.code, asset_type=at)

    label = (asset_type_name or "").strip()
    if label:
        from app.services.asset_types_service import find_or_create_asset_type_by_label

        at = find_or_create_asset_type_by_label(db, tenant_id, label)
        return ResolvedAssetType(category=at.code, asset_type=at)

    linked = get_tenant_asset_type_by_code(db, tenant_id, category)
    return ResolvedAssetType(category=category, asset_type=linked)


def get_tenant_asset_type(
    db: Session, tenant_id: UUID, asset_type_id: UUID
) -> Optional[AssetType]:
    """Load a tenant asset type by id; return None if missing or cross-tenant."""
    at = db.get(AssetType, asset_type_id)
    if not at or at.tenant_id != tenant_id:
        return None
    return at


def get_tenant_asset_type_by_code(
    db: Session, tenant_id: UUID, code: str
) -> Optional[AssetType]:
    """Exact code match (case-sensitive, per I1)."""
    return db.scalar(
        select(AssetType).where(
            AssetType.tenant_id == tenant_id,
            AssetType.code == code,
        )
    )


# Alias used by the assets router
find_type_by_code = get_tenant_asset_type_by_code


def apply_type_defaults(
    asset_type: Optional[AssetType],
    *,
    max_age_years: Optional[int],
    max_repair_count: Optional[int],
    criticality: Optional[str],
) -> dict[str, Any]:
    """Fill None body fields from asset type defaults. Explicit body values win."""
    if asset_type is None:
        return {
            "max_age_years": max_age_years,
            "max_repair_count": max_repair_count,
            "criticality": criticality,
        }
    return {
        "max_age_years": max_age_years if max_age_years is not None else asset_type.default_max_age_years,
        "max_repair_count": max_repair_count if max_repair_count is not None else asset_type.default_max_repair_count,
        "criticality": criticality if criticality is not None else asset_type.default_criticality,
    }


# ---------------------------------------------------------------------------
# Client vertical helpers (used by clients router)
# ---------------------------------------------------------------------------


def client_vertical_code(db: Session, client: Client) -> str | None:
    """Return the vertical code for a client, preferring the FK column."""
    if client.vertical_id:
        from app.models.asset_types import Vertical
        v = db.get(Vertical, client.vertical_id)
        return v.code if v else None
    return client.activity_type
