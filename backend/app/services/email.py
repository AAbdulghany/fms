"""Transactional email helpers (Phase 3). Uses SMTP when configured; otherwise logs only."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST"))


def _send_smtp(
    to_email: str,
    subject: str,
    body_text: str,
    attachment: tuple[str, bytes, str] | None = None,
) -> bool:
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("FROM_EMAIL", "notifications@fms.local")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.set_content(body_text)
    if attachment:
        filename, data, mime = attachment
        msg.add_attachment(data, maintype=mime.split("/")[0], subtype=mime.split("/")[1], filename=filename)
    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            if user:
                smtp.login(user, password)
            smtp.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001
        logger.warning("SMTP send failed: %s", e)
        return False


def send_invoice_email(
    to_email: str,
    invoice_number: str,
    pdf_bytes: bytes,
    client_name: str = "",
) -> None:
    subject = f"Invoice {invoice_number}"
    body = (
        f"Please find attached invoice {invoice_number}.\n\n"
        f"Client: {client_name}\n"
    )
    attachment = (f"invoice-{invoice_number}.pdf", pdf_bytes, "application/pdf")
    if _smtp_configured():
        _send_smtp(to_email, subject, body, attachment=attachment)
    else:
        logger.info(
            "Email (no SMTP): to=%s subject=%s attachment=%d bytes",
            to_email,
            subject,
            len(pdf_bytes),
        )


def send_work_order_assigned_email(to_email: str, title: str, work_order_id: str) -> None:
    subject = f"New work order assigned: {title}"
    body = (
        f"You have been assigned a work order.\n\n"
        f"Title: {title}\n"
        f"ID: {work_order_id}\n"
    )
    if _smtp_configured():
        _send_smtp(to_email, subject, body)
    else:
        logger.info("Email (no SMTP): to=%s subject=%s", to_email, subject)


def send_work_order_status_email(to_email: str, title: str, old_status: str, new_status: str) -> None:
    subject = f"Work order updated: {title}"
    body = f"Status changed: {old_status} → {new_status}\n\nTitle: {title}\n"
    if _smtp_configured():
        _send_smtp(to_email, subject, body)
    else:
        logger.info("Email (no SMTP): to=%s subject=%s", to_email, subject)
