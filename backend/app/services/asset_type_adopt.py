"""A1 — Adopt platform catalog templates into a tenant asset type library (copy-on-adopt).

See docs/engineering/AgDR-A1-asset-type-copy-on-adopt.md and tech design §5.4.
The service flushes but never commits; the caller owns the transaction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AssetType,
    AssetTypeTemplate,
    AssetTypeTemplateVertical,
    AssetTypeVertical,
    ReportTemplate,
    User,
)
from app.services.audit import write_audit

REASON_ALREADY_ADOPTED = "already_adopted"
REASON_MERGED = "merged_with_existing_code"


@dataclass
class SkippedAdoption:
    template_id: UUID
    asset_type_id: UUID
    reason: str


@dataclass
class AdoptResult:
    created: list[AssetType] = field(default_factory=list)
    skipped: list[SkippedAdoption] = field(default_factory=list)


def resolve_tenant_report_template_id(
    db: Session, tenant_id: UUID, code: Optional[str]
) -> Optional[UUID]:
    """Resolve a template code (e.g. ``STD-INSP``) against this tenant's report templates only."""
    if not code:
        return None
    return db.scalar(
        select(ReportTemplate.id)
        .where(
            ReportTemplate.tenant_id == tenant_id,
            ReportTemplate.code == code,
            ReportTemplate.is_active.is_(True),
        )
        .order_by(ReportTemplate.version.desc(), ReportTemplate.created_at.desc())
        .limit(1)
    )


def _dedupe(ids: list[UUID]) -> list[UUID]:
    seen: set[UUID] = set()
    out: list[UUID] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def adopt_templates(
    db: Session,
    *,
    tenant_id: UUID,
    template_ids: list[UUID],
    actor: Optional[User] = None,
) -> AdoptResult:
    """Copy catalog templates into the tenant library. Idempotent (I3).

    All templates are validated before any row is written, so an invalid or inactive
    template raises ``400 INVALID_TEMPLATE`` with nothing changed.
    """
    ids = _dedupe(list(template_ids))

    templates: dict[UUID, AssetTypeTemplate] = {}
    for tid in ids:
        tmpl = db.get(AssetTypeTemplate, tid)
        if tmpl is None or not tmpl.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_TEMPLATE")
        templates[tid] = tmpl

    now = datetime.now(timezone.utc)
    result = AdoptResult()
    report_cache: dict[str, Optional[UUID]] = {}

    for tid in ids:
        tmpl = templates[tid]

        already = db.scalar(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id, AssetType.source_template_id == tmpl.id
            )
        )
        if already is not None:
            result.skipped.append(SkippedAdoption(tmpl.id, already.id, REASON_ALREADY_ADOPTED))
            continue

        report_code = tmpl.default_report_template_code
        if report_code and report_code not in report_cache:
            report_cache[report_code] = resolve_tenant_report_template_id(db, tenant_id, report_code)
        report_id = report_cache.get(report_code) if report_code else None

        existing = db.scalar(
            select(AssetType).where(
                AssetType.tenant_id == tenant_id,
                func.lower(AssetType.code) == tmpl.code.lower(),
            )
        )
        if existing is not None:
            # Merge: provenance + fill NULL defaults only; never overwrite tenant values.
            if existing.source_template_id is None:
                existing.source_template_id = tmpl.id
                existing.source_version = tmpl.version
                existing.adopted_at = now
            for attr, value in (
                ("default_max_age_years", tmpl.default_max_age_years),
                ("default_max_repair_count", tmpl.default_max_repair_count),
                ("default_criticality", tmpl.default_criticality),
                ("default_frequency", tmpl.default_frequency),
                ("default_report_template_id", report_id),
            ):
                if getattr(existing, attr) is None and value is not None:
                    setattr(existing, attr, value)
            db.flush()
            result.skipped.append(SkippedAdoption(tmpl.id, existing.id, REASON_MERGED))
            continue

        row = AssetType(
            tenant_id=tenant_id,
            code=tmpl.code,
            name_en=tmpl.name_en,
            name_ar=tmpl.name_ar,
            default_max_age_years=tmpl.default_max_age_years,
            default_max_repair_count=tmpl.default_max_repair_count,
            default_criticality=tmpl.default_criticality,
            default_frequency=tmpl.default_frequency,
            default_report_template_id=report_id,
            origin="catalog",
            source_template_id=tmpl.id,
            source_version=tmpl.version,
            adopted_at=now,
            is_active=True,
        )
        db.add(row)
        db.flush()
        vertical_ids = db.scalars(
            select(AssetTypeTemplateVertical.vertical_id).where(
                AssetTypeTemplateVertical.template_id == tmpl.id
            )
        ).all()
        for vid in vertical_ids:
            db.add(AssetTypeVertical(asset_type_id=row.id, vertical_id=vid))
        db.flush()
        db.refresh(row, attribute_names=["asset_type_verticals"])
        result.created.append(row)

    write_audit(
        db,
        tenant_id=tenant_id,
        actor=actor,
        action="adopt_asset_types",
        entity_type="asset_type",
        after={
            "created": len(result.created),
            "skipped": len(result.skipped),
            "created_codes": [r.code for r in result.created],
        },
    )
    db.flush()
    return result
