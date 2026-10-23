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


def render_asset_label_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
    design: str | None = None,
) -> bytes:
    """A2 sticker PDF — Design A (square) or C (field tag); size configurable in mm."""
    from app.services.asset_label_sticker import render_asset_sticker_pdf

    return render_asset_sticker_pdf(
        asset, client_name=client_name, size_mm=size_mm, design=design
    )


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
