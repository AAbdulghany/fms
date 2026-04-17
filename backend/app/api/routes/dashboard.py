"""P2-F6: Role-aware dashboard aggregates."""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import (
    Asset,
    AssetLifecycleStatus,
    Client,
    Invoice,
    InvoiceStatus,
    Site,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderStatus,
)
from app.schemas import DashboardSummaryOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
def dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> DashboardSummaryOut:
    tid = current.tenant_id
    role = current.role.value if hasattr(current.role, "value") else str(current.role)

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    out = DashboardSummaryOut(role=role, open_work_orders=0, completed_this_week=0)

    # --- Technician: assigned work only ---
    if current.role == UserRole.technician:
        my_open = db.scalar(
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tid,
                WorkOrder.assignee_user_id == current.id,
                WorkOrder.status.in_(
                    [
                        WorkOrderStatus.assigned,
                        WorkOrderStatus.in_progress,
                    ]
                ),
            )
        )
        my_prog = db.scalar(
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tid,
                WorkOrder.assignee_user_id == current.id,
                WorkOrder.status == WorkOrderStatus.in_progress,
            )
        )
        done_week = db.scalar(
            select(func.count())
            .select_from(WorkOrder)
            .where(
                WorkOrder.tenant_id == tid,
                WorkOrder.assignee_user_id == current.id,
                WorkOrder.status == WorkOrderStatus.completed,
                WorkOrder.closed_at.isnot(None),
                WorkOrder.closed_at >= week_ago,
            )
        )
        out.my_assigned_open = int(my_open or 0)
        out.my_in_progress = int(my_prog or 0)
        out.completed_this_week = int(done_week or 0)
        out.open_work_orders = int(
            db.scalar(
                select(func.count())
                .select_from(WorkOrder)
                .where(
                    WorkOrder.tenant_id == tid,
                    WorkOrder.assignee_user_id == current.id,
                    WorkOrder.status.notin_([WorkOrderStatus.closed, WorkOrderStatus.cancelled]),
                )
            )
            or 0
        )
        return out

    # --- Client admin: scope to client ---
    client_filter = None
    if current.role == UserRole.client_admin and current.client_id:
        client_filter = current.client_id

    # --- Site manager: scope to sites ---
    site_ids: list | None = None
    if current.role == UserRole.site_manager:
        site_ids = list(
            db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        )
        if not site_ids:
            out.open_work_orders = 0
            out.completed_this_week = 0
            return out

    # Counts
    cq = select(func.count()).select_from(Client).where(Client.tenant_id == tid)
    if client_filter:
        cq = cq.where(Client.id == client_filter)
    out.clients_count = int(db.scalar(cq) or 0)

    sq = select(func.count()).select_from(Site).where(Site.tenant_id == tid)
    if client_filter:
        sq = sq.where(Site.client_id == client_filter)
    if site_ids is not None:
        sq = sq.where(Site.id.in_(site_ids))
    out.sites_count = int(db.scalar(sq) or 0)

    aq = select(func.count()).select_from(Asset).where(Asset.tenant_id == tid)
    if site_ids is not None:
        aq = aq.where(Asset.site_id.in_(site_ids))
    elif client_filter:
        sub = select(Site.id).where(Site.client_id == client_filter)
        aq = aq.where(Asset.site_id.in_(sub))
    out.assets_count = int(db.scalar(aq) or 0)

    wq = select(func.count()).select_from(WorkOrder).where(WorkOrder.tenant_id == tid)
    wq = wq.where(WorkOrder.status.notin_([WorkOrderStatus.closed, WorkOrderStatus.cancelled]))
    if client_filter:
        wq = wq.where(WorkOrder.client_id == client_filter)
    if site_ids is not None:
        wq = wq.where(WorkOrder.site_id.in_(site_ids))
    out.open_work_orders = int(db.scalar(wq) or 0)

    tech_q = select(func.count()).select_from(User).where(
        User.tenant_id == tid,
        User.role == UserRole.technician,
        User.is_active.is_(True),
    )
    out.technicians_count = int(db.scalar(tech_q) or 0)

    inv_q = select(func.count()).select_from(Invoice).where(
        Invoice.tenant_id == tid,
        Invoice.status == InvoiceStatus.draft,
    )
    if client_filter:
        inv_q = inv_q.where(Invoice.client_id == client_filter)
    out.pending_invoices_draft = int(db.scalar(inv_q) or 0)

    comp_q = select(func.count()).select_from(WorkOrder).where(
        WorkOrder.tenant_id == tid,
        WorkOrder.status == WorkOrderStatus.completed,
        WorkOrder.closed_at.isnot(None),
        WorkOrder.closed_at >= week_ago,
    )
    if client_filter:
        comp_q = comp_q.where(WorkOrder.client_id == client_filter)
    if site_ids is not None:
        comp_q = comp_q.where(WorkOrder.site_id.in_(site_ids))
    out.completed_this_week = int(db.scalar(comp_q) or 0)

    eol_q = select(func.count()).select_from(Asset).where(
        Asset.tenant_id == tid,
        Asset.lifecycle_status.in_([AssetLifecycleStatus.end_of_life, AssetLifecycleStatus.warning]),
    )
    if site_ids is not None:
        eol_q = eol_q.where(Asset.site_id.in_(site_ids))
    elif client_filter:
        sub = select(Site.id).where(Site.client_id == client_filter)
        eol_q = eol_q.where(Asset.site_id.in_(sub))
    out.assets_at_eol = int(db.scalar(eol_q) or 0)

    return out
