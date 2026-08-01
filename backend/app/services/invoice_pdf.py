"""Branded invoice PDF — layout aligned with maintenance report template."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import Client, Invoice, Tenant, WorkOrder
from app.services.billing import extract_invoice_charges
from app.services.maintenance_report_pdf import (
    GRID_COL_WIDTH,
    PAGE_CONTENT_WIDTH,
    _p,
    _panel_table,
)
from app.services.pdf_brand import NEUTRAL_100, NEUTRAL_700, PRIMARY_500
from app.services.pdf_fonts import ensure_pdf_fonts
from app.services.platform_bootstrap import DEFAULT_BRANDING


def _money(amount: Any, currency: str) -> str:
    cur = (currency or "SAR").upper()
    try:
        val = Decimal(str(amount))
    except Exception:
        val = Decimal("0")
    return f"{cur} {val:,.2f}"


def _meta_str(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    s = str(value).strip()
    return s if s else "—"


def render_invoice_pdf_branded(db: Session, *, invoice: Invoice) -> bytes:
    tenant = db.get(Tenant, invoice.tenant_id)
    client = db.get(Client, invoice.client_id)
    wo = db.get(WorkOrder, invoice.work_order_id)
    db.refresh(invoice)
    line_items = list(invoice.line_items)
    meta = dict(invoice.metadata_json or {})
    cur = (invoice.currency or "SAR").strip().upper() or "SAR"

    billing_email = (meta.get("billing_email") or (client.billing_email if client else "") or "").strip()
    notes = (meta.get("notes") or "").strip()
    wo_title = (meta.get("work_order_title") or (wo.title if wo else "") or "").strip()
    client_name = client.legal_name if client else ""
    charges = extract_invoice_charges(invoice)
    labor_hours = charges["labor_hours"]
    labor_rate = charges["labor_rate_sar"]
    labor_amount = charges["labor_amount_sar"]
    service_fee = charges["service_fee_sar"]

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    base = getSampleStyleSheet()
    font_name = ensure_pdf_fonts()
    styles = {
        "title": ParagraphStyle(
            "InvTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=14,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "InvSub",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=TA_LEFT,
        ),
        "brand": ParagraphStyle(
            "InvBrand",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=11,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=TA_LEFT,
        ),
        "panel_title": ParagraphStyle(
            "InvPT",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "InvPL",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=TA_LEFT,
        ),
        "value": ParagraphStyle(
            "InvPV",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            alignment=TA_LEFT,
        ),
        "value_wrap": ParagraphStyle(
            "InvPVW",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            alignment=TA_LEFT,
            leading=11,
            wordWrap="CJK",
        ),
        "section": ParagraphStyle(
            "InvSec",
            parent=base["Heading3"],
            fontName=font_name,
            fontSize=11,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "InvBody",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            alignment=TA_LEFT,
            leading=11,
            wordWrap="CJK",
        ),
    }

    platform = DEFAULT_BRANDING.get("company_name", "Orbit Software")
    tenant_name = tenant.name if tenant else ""
    story: list[Any] = []

    header = Table(
        [
            [
                Table(
                    [[_p(platform, styles["brand"])], [_p(tenant_name, styles["subtitle"])]],
                    colWidths=[GRID_COL_WIDTH],
                ),
                Table(
                    [
                        [_p("Invoice / فاتورة", styles["title"])],
                        [_p(f"Invoice #{invoice.number}", styles["subtitle"])],
                    ],
                    colWidths=[GRID_COL_WIDTH],
                ),
            ]
        ],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LINEBELOW", (0, 0), (-1, -1), 2, colors.HexColor(PRIMARY_500)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, 0.4 * cm))

    row1 = Table(
        [
            [
                _panel_table(
                    "Bill to",
                    [
                        ("Client", client_name),
                        ("Billing email", billing_email, True),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
                _panel_table(
                    "Invoice details",
                    [
                        ("Issue date", _meta_str(invoice.issued_at)),
                        ("Due date", _meta_str(invoice.due_date)),
                        ("Currency", cur),
                        ("Status", invoice.status.value),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
            ]
        ],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
    )
    row1.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(row1)
    story.append(Spacer(1, 0.25 * cm))

    row2 = Table(
        [
            [
                _panel_table(
                    "Work order",
                    [("Reference", wo_title or "—")],
                    styles,
                    GRID_COL_WIDTH,
                ),
                _panel_table(
                    "Totals",
                    [
                        ("Subtotal", _money(invoice.subtotal_sar, cur)),
                        ("Tax", _money(invoice.tax_sar, cur)),
                        ("Total", _money(invoice.total_sar, cur)),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
            ]
        ],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
    )
    row2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(row2)
    story.append(Spacer(1, 0.25 * cm))

    charge_rows: list[tuple[str, str]] = []
    if labor_hours > 0 and labor_rate > 0:
        charge_rows.append(
            (
                "Labor",
                f"{labor_hours} h × {_money(labor_rate, cur)} = {_money(labor_amount, cur)}",
            )
        )
    elif labor_amount > 0:
        charge_rows.append(("Labor", _money(labor_amount, cur)))
    if service_fee > 0:
        charge_rows.append(("Service fee", _money(service_fee, cur)))
    if charge_rows:
        story.append(
            _panel_table("Charges breakdown", charge_rows, styles, PAGE_CONTENT_WIDTH)
        )
        story.append(Spacer(1, 0.25 * cm))

    story.append(Spacer(1, 0.15 * cm))

    story.append(_p("Line items", styles["section"]))
    story.append(Spacer(1, 0.15 * cm))
    table_data = [
        [
            _p("Description", styles["label"]),
            _p("Qty", styles["label"]),
            _p(f"Unit ({cur})", styles["label"]),
            _p(f"Amount ({cur})", styles["label"]),
        ]
    ]
    for li in line_items:
        table_data.append(
            [
                _p(li.description[:120], styles["body"]),
                _p(str(li.quantity), styles["value"]),
                _p(str(li.unit_price_sar), styles["value"]),
                _p(str(li.amount_sar), styles["value"]),
            ]
        )
    items_table = Table(table_data, colWidths=[8.5 * cm, 2.5 * cm, 3 * cm, 3 * cm])
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_500)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor(NEUTRAL_100)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(NEUTRAL_100)]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(items_table)

    story.append(Spacer(1, 0.35 * cm))
    story.append(_p("Notes", styles["section"]))
    story.append(Spacer(1, 0.1 * cm))
    notes_box = Table([[ _p(notes or "—", styles["body"]) ]], colWidths=[PAGE_CONTENT_WIDTH])
    notes_box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(NEUTRAL_100), None, (3, 3)), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    story.append(notes_box)

    story.append(Spacer(1, 0.3 * cm))
    story.append(_p(DEFAULT_BRANDING.get("copyright_watermark", f"© {platform}"), styles["subtitle"]))

    doc.build(story)
    return buf.getvalue()
