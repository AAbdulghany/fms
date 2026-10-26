"""Background maintenance-report PDF export (P18).

Draft save / submit schedule this after commit so the request returns quickly.
Download endpoints still regenerate on demand.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import MaintenanceReport, User, WorkOrder

logger = logging.getLogger(__name__)


def export_maintenance_report_pdf(
    work_order_id: UUID,
    report_id: UUID,
    actor_user_id: UUID,
    pdf_lang: str | None = None,
) -> None:
    """Regenerate and store the maintenance report PDF in a fresh session."""
    from app.domains.work_orders._common import _sync_maintenance_report_pdf_export

    db = SessionLocal()
    try:
        actor = db.get(User, actor_user_id)
        if actor is None:
            logger.warning("export_maintenance_report_pdf: user %s missing", actor_user_id)
            return
        report = db.get(MaintenanceReport, report_id)
        if report is None or report.work_order_id != work_order_id:
            logger.warning("export_maintenance_report_pdf: report %s missing", report_id)
            return
        wo = db.scalars(
            select(WorkOrder)
            .where(WorkOrder.id == work_order_id)
            .options(
                joinedload(WorkOrder.site),
                joinedload(WorkOrder.asset),
                joinedload(WorkOrder.assignee_user),
                joinedload(WorkOrder.creator_user),
                joinedload(WorkOrder.client),
                joinedload(WorkOrder.documents),
            )
        ).first()
        if wo is None:
            logger.warning("export_maintenance_report_pdf: WO %s missing", work_order_id)
            return
        _sync_maintenance_report_pdf_export(
            db, wo=wo, report=report, current=actor, pdf_lang=pdf_lang
        )
        db.commit()
    except Exception:
        logger.exception(
            "export_maintenance_report_pdf failed wo=%s report=%s",
            work_order_id,
            report_id,
        )
        db.rollback()
    finally:
        db.close()
