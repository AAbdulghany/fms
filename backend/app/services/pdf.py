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


def _invoice_currency_label(invoice: Invoice) -> str:
    return (invoice.currency or "SAR").strip().upper() or "SAR"


def render_invoice_pdf(
    db: Session,
    *,
    invoice: Invoice,
) -> bytes:
    tenant = db.get(Tenant, invoice.tenant_id)
    client = db.get(Client, invoice.client_id)
    wo = db.get(WorkOrder, invoice.work_order_id)
    report = wo.report if wo else None
    db.refresh(invoice)
    line_items = list(invoice.line_items)
    cur = _invoice_currency_label(invoice)

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

    tenant_name = tenant.name if tenant else ""
    title = reshape_text(f"Invoice {invoice.number}")
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(reshape_text(tenant_name), styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    bill_to = client.legal_name if client else ""
    meta_data = [
        [reshape_text("Bill to"), reshape_text(bill_to)],
        [reshape_text("Billing email"), client.billing_email if client else ""],
        [reshape_text("Invoice #"), invoice.number],
        [reshape_text("Issue date"), str(invoice.issued_at.date() if invoice.issued_at else "")],
        [reshape_text("Due date"), str(invoice.due_date or "")],
        [reshape_text("Work order"), wo.title if wo else ""],
        [reshape_text("WO ID"), str(wo.id) if wo else ""],
        [reshape_text("Status"), invoice.status.value],
        [reshape_text("Total (SAR)"), str(invoice.total_sar)],
        [reshape_text("Display currency"), cur],
    ]
    if cur != "SAR":
        meta_data.append(
            [
                reshape_text("Note"),
                reshape_text("Amounts are SAR-denominated; display currency is for labeling only."),
            ]
        )
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

    hdr = [
        [
            reshape_text("Type"),
            reshape_text("Description"),
            "Qty",
            reshape_text("Unit (SAR)"),
            reshape_text("Amount (SAR)"),
        ]
    ]
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
    if report:
        answers = report.answers_json or {}
        summary = str(answers.get("work_summary") or answers.get("summary") or wo.description or "")[:500]
        if summary:
            story.append(Spacer(1, 0.6 * cm))
            story.append(Paragraph(f"<b>{reshape_text('Work performed')}</b>", styles["Heading3"]))
            story.append(Paragraph(reshape_text(summary), styles["Normal"]))
    story.append(Spacer(1, 0.8 * cm))
    story.append(
        Paragraph(
            reshape_text("Payment terms: Net 30. Amounts in SAR unless noted."),
            styles["Normal"],
        )
    )
    doc.build(story)
    return buf.getvalue()


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
    answers: dict[str, Any],
    template_schema: dict[str, Any] = None,
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

    # Custom style for Arabic/Bilingual content
    arabic_style = ParagraphStyle(
        "ArabicStyle",
        parent=styles["Normal"],
        fontName="Helvetica", # In real prod, this would be a registered Arabic font like NotoSans
        alignment=2, # Right aligned
        fontSize=10,
    )

    story: list[Any] = []

    # Branded Header
    title_text = reshape_text("Maintenance Report")
    story.append(Paragraph(f"<center><b style='font-size:18pt'>{title_text}</b></center>", styles["Title"]))
    story.append(Spacer(1, 0.5 * cm))

    # Report Meta Information Table
    meta_data = [
        [reshape_text("Tenant:"), reshape_text(tenant_name), reshape_text("Work Order:"), reshape_text(work_order_title)],
    ]
    t_meta = Table(meta_data, colWidths=[3 * cm, 6 * cm, 3 * cm, 6 * cm])
    t_meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (0, 0), (-1, -1), "LEFT")]))
    story.append(t_meta)
    story.append(Spacer(1, 1 * cm))

    # Process Sections from Schema
    sections = template_schema.get("sections", []) if template_schema else []

    if not sections:
        # Fallback to raw answers if no schema provided
        for k, v in (answers or {}).items():
            key = reshape_text(str(k))
            val = reshape_text(str(v))
            story.append(Paragraph(f"<b>{key}</b>: {val}", styles["Normal"]))
            story.append(Spacer(1, 0.2 * cm))
    else:
        for sec in sections:
            sec_title = reshape_text(sec.get("title", "Section"))
            story.append(Paragraph(f"<b>{sec_title}</b>", ParagraphStyle("SecTitle", parent=styles["Normal"], fontSize=12, spaceAfter=6)))
            story.append(Spacer(1, 0.2 * cm))

            for f in sec.get("fields", []):
                fid = f.get("id")
                label = reshape_text(f.get("label", fid))
                val = answers.get(fid)

                if val is None or val == "":
                    continue

                # Render Label
                story.append(Paragraph(f"<b>{label}</b>", styles["Normal"]))

                # Handle different value types
                if f.get("type") == "photo":
                    # Embed Photos
                    photos = val if isinstance(val, list) else [val]
                    # We use a table to layout photos side-by-side
                    photo_row = []
                    for photo_url in photos:
                        try:
                            # In a real system, we'd fetch the S3 image into BytesIO
                            # Since we don't have a real S3 client here, we'll place a placeholder
                            # or a simulated image if the URL is valid.
                            # For implementation, we'll assume we have a helper that gets the bytes.
                            img = Image(photo_url, width=4 * cm, height=3 * cm)
                            photo_row.append(img)
                        except Exception:
                            photo_row.append(Paragraph("[Photo Unavailable]", styles["Normal"]))

                    if photo_row:
                        t_photos = Table([photo_row], colWidths=[4 * cm] * len(photo_row))
                        t_photos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
                        story.append(t_photos)
                        story.append(Spacer(1, 0.3 * cm))

                elif f.get("type") == "signature":
                    # Render Signature
                    try:
                        sig_img = Image(val, width=5 * cm, height=2 * cm)
                        story.append(sig_img)
                    except Exception:
                        story.append(Paragraph("[Signature Image Unavailable]", styles["Normal"]))
                    story.append(Spacer(1, 0.3 * cm))

                else:
                    # Regular text/number
                    val_text = reshape_text(str(val))
                    story.append(Paragraph(val_text, styles["Normal"]))
                    story.append(Spacer(1, 0.2 * cm))

            story.append(Spacer(1, 0.5 * cm))

    doc.build(story)
    return buf.getvalue()
