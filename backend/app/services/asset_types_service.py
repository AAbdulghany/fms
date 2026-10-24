"""A1 — Tenant asset-type library: adopt, create, update, and link helpers.

Design references:
- §5.4 Adoption algorithm
- Invariant I1: assets.category == asset_types.code when asset_type_id is set
- Invariant I2: asset_types.code is immutable after creation
- Invariant I3: one asset type per source_template_id per tenant
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Asset, ReportTemplate
from app.models.asset_types import (
    AssetType,
    AssetTypeTemplate,
    AssetTypeTemplateVertical,
    AssetTypeVertical,
    Vertical,
)

# Allowed frequency values for tenant types (locked A1 decision)
ALLOWED_FREQUENCIES = frozenset({"monthly", "quarterly", "semi_annual", "yearly"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _check_frequency(freq: str | None) -> None:
    if freq is not None and freq not in ALLOWED_FREQUENCIES:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="INVALID_FREQUENCY",
        )


def _resolve_report_template(
    db: Session, tenant_id: UUID, template_id: UUID | None
) -> None:
    """Verify that the report template belongs to this tenant (R9 guard)."""
    if template_id is None:
        return
    tmpl = db.get(ReportTemplate, template_id)
    if not tmpl or tmpl.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_REPORT_TEMPLATE")


def _check_code_uniqueness(
    db: Session, tenant_id: UUID, code: str, exclude_id: UUID | None = None
) -> None:
    """Case-insensitive duplicate check (I2)."""
    q = select(AssetType).where(
        AssetType.tenant_id == tenant_id,
        func.lower(AssetType.code) == code.lower(),
    )
    if exclude_id:
        q = q.where(AssetType.id != exclude_id)
    existing = db.scalar(q)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="ASSET_TYPE_CODE_EXISTS")


def _set_vertical_tags(db: Session, asset_type: AssetType, vertical_codes: list[str]) -> None:
    """Replace the vertical tags on a tenant asset type."""
    # Delete existing tags
    for tv in list(asset_type.asset_type_verticals):
        db.delete(tv)
    db.flush()

    if not vertical_codes:
        return

    for code in vertical_codes:
        v = db.scalar(select(Vertical).where(Vertical.code == code, Vertical.is_active.is_(True)))
        if not v:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"INVALID_VERTICAL:{code}",
            )
        db.add(AssetTypeVertical(asset_type_id=asset_type.id, vertical_id=v.id))
    db.flush()


# ---------------------------------------------------------------------------
# Adopt
# ---------------------------------------------------------------------------


def adopt_templates(
    db: Session,
    tenant_id: UUID,
    template_ids: list[UUID],
) -> dict[str, Any]:
    """Copy active templates into the tenant library (§5.4).

    Returns ``{created: [AssetType], skipped: [{template_id, asset_type_id, reason}]}``.
    """
    created: list[AssetType] = []
    skipped: list[dict[str, Any]] = []

    seen: set[UUID] = set()
    for tid in template_ids:
        if tid in seen:
            continue
        seen.add(tid)

        tmpl = db.get(AssetTypeTemplate, tid)
        if not tmpl or not tmpl.is_active:
            skipped.append(
                {"template_id": tid, "asset_type_id": None, "reason": "inactive_template"}
            )
            continue

        # Already adopted?
        already = db.scalar(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id,
                AssetType.source_template_id == tmpl.id,
            )
        )
        if already:
            skipped.append(
                {
                    "template_id": tid,
                    "asset_type_id": already.id,
                    "reason": "already_adopted",
                }
            )
            continue

        # Case-insensitive code match → merge with existing row
        existing_code = db.scalar(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id,
                func.lower(AssetType.code) == tmpl.code.lower(),
            )
        )
        if existing_code:
            # Link provenance; fill only NULL defaults
            existing_code.source_template_id = tmpl.id
            existing_code.source_version = tmpl.version
            existing_code.adopted_at = _utcnow()
            if existing_code.default_max_age_years is None:
                existing_code.default_max_age_years = tmpl.default_max_age_years
            if existing_code.default_max_repair_count is None:
                existing_code.default_max_repair_count = tmpl.default_max_repair_count
            if existing_code.default_criticality is None:
                existing_code.default_criticality = tmpl.default_criticality
            if existing_code.default_frequency is None:
                existing_code.default_frequency = tmpl.default_frequency
            if existing_code.default_report_template_id is None:
                rt = _find_report_template(db, tenant_id, tmpl.default_report_template_code)
                existing_code.default_report_template_id = rt.id if rt else None
            db.flush()
            skipped.append(
                {
                    "template_id": tid,
                    "asset_type_id": existing_code.id,
                    "reason": "merged_with_existing_code",
                }
            )
            continue

        # Resolve default report template for this tenant
        rt = _find_report_template(db, tenant_id, tmpl.default_report_template_code)

        new_type = AssetType(
            tenant_id=tenant_id,
            code=tmpl.code,
            name_en=tmpl.name_en,
            name_ar=tmpl.name_ar,
            default_max_age_years=tmpl.default_max_age_years,
            default_max_repair_count=tmpl.default_max_repair_count,
            default_criticality=tmpl.default_criticality,
            default_frequency=tmpl.default_frequency,
            default_report_template_id=rt.id if rt else None,
            origin="catalog",
            source_template_id=tmpl.id,
            source_version=tmpl.version,
            adopted_at=_utcnow(),
            is_active=True,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        db.add(new_type)
        db.flush()

        # Copy vertical tags from template
        for tv in db.scalars(
            select(AssetTypeTemplateVertical).where(
                AssetTypeTemplateVertical.template_id == tmpl.id
            )
        ).all():
            db.add(AssetTypeVertical(asset_type_id=new_type.id, vertical_id=tv.vertical_id))
        db.flush()

        created.append(new_type)

    return {"created": created, "skipped": skipped}


def _find_report_template(
    db: Session, tenant_id: UUID, code: str | None
) -> ReportTemplate | None:
    if not code:
        return None
    return db.scalar(
        select(ReportTemplate).where(
            ReportTemplate.tenant_id == tenant_id,
            ReportTemplate.code == code,
        )
    )


# ---------------------------------------------------------------------------
# Create custom type
# ---------------------------------------------------------------------------


def _slug_code(label: str) -> str:
    """Build an immutable code slug from a free-text type label."""
    raw = (label or "").strip().lower()
    out = []
    prev_us = False
    for ch in raw:
        if ch.isalnum():
            out.append(ch)
            prev_us = False
        elif not prev_us:
            out.append("_")
            prev_us = True
    code = "".join(out).strip("_")[:64]
    return code or "general"


def find_or_create_asset_type_by_label(
    db: Session,
    tenant_id: UUID,
    label: str,
    *,
    name_ar: str | None = None,
) -> AssetType:
    """Match by code / name_en (case-insensitive) or create a custom type.

    Used when registering an asset by typing the type name.
    """
    label = (label or "").strip()
    if not label:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_REQUIRED")

    existing = db.scalar(
        select(AssetType).where(
            AssetType.tenant_id == tenant_id,
            AssetType.is_active.is_(True),
            func.lower(AssetType.name_en) == label.lower(),
        )
    )
    if existing:
        return existing

    code = _slug_code(label)
    by_code = db.scalar(
        select(AssetType).where(
            AssetType.tenant_id == tenant_id,
            func.lower(AssetType.code) == code.lower(),
        )
    )
    if by_code:
        if not by_code.is_active:
            by_code.is_active = True
            by_code.updated_at = _utcnow()
        return by_code

    # Unique-ify code if a soft-conflict exists with different name
    base = code
    n = 2
    while True:
        clash = db.scalar(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id,
                func.lower(AssetType.code) == code.lower(),
            )
        )
        if not clash:
            break
        code = f"{base}_{n}"[:64]
        n += 1

    return create_asset_type(
        db,
        tenant_id,
        code=code,
        name_en=label,
        name_ar=(name_ar or label).strip() or label,
        vertical_codes=[],
        default_max_age_years=None,
        default_max_repair_count=None,
        default_criticality=None,
        default_frequency=None,
        default_report_template_id=None,
    )


def archive_all_asset_types(db: Session, tenant_id: UUID) -> int:
    """Soft-archive every tenant asset type (library reset)."""
    rows = list(
        db.scalars(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id,
                AssetType.is_active.is_(True),
            )
        ).all()
    )
    for at in rows:
        at.is_active = False
        at.updated_at = _utcnow()
    db.flush()
    return len(rows)


def create_asset_type(
    db: Session,
    tenant_id: UUID,
    code: str,
    name_en: str,
    name_ar: str,
    vertical_codes: list[str],
    default_max_age_years: int | None,
    default_max_repair_count: int | None,
    default_criticality: str | None,
    default_frequency: str | None,
    default_report_template_id: UUID | None,
) -> AssetType:
    _check_frequency(default_frequency)
    _check_code_uniqueness(db, tenant_id, code)
    _resolve_report_template(db, tenant_id, default_report_template_id)

    at = AssetType(
        tenant_id=tenant_id,
        code=code,
        name_en=name_en,
        name_ar=name_ar,
        default_max_age_years=default_max_age_years,
        default_max_repair_count=default_max_repair_count,
        default_criticality=default_criticality,
        default_frequency=default_frequency,
        default_report_template_id=default_report_template_id,
        origin="custom",
        source_template_id=None,
        source_version=None,
        adopted_at=None,
        is_active=True,
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(at)
    db.flush()
    _set_vertical_tags(db, at, vertical_codes)
    return at


# ---------------------------------------------------------------------------
# Update tenant type
# ---------------------------------------------------------------------------


def update_asset_type(
    db: Session,
    asset_type: AssetType,
    tenant_id: UUID,
    *,
    name_en: str | None = None,
    name_ar: str | None = None,
    vertical_codes: list[str] | None = None,
    default_max_age_years: int | None | type[...] = ...,
    default_max_repair_count: int | None | type[...] = ...,
    default_criticality: str | None | type[...] = ...,
    default_frequency: str | None | type[...] = ...,
    default_report_template_id: UUID | None | type[...] = ...,
    is_active: bool | None = None,
) -> AssetType:
    if name_en is not None:
        asset_type.name_en = name_en
    if name_ar is not None:
        asset_type.name_ar = name_ar
    if default_max_age_years is not ...:
        asset_type.default_max_age_years = default_max_age_years
    if default_max_repair_count is not ...:
        asset_type.default_max_repair_count = default_max_repair_count
    if default_criticality is not ...:
        asset_type.default_criticality = default_criticality
    if default_frequency is not ...:
        _check_frequency(default_frequency)
        asset_type.default_frequency = default_frequency
    if default_report_template_id is not ...:
        _resolve_report_template(db, tenant_id, default_report_template_id)
        asset_type.default_report_template_id = default_report_template_id
    if is_active is not None:
        asset_type.is_active = is_active
    if vertical_codes is not None:
        _set_vertical_tags(db, asset_type, vertical_codes)
    asset_type.updated_at = _utcnow()
    db.flush()
    return asset_type


# ---------------------------------------------------------------------------
# Asset link helper (used by asset create/update)
# ---------------------------------------------------------------------------


def resolve_asset_type_for_category(
    db: Session, tenant_id: UUID, category: str
) -> AssetType | None:
    """Find the tenant asset type whose code exactly equals *category*.

    Returns None if no match exists (legacy assets remain unlinked).
    """
    return db.scalar(
        select(AssetType).where(
            AssetType.tenant_id == tenant_id,
            AssetType.code == category,
        )
    )


def get_asset_type_or_404(
    db: Session, tenant_id: UUID, asset_type_id: UUID
) -> AssetType:
    """Load and tenant-check an asset type; raise 404 if missing."""
    at = db.get(AssetType, asset_type_id)
    if not at or at.tenant_id != tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="ASSET_TYPE_NOT_FOUND")
    return at


def apply_type_defaults_to_asset(
    at: AssetType,
    *,
    max_age_years: int | None,
    max_repair_count: int | None,
    criticality: str | None,
) -> tuple[int | None, int | None, str | None]:
    """Return (max_age_years, max_repair_count, criticality) with type defaults filled in.

    Explicit body values (non-None) always win over defaults.
    """
    resolved_age = max_age_years if max_age_years is not None else at.default_max_age_years
    resolved_repair = (
        max_repair_count if max_repair_count is not None else at.default_max_repair_count
    )
    resolved_criticality = criticality if criticality is not None else at.default_criticality
    return resolved_age, resolved_repair, resolved_criticality


def count_assets_for_type(db: Session, asset_type_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(Asset).where(Asset.asset_type_id == asset_type_id)
        )
        or 0
    )
