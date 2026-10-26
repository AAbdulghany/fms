"""Background invoice PDF + SMTP delivery (P18).

Runs after the HTTP response so workers are not blocked on ReportLab / SMTP.
Uses a fresh SessionLocal — never the request session.
"""

from __future__ import annotations

import logging
from uuid import UUID

from app.database import SessionLocal
from app.models import Client, Invoice
from app.services.email import send_invoice_email
from app.services.pdf import render_invoice_pdf

logger = logging.getLogger(__name__)


def deliver_invoice_email(
    invoice_id: UUID,
    to_email: str,
    client_name: str = "",
) -> None:
    """Render invoice PDF and send email off the request path."""
    db = SessionLocal()
    try:
        inv = db.get(Invoice, invoice_id)
        if inv is None:
            logger.warning("deliver_invoice_email: invoice %s not found", invoice_id)
            return
        _ = inv.line_items  # ensure loaded for PDF
        if not client_name:
            client = db.get(Client, inv.client_id)
            client_name = client.legal_name if client else ""
        pdf_bytes = render_invoice_pdf(db, invoice=inv)
        # Release DB before SMTP — PDF data is already in memory.
        db.expire_all()
        send_invoice_email(
            to_email,
            inv.number,
            pdf_bytes,
            client_name=client_name,
        )
    except Exception:
        logger.exception("deliver_invoice_email failed for invoice %s", invoice_id)
    finally:
        db.close()
