from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image
from sqlalchemy.orm import Session

from app.models import Asset, Client, Invoice, Tenant, WorkOrder
from app.services.arabic_utils import reshape_text
from app.services.pdf_fonts import ensure_pdf_fonts


def _invoice_currency_label(invoice: Invoice) -> str:
    return (invoice.currency or "SAR").strip().upper() or "SAR"


def render_invoice_pdf(
    db: Session,
    *,
    invoice: Invoice,
) -> bytes:
    from app.services.invoice_pdf import render_invoice_pdf_branded

    return render_invoice_pdf_branded(db, invoice=invoice)


def render_asset_label_pdf(asset: Asset) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story: list[Any] = []
    label = asset.label_code or str(asset.id)[:8]
    story.append(Paragraph(f"<b>{reshape_text(label)}</b>", styles["Title"]))
    story.append(Paragraph(reshape_text(asset.name), styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    if asset.qr_payload:
        story.append(Paragraph(reshape_text(f"QR: {asset.qr_payload}"), styles["Normal"]))
    active = [s for s in (asset.schedules or []) if s.is_active]
    if active:
        next_due = min(s.next_due_at for s in active)
        story.append(Paragraph(reshape_text(f"Next maintenance: {next_due.date()}"), styles["Normal"]))
    doc.build(story)
    return buf.getvalue()


def render_report_summary_pdf(
    *,
    tenant_name: str,
    work_order_title: str,
    work_order_id: str = "",
    answers: dict[str, Any],
    template_schema: dict[str, Any] | None = None,
    platform_company_name: str = "Orbit Software",
    platform_copyright: str = "",
    lang: str = "ar",
    dir_: str | None = None,
) -> bytes:
    from app.services.maintenance_report_pdf import render_maintenance_report_pdf

    return render_maintenance_report_pdf(
        tenant_name=tenant_name,
        work_order_title=work_order_title,
        work_order_id=work_order_id,
        answers=answers or {},
        platform_company_name=platform_company_name,
        platform_copyright=platform_copyright,
        lang=lang,
        dir_=dir_,
    )
