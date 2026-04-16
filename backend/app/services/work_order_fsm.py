from app.models import WorkOrderStatus

ALLOWED: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.created: {WorkOrderStatus.assigned, WorkOrderStatus.cancelled},
    WorkOrderStatus.assigned: {
        WorkOrderStatus.in_progress,
        WorkOrderStatus.on_hold,
        WorkOrderStatus.cancelled,
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


def can_transition(from_s: WorkOrderStatus, to_s: WorkOrderStatus) -> bool:
    return to_s in ALLOWED.get(from_s, set())
