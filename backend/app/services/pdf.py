from io import BytesIO
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.models import Client, Invoice, Tenant, WorkOrder
from app.services.arabic_utils import reshape_text

def render_invoice_pdf(
    db: Session,
    *,
    invoice: Invoice,
) -> bytes:
    tenant = db.get(Tenant, invoice.tenant_id)
    client = db.get(Client, invoice.client_id)
    wo = db.get(WorkOrder, invoice.work_order_id)
    db.refresh(invoice)
    line_items = list(invoice.line_items)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = []

    # Apply reshaping to all dynamic text
    title = reshape_text(f"Invoice {invoice.number}")
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    meta_data = [
        [reshape_text("Tenant"), tenant.name if tenant else ""],
        [reshape_text("Client"), client.legal_name if client else ""],
        [reshape_text("Work order"), str(wo.id) if wo else ""],
        [reshape_text("Status"), invoice.status.value],
        [reshape_text("Total (SAR)"), str(invoice.total_sar)],
    ]
    t_meta = Table(meta_data, colWidths=[4 * cm, 12 * cm])
    t_meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_meta)
    story.append(Spacer(1, 0.8 * cm))

    hdr = [[reshape_text("Type"), reshape_text("Description"), "Qty", "Unit", "Amount"]]
    rows = hdr + [
        [
            reshape_text(li.line_type),
            reshape_text(li.description[:80]),
            str(li.quantity),
            str(li.unit_price_sar),
            str(li.amount_sar),
        ]
        for li in line_items
    ]
    t = Table(rows, colWidths=[2 * cm, 7 * cm, 2 * cm, 2.5 * cm, 2.5 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d7c8c")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f4")]),
            ]
        )
    )
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def render_report_summary_pdf(
    *,
    tenant_name: str,
    work_order_title: str,
    answers: dict[str, Any],
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = []
    
    # Apply reshaping
    title = reshape_text(f"Maintenance report")
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Paragraph(f"{reshape_text('Tenant')}: {reshape_text(tenant_name)}", styles["Normal"]))
    story.append(Paragraph(f"{reshape_text('Work order')}: {reshape_text(work_order_title)}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))
    
    for k, v in (answers or {}).items():
        key = reshape_text(str(k))
        val = reshape_text(str(v))
        story.append(Paragraph(f"<b>{key}</b>: {val}", styles["Normal"]))
        
    doc.build(story)
    return buf.getvalue()
