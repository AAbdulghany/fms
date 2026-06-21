from typing import Any, Optional
import logging
from uuid import UUID

# In a real production app, we would use:
# import smtplib
# from firebase_admin import messaging

logger = logging.getLogger(__name__)

class NotificationEvent:
    NEW_WORK_ORDER = "new_work_order"
    SLA_WARNING = "sla_warning"
    SLA_BREACH = "sla_breach"
    WORK_COMPLETED = "work_completed"
    REPORT_READY = "report_ready"
    INVOICE_GENERATED = "invoice_generated"
    PAYMENT_OVERDUE = "payment_overdue"

class NotificationService:
    def __init__(self, smtp_settings: Optional[dict] = None, fcm_settings: Optional[dict] = None):
        self.smtp_settings = smtp_settings
        self.fcm_settings = fcm_settings

    async def send_email(self, recipient_email: str, subject: str, body: str, attachment_path: Optional[str] = None):
        """Sends a transactional email via SMTP."""
        if not self.smtp_settings:
            logger.warning(f"SMTP not configured. Skipping email to {recipient_email}")
            return False
        
        # Logic for smtplib / SendGrid / AWS SES would go here
        logger.info(f"Email sent to {recipient_email}: {subject}")
        return True

    async def send_push(self, user_fcm_token: str, title: str, body: str, data: Optional[dict] = None):
        """Sends a push notification via Firebase Cloud Messaging."""
        if not self.fcm_settings:
            logger.warning("FCM not configured. Skipping push notification.")
            return False
            
        # Logic for firebase_admin.messaging.send() would go here
        logger.info(f"Push sent to {user_fcm_token}: {title}")
        return True

    async def notify(self, user, event_type: str, context: dict):
        """
        The main entry point for notifications.
        Determines channels based on event type and user preferences.
        """
        # 1. Resolve content based on event_type (i18n would be applied here)
        subject, body = self._get_content(event_type, context)
        
        # 2. Send via Email
        if user.email:
            await self.send_email(user.email, subject, body)
            
        # 3. Send via Push (if token available)
        # Assuming User model has a fcm_token field in metadata_json
        token = user.metadata_json.get("fcm_token") if user.metadata_json else None
        if token:
            await self.send_push(token, subject, body, context)

    def _get_content(self, event_type: str, context: dict) -> tuple[str, str]:
        # Simple mapping for MVP. In production, this uses translation files.
        mapping = {
            NotificationEvent.NEW_WORK_ORDER: ("New Work Order Assigned", "You have been assigned to a new work order: {title}"),
            NotificationEvent.SLA_WARNING: ("SLA Warning", "Work order {title} is approaching its SLA limit!"),
            NotificationEvent.SLA_BREACH: ("SLA BREACH", "Urgent: Work order {title} has breached its SLA!"),
            NotificationEvent.WORK_COMPLETED: ("Work Completed", "The work order {title} has been marked as completed."),
            NotificationEvent.REPORT_READY: ("Report Ready", "The maintenance report for {title} is now available."),
            NotificationEvent.INVOICE_GENERATED: ("Invoice Issued", "A new invoice {number} has been generated."),
            NotificationEvent.PAYMENT_OVERDUE: ("Payment Overdue", "Invoice {number} is now overdue."),
        }
        
        template = mapping.get(event_type, ("Notification", "You have a new update in Orbit"))
        subject = template[0].format(**context)
        body = template[1].format(**context)
        return subject, body

# Singleton instance for the app
notification_service = NotificationService()
