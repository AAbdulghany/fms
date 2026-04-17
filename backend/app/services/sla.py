from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkOrder, Urgency, Tenant

class SLAService:
    # Default SLA policies (in hours) if not defined in tenant settings
    DEFAULT_POLICIES = {
        Urgency.emergency: {"response": 2, "resolution": 24},
        Urgency.urgent: {"response": 4, "resolution": 72},
        Urgency.normal: {"response": 24, "resolution": 168}, # 1 week
    }

    @staticmethod
    def calculate_due_dates(tenant: Tenant, urgency: Urgency) -> tuple[datetime, datetime]:
        """
        Calculates the SLA response and resolution due dates.
        Checks tenant settings first, then falls back to defaults.
        """
        settings = tenant.settings_json or {}
        sla_settings = settings.get("sla_policies", {})
        
        # Get policy for specific urgency
        policy = sla_settings.get(urgency.value) or SLAService.DEFAULT_POLICIES.get(urgency)
        
        now = datetime.now(timezone.utc)
        response_due = now + timedelta(hours=policy["response"])
        resolution_due = now + timedelta(hours=policy["resolution"])
        
        return response_due, resolution_due

    async def check_for_breaches(self, db: Session, notification_service):
        """
        Scans for work orders that are approaching or have passed their SLA limits.
        This would be called by a background cron job (Celery/RQ).
        """
        now = datetime.now(timezone.utc)
        
        # 1. Find breached orders (Resolution overdue and not completed)
        breached_stmt = select(WorkOrder).where(
            WorkOrder.sla_resolution_due_at < now,
            WorkOrder.status != "completed",
            WorkOrder.status != "closed"
        )
        breached_orders = db.scalars(breached_stmt).all()
        
        for wo in breached_orders:
            # Trigger Breach Notification
            from app.services.notifications import NotificationEvent
            await notification_service.notify(
                wo.assignee_user, 
                NotificationEvent.SLA_BREACH, 
                {"title": wo.title}
            )

        # 2. Find warning orders (Within 20% of the SLA limit)
        # (Implementation similar to above but checking a threshold)

sla_service = SLAService()
