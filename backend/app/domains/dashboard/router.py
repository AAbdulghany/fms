"""P2-F6: Role-aware dashboard aggregates.

Perf P5: collapse same-table COUNTs into FILTER aggregates (fewer round-trips).
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

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

_CLOSED = (WorkOrderStatus.closed, WorkOrderStatus.cancelled)
_OVERDUE_EXCLUDED = (
    WorkOrderStatus.closed,
    WorkOrderStatus.cancelled,
    WorkOrderStatus.completed,
    WorkOrderStatus.verified,
)
_EOL_STATUSES = (AssetLifecycleStatus.end_of_life, AssetLifecycleStatus.warning)


def _wo_agg(
    db: Session,
    *,
    tenant_id: UUID,
    week_ago: datetime,
    now: datetime,
    assignee_user_id: UUID | None = None,
    client_id: UUID | None = None,
    site_ids: list[UUID] | None = None,
) -> tuple[int, int, int, int, int]:
    """One scan of work_orders → open, in_progress, overdue, completed_week, assigned_open."""
    filters = [WorkOrder.tenant_id == tenant_id]
    if assignee_user_id is not None:
        filters.append(WorkOrder.assignee_user_id == assignee_user_id)
    if client_id is not None:
        filters.append(WorkOrder.client_id == client_id)
    if site_ids is not None:
        filters.append(WorkOrder.site_id.in_(site_ids))

    row = db.execute(
        select(
            func.count()
            .filter(WorkOrder.status.notin_(_CLOSED))
            .label("open_wo"),
            func.count()
            .filter(WorkOrder.status == WorkOrderStatus.in_progress)
            .label("in_progress"),
            func.count()
            .filter(
                WorkOrder.due_at.isnot(None),
                WorkOrder.due_at < now,
                WorkOrder.status.notin_(_OVERDUE_EXCLUDED),
            )
            .label("overdue"),
            func.count()
            .filter(
                WorkOrder.status == WorkOrderStatus.completed,
                WorkOrder.closed_at.isnot(None),
                WorkOrder.closed_at >= week_ago,
            )
            .label("completed_week"),
            func.count()
            .filter(
                WorkOrder.status.in_(
                    [WorkOrderStatus.assigned, WorkOrderStatus.in_progress]
                )
            )
            .label("assigned_open"),
        ).where(*filters)
    ).one()
    return (
        int(row.open_wo or 0),
        int(row.in_progress or 0),
        int(row.overdue or 0),
        int(row.completed_week or 0),
        int(row.assigned_open or 0),
    )


def _asset_agg(
    db: Session,
    *,
    tenant_id: UUID,
    client_id: UUID | None = None,
    site_ids: list[UUID] | None = None,
) -> tuple[int, int]:
    """One scan of assets → total, at_eol_or_warning."""
    filters = [Asset.tenant_id == tenant_id]
    if site_ids is not None:
        filters.append(Asset.site_id.in_(site_ids))
    elif client_id is not None:
        filters.append(Asset.site_id.in_(select(Site.id).where(Site.client_id == client_id)))

    row = db.execute(
        select(
            func.count().label("total"),
            func.count()
            .filter(Asset.lifecycle_status.in_(_EOL_STATUSES))
            .label("at_eol"),
        ).where(*filters)
    ).one()
    return int(row.total or 0), int(row.at_eol or 0)


@router.get("/summary", response_model=DashboardSummaryOut)
def dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> DashboardSummaryOut:
    tid = current.tenant_id
    role = current.role.value if hasattr(current.role, "value") else str(current.role)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    out = DashboardSummaryOut(role=role, open_work_orders=0, completed_this_week=0)

    # --- Technician: assigned work only (1 WO aggregate query) ---
    if current.role == UserRole.technician:
        open_wo, in_prog, overdue, done_week, assigned_open = _wo_agg(
            db,
            tenant_id=tid,
            week_ago=week_ago,
            now=now,
            assignee_user_id=current.id,
        )
        out.my_assigned_open = assigned_open
        out.my_in_progress = in_prog
        out.in_progress_count = in_prog
        out.completed_this_week = done_week
        out.open_work_orders = open_wo
        out.overdue_count = overdue
        return out

    # --- Client admin: scope to client ---
    client_filter: UUID | None = None
    if current.role == UserRole.client_admin and current.client_id:
        client_filter = current.client_id

    # --- Site manager: scope to sites ---
    site_ids: list[UUID] | None = None
    if current.role == UserRole.site_manager:
        site_ids = list(
            db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()
        )
        if not site_ids:
            out.open_work_orders = 0
            out.completed_this_week = 0
            return out

    cq = select(func.count()).select_from(Client).where(
        Client.tenant_id == tid,
        Client.status == "active",
    )
    if client_filter:
        cq = cq.where(Client.id == client_filter)
    out.clients_count = int(db.scalar(cq) or 0)

    sq = select(func.count()).select_from(Site).where(Site.tenant_id == tid)
    if client_filter:
        sq = sq.where(Site.client_id == client_filter)
    if site_ids is not None:
        sq = sq.where(Site.id.in_(site_ids))
    out.sites_count = int(db.scalar(sq) or 0)

    assets_total, assets_eol = _asset_agg(
        db, tenant_id=tid, client_id=client_filter, site_ids=site_ids
    )
    out.assets_count = assets_total
    out.assets_at_eol = assets_eol

    open_wo, in_prog, overdue, done_week, _ = _wo_agg(
        db,
        tenant_id=tid,
        week_ago=week_ago,
        now=now,
        client_id=client_filter,
        site_ids=site_ids,
    )
    out.open_work_orders = open_wo
    out.in_progress_count = in_prog
    out.overdue_count = overdue
    out.completed_this_week = done_week

    out.operational_users_count = int(
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.tenant_id == tid,
                User.is_active.is_(True),
                User.is_platform_admin.is_(False),
                User.role.notin_([UserRole.super_user, UserRole.sw_dev]),
            )
        )
        or 0
    )

    inv_q = select(func.count()).select_from(Invoice).where(
        Invoice.tenant_id == tid,
        Invoice.status == InvoiceStatus.draft,
    )
    if client_filter:
        inv_q = inv_q.where(Invoice.client_id == client_filter)
    out.pending_invoices_draft = int(db.scalar(inv_q) or 0)

    return out
