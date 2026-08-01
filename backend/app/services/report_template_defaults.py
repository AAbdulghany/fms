"""Resolve tenant default report templates."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReportTemplate


def resolve_default_report_template(db: Session, tenant_id: UUID) -> ReportTemplate | None:
    """Prefer STD-INSP, otherwise the first active template for the tenant."""
    std = db.scalar(
        select(ReportTemplate).where(
            ReportTemplate.tenant_id == tenant_id,
            ReportTemplate.code == "STD-INSP",
            ReportTemplate.is_active.is_(True),
        )
    )
    if std:
        return std
    return db.scalar(
        select(ReportTemplate)
        .where(ReportTemplate.tenant_id == tenant_id, ReportTemplate.is_active.is_(True))
        .order_by(ReportTemplate.name)
        .limit(1)
    )
