"""CSV asset import (Phase 3.1)."""

from __future__ import annotations

import csv
import io
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, ReportTemplate, Site
from app.services.asset_labels import generate_label_code, qr_payload_for_asset
from app.services.maintenance_schedules import create_schedule


REQUIRED_COLUMNS = {"site_code", "name", "category"}


def _parse_csv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return []
    return [dict(row) for row in reader]


def _find_site(db: Session, tenant_id: UUID, site_code: str) -> Site | None:
    code = site_code.strip()
    site = db.scalar(select(Site).where(Site.tenant_id == tenant_id, Site.name.ilike(code)))
    if site:
        return site
    # Match slug prefix of site name e.g. HQ -> Headquarters
    for s in db.scalars(select(Site).where(Site.tenant_id == tenant_id)).all():
        if _slug_code(s.name) == _slug_code(code):
            return s
    return None


def _slug_code(value: str) -> str:
    import re

    cleaned = re.sub(r"[^A-Za-z0-9]", "", value.upper())
    return cleaned[:8] or "SITE"


def preview_import(db: Session, tenant_id: UUID, content: str) -> dict[str, Any]:
    rows_raw = _parse_csv(content)
    rows_out: list[dict[str, Any]] = []
    valid = 0
    errors = 0
    for i, row in enumerate(rows_raw, start=2):
        errs: list[str] = []
        site_code = (row.get("site_code") or "").strip()
        name = (row.get("name") or "").strip()
        if not site_code:
            errs.append("site_code required")
        if not name:
            errs.append("name required")
        site = None
        if site_code:
            site = _find_site(db, tenant_id, site_code)
            if not site:
                errs.append(f"unknown site_code {site_code}")
        serial = (row.get("serial") or "").strip() or None
        if serial and site:
            dup = db.scalar(
                select(Asset).where(Asset.tenant_id == tenant_id, Asset.site_id == site.id, Asset.serial == serial)
            )
            if dup:
                errs.append("duplicate serial for site")
        template_code = (row.get("template_code") or "").strip()
        if template_code:
            tmpl = db.scalar(
                select(ReportTemplate).where(
                    ReportTemplate.tenant_id == tenant_id, ReportTemplate.code == template_code
                )
            )
            if not tmpl:
                errs.append(f"unknown template_code {template_code}")
        status = "ok" if not errs else "error"
        if status == "ok":
            valid += 1
        else:
            errors += 1
        rows_out.append(
            {
                "row": i,
                "site_code": site_code,
                "name": name,
                "category": (row.get("category") or "general").strip(),
                "serial": serial,
                "status": status,
                "errors": errs,
            }
        )
    return {"valid_count": valid, "error_count": errors, "rows": rows_out}


def commit_import(db: Session, tenant_id: UUID, content: str) -> dict[str, int]:
    preview = preview_import(db, tenant_id, content)
    if preview["error_count"] > 0:
        raise ValueError("VALIDATION_ERRORS")
    created = 0
    skipped = 0
    rows_raw = _parse_csv(content)
    for row in rows_raw:
        site_code = (row.get("site_code") or "").strip()
        site = _find_site(db, tenant_id, site_code)
        if not site:
            skipped += 1
            continue
        serial = (row.get("serial") or "").strip() or None
        if serial:
            existing = db.scalar(
                select(Asset).where(Asset.tenant_id == tenant_id, Asset.site_id == site.id, Asset.serial == serial)
            )
            if existing:
                skipped += 1
                continue
        category = (row.get("category") or "general").strip()
        asset = Asset(
            tenant_id=tenant_id,
            site_id=site.id,
            name=(row.get("name") or "").strip(),
            category=category,
            serial=serial,
            label_code=generate_label_code(db, tenant_id=tenant_id, site_id=site.id, category=category),
        )
        db.add(asset)
        db.flush()
        asset.qr_payload = qr_payload_for_asset(asset.id)
        freq = (row.get("schedule_frequency") or "").strip()
        template_code = (row.get("template_code") or "").strip()
        if freq and template_code:
            tmpl = db.scalar(
                select(ReportTemplate).where(
                    ReportTemplate.tenant_id == tenant_id, ReportTemplate.code == template_code
                )
            )
            if tmpl:
                create_schedule(
                    db,
                    tenant_id=tenant_id,
                    asset_id=asset.id,
                    template_id=tmpl.id,
                    frequency=freq if freq in ("monthly", "quarterly", "yearly", "weekly") else "monthly",
                )
        created += 1
    db.flush()
    return {"created": created, "skipped": skipped}
