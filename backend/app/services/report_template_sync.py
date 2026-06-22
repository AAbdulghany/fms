"""Sync STD-INSP report template to the current v2 schema for one or all tenants."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReportTemplate, Tenant
from app.services.report_schema_resolve import (
    DEFAULT_CATEGORY_KEY,
    get_observations_by_category,
)
from app.standard_inspection_report_schema import STANDARD_INSPECTION_SCHEMA

STD_INSP_CODE = "STD-INSP"
STD_INSP_NAME = "Standard Inspection"


def _merge_schema(existing: dict | None) -> dict:
    """Upgrade base sections while preserving custom category observation checklists."""
    merged = dict(STANDARD_INSPECTION_SCHEMA)
    if existing:
        preserved = get_observations_by_category(existing)
        if preserved:
            merged["observations_by_category"] = preserved
            default_fields = preserved.get(DEFAULT_CATEGORY_KEY)
            if default_fields:
                for sec in merged.get("sections", []):
                    if sec.get("id") == "sec_observations":
                        sec["fields"] = list(default_fields)
                        sec["category_variant"] = True
                        break
    return merged


def sync_std_insp_for_tenant(db: Session, tenant_id: UUID) -> tuple[str, ReportTemplate]:
    """Create or upgrade STD-INSP for a tenant. Returns action ('created'|'updated') and row."""
    tmpl = db.scalar(
        select(ReportTemplate).where(
            ReportTemplate.tenant_id == tenant_id,
            ReportTemplate.code == STD_INSP_CODE,
        )
    )
    new_schema = _merge_schema(tmpl.schema_json if tmpl else None)

    if tmpl is None:
        tmpl = ReportTemplate(
            tenant_id=tenant_id,
            name=STD_INSP_NAME,
            code=STD_INSP_CODE,
            schema_json=new_schema,
            maintenance_types=[],
            version=2,
            is_active=True,
        )
        db.add(tmpl)
        db.flush()
        return "created", tmpl

    old_schema = tmpl.schema_json or {}
    if old_schema == new_schema and tmpl.version >= 2:
        return "unchanged", tmpl

    tmpl.schema_json = new_schema
    if tmpl.version < 2:
        tmpl.version = 2
    else:
        tmpl.version += 1
    db.flush()
    return "updated", tmpl


def sync_std_insp_all_tenants(db: Session) -> dict[str, int]:
    """Sync STD-INSP for every tenant. Safe to run on every startup."""
    counts = {"created": 0, "updated": 0, "unchanged": 0}
    tenants = list(db.scalars(select(Tenant)).all())
    for tenant in tenants:
        action, _ = sync_std_insp_for_tenant(db, tenant.id)
        counts[action] += 1
    return counts
