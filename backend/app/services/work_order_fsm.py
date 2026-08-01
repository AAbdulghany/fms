"""Work order state machine — transitions, roles, and payload validation."""

from __future__ import annotations

from app.models import ReportStatus, User, UserRole, WorkOrder, WorkOrderStatus
from app.schemas import WorkOrderUpdate

ALLOWED: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.requested: {WorkOrderStatus.created, WorkOrderStatus.declined},
    WorkOrderStatus.declined: set(),
    WorkOrderStatus.created: {WorkOrderStatus.assigned, WorkOrderStatus.cancelled},
    WorkOrderStatus.assigned: {
        WorkOrderStatus.in_progress,
        WorkOrderStatus.on_hold,
        WorkOrderStatus.cancelled,
        WorkOrderStatus.assigned,
    },
    WorkOrderStatus.in_progress: {
        WorkOrderStatus.completed,
        WorkOrderStatus.on_hold,
        WorkOrderStatus.cancelled,
    },
    WorkOrderStatus.on_hold: {WorkOrderStatus.in_progress, WorkOrderStatus.cancelled},
    WorkOrderStatus.completed: {WorkOrderStatus.verified, WorkOrderStatus.cancelled},
    WorkOrderStatus.verified: {WorkOrderStatus.closed, WorkOrderStatus.cancelled},
    WorkOrderStatus.closed: set(),
    WorkOrderStatus.cancelled: set(),
}

TERMINAL_STATUSES = frozenset(
    {WorkOrderStatus.closed, WorkOrderStatus.cancelled, WorkOrderStatus.verified}
)

ADMIN_TRANSITION_ROLES = frozenset(
    {
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.company_engineer,
        UserRole.site_manager,
    }
)


class TransitionError(ValueError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(message or code)


def can_transition(from_s: WorkOrderStatus, to_s: WorkOrderStatus) -> bool:
    if from_s == to_s:
        return True
    return to_s in ALLOWED.get(from_s, set())


def is_terminal(status: WorkOrderStatus) -> bool:
    return status in TERMINAL_STATUSES


def validate_status_transition(
    wo: WorkOrder,
    from_s: WorkOrderStatus,
    to_s: WorkOrderStatus,
    body: WorkOrderUpdate,
    current: User,
) -> None:
    if from_s == to_s:
        return
    if not can_transition(from_s, to_s):
        raise TransitionError("INVALID_TRANSITION")

    role = current.role
    assignee_id = body.assignee_user_id if body.assignee_user_id is not None else wo.assignee_user_id

    if to_s == WorkOrderStatus.assigned and not assignee_id:
        raise TransitionError("ASSIGNEE_REQUIRED")

    if to_s == WorkOrderStatus.on_hold and not (body.hold_reason or "").strip():
        raise TransitionError("HOLD_REASON_REQUIRED")

    if to_s == WorkOrderStatus.cancelled and not (body.cancellation_reason or "").strip():
        raise TransitionError("CANCELLATION_REASON_REQUIRED")

    if to_s == WorkOrderStatus.completed:
        report = wo.report
        if not report or report.status not in (ReportStatus.submitted, ReportStatus.approved):
            raise TransitionError("REPORT_REQUIRED")

    if role == UserRole.technician:
        if wo.assignee_user_id != current.id:
            raise TransitionError("FORBIDDEN")
        if to_s not in {
            WorkOrderStatus.in_progress,
            WorkOrderStatus.on_hold,
            WorkOrderStatus.completed,
        }:
            raise TransitionError("FORBIDDEN")

    elif to_s in {
        WorkOrderStatus.assigned,
        WorkOrderStatus.verified,
        WorkOrderStatus.closed,
        WorkOrderStatus.cancelled,
    } and role not in ADMIN_TRANSITION_ROLES:
        raise TransitionError("FORBIDDEN")


def assert_mutable(wo: WorkOrder, body: WorkOrderUpdate) -> None:
    """Block field edits on terminal work orders."""
    if not is_terminal(wo.status):
        return
    if body.status is not None and body.status != wo.status:
        raise TransitionError("IMMUTABLE")
    mutable_fields = (
        body.title,
        body.description,
        body.urgency,
        body.template_id,
        body.assignee_user_id,
        body.tags,
        body.hold_reason,
        body.cancellation_reason,
    )
    if any(v is not None for v in mutable_fields):
        raise TransitionError("IMMUTABLE")
