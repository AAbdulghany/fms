"""A1 — Idempotent upsert of the platform vertical and asset-type template catalog.

``ensure_vertical_catalog(db)`` follows the ``ensure_default_packages`` pattern
in ``services/platform_bootstrap.py``.  It is called from
``run_wave0_platform_bootstrap`` after the schema is ready.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_types import AssetTypeTemplate, AssetTypeTemplateVertical, Vertical
from app.services.asset_type_catalog_data import TEMPLATE_SEED, VERTICAL_SEED


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_vertical_catalog(db: Session) -> dict[str, int]:
    """Upsert verticals and asset-type templates; return row counts."""

    # ------------------------------------------------------------------
    # 1. Verticals
    # ------------------------------------------------------------------
    vertical_by_code: dict[str, Vertical] = {}
    for spec in VERTICAL_SEED:
        row = db.scalar(select(Vertical).where(Vertical.code == spec["code"]))
        if not row:
            row = Vertical(
                code=spec["code"],
                name_en=spec["name_en"],
                name_ar=spec["name_ar"],
                sort_order=spec["sort_order"],
                is_active=True,
                created_at=_utcnow(),
            )
            db.add(row)
            db.flush()
        else:
            # Update if fields changed (name or sort_order drift)
            changed = False
            for field in ("name_en", "name_ar", "sort_order"):
                if getattr(row, field) != spec[field]:
                    setattr(row, field, spec[field])
                    changed = True
            if not row.is_active:
                row.is_active = True
                changed = True
            if changed:
                db.flush()
        vertical_by_code[spec["code"]] = row

    # Mark verticals removed from seed as inactive
    all_codes = {s["code"] for s in VERTICAL_SEED}
    for orphan in db.scalars(
        select(Vertical).where(Vertical.is_active.is_(True))
    ).all():
        if orphan.code not in all_codes:
            orphan.is_active = False
    db.flush()

    # ------------------------------------------------------------------
    # 2. Asset type templates
    # ------------------------------------------------------------------
    template_by_code: dict[str, AssetTypeTemplate] = {}
    for spec in TEMPLATE_SEED:
        row = db.scalar(select(AssetTypeTemplate).where(AssetTypeTemplate.code == spec["code"]))
        if not row:
            row = AssetTypeTemplate(
                code=spec["code"],
                name_en=spec["name_en"],
                name_ar=spec["name_ar"],
                default_max_age_years=spec.get("default_max_age_years"),
                default_max_repair_count=spec.get("default_max_repair_count"),
                default_criticality=spec.get("default_criticality"),
                default_frequency=spec.get("default_frequency"),
                default_report_template_code=spec.get("default_report_template_code"),
                version=1,
                is_active=True,
                created_at=_utcnow(),
                updated_at=_utcnow(),
            )
            db.add(row)
            db.flush()
            # Seed vertical tags for new templates
            _sync_template_verticals(db, row, spec["verticals"], vertical_by_code)
        else:
            # Check for content changes → increment version
            content_fields = (
                "name_en",
                "name_ar",
                "default_max_age_years",
                "default_max_repair_count",
                "default_criticality",
                "default_frequency",
                "default_report_template_code",
            )
            changed = False
            for field in content_fields:
                if getattr(row, field) != spec.get(field):
                    setattr(row, field, spec.get(field))
                    changed = True
            if changed:
                row.version += 1
                row.updated_at = _utcnow()
                db.flush()
            if not row.is_active:
                row.is_active = True
                db.flush()
            _sync_template_verticals(db, row, spec["verticals"], vertical_by_code)
        template_by_code[spec["code"]] = row

    # Mark templates removed from seed as inactive
    seed_codes = {s["code"] for s in TEMPLATE_SEED}
    for orphan in db.scalars(
        select(AssetTypeTemplate).where(AssetTypeTemplate.is_active.is_(True))
    ).all():
        if orphan.code not in seed_codes:
            orphan.is_active = False
    db.flush()

    return {
        "verticals": len(vertical_by_code),
        "templates": len(template_by_code),
    }


def _sync_template_verticals(
    db: Session,
    template: AssetTypeTemplate,
    vertical_codes: list[str],
    vertical_by_code: dict[str, Vertical],
) -> None:
    """Reconcile the template's vertical tag rows with the seed list."""
    existing_v_ids = {
        tv.vertical_id
        for tv in db.scalars(
            select(AssetTypeTemplateVertical).where(
                AssetTypeTemplateVertical.template_id == template.id
            )
        ).all()
    }
    desired_v_ids = {
        vertical_by_code[code].id for code in vertical_codes if code in vertical_by_code
    }

    # Add missing
    for vid in desired_v_ids - existing_v_ids:
        db.add(AssetTypeTemplateVertical(template_id=template.id, vertical_id=vid))

    # Remove extras (if any; normally never happens in a seed)
    for vid in existing_v_ids - desired_v_ids:
        stale = db.scalar(
            select(AssetTypeTemplateVertical).where(
                AssetTypeTemplateVertical.template_id == template.id,
                AssetTypeTemplateVertical.vertical_id == vid,
            )
        )
        if stale:
            db.delete(stale)

    db.flush()
