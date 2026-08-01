"""Enterprise maintenance report PDF — HTML template + ReportLab renderer."""

from __future__ import annotations

import base64
import html
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.arabic_utils import reshape_text
from app.services.pdf_fonts import ensure_pdf_fonts
from app.services.pdf_brand import (
    CONDITION_COLORS,
    LOGO_SVG_PATH,
    NEUTRAL_100,
    NEUTRAL_200,
    NEUTRAL_50,
    NEUTRAL_700,
    PRIMARY_500,
    PRIMARY_50,
)

PAGE_CONTENT_WIDTH = 17 * cm
GRID_COL_WIDTH = PAGE_CONTENT_WIDTH / 2

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _labels(lang: str) -> dict[str, str]:
    if lang == "ar":
        return {
            "site_asset": "الموقع والأصل",
            "site_name": "اسم الموقع",
            "address": "العنوان",
            "asset_id": "معرف الأصل",
            "inspection": "تفاصيل الفحص",
            "date": "التاريخ",
            "type": "نوع الفحص",
            "scope": "النطاق",
            "personnel": "الطاقم",
            "inspector_role": "المفتش / الدور",
            "contact": "التواصل",
            "time_logging": "تسجيل الوقت",
            "start_time": "وقت البداية",
            "end_time": "وقت النهاية",
            "labor_hours": "ساعات العمل",
            "observations": "الملاحظات",
            "overall_condition": "الحالة العامة",
            "findings": "النتائج / العيوب",
            "tests": "الاختبارات المنفذة",
            "resolution": "الإجراءات",
            "part_name": "القطعة",
            "sku": "رمز SKU",
            "qty": "الكمية",
            "no_parts": "لم تُستخدم قطع.",
            "recommended": "الإجراءات الموصى بها",
            "signoff": "التوقيع / الختم",
            "wo": "أمر العمل",
        }
    return {
        "site_asset": "Site & asset",
        "site_name": "Site name",
        "address": "Address",
        "asset_id": "Asset ID",
        "inspection": "Inspection details",
        "date": "Date",
        "type": "Type",
        "scope": "Scope",
        "personnel": "Personnel",
        "inspector_role": "Inspector / role",
        "contact": "Contact",
        "time_logging": "Time logging",
        "start_time": "Start time",
        "end_time": "End time",
        "labor_hours": "Logged labor hours",
        "observations": "Observations",
        "overall_condition": "Overall condition",
        "findings": "Findings / defects",
        "tests": "Tests performed",
        "resolution": "Resolution",
        "part_name": "Part",
        "sku": "SKU",
        "qty": "Qty",
        "no_parts": "No parts used.",
        "recommended": "Recommended actions",
        "signoff": "Verification signature / stamp",
        "wo": "Work order",
    }


def _doc_title(lang: str) -> str:
    if lang == "ar":
        return "تقرير صيانة / Maintenance Report"
    return "Maintenance Report / تقرير صيانة"


def _logo_data_uri() -> str | None:
    if not LOGO_SVG_PATH.is_file():
        return None
    raw = LOGO_SVG_PATH.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _condition_color(value: str) -> str:
    key = (value or "").strip().lower()
    return CONDITION_COLORS.get(key, PRIMARY_500)


def _format_parts(answers: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    raw = answers.get("parts_used")
    if not isinstance(raw, list):
        return rows
    for row in raw:
        if not isinstance(row, dict):
            continue
        sku = str(row.get("sku", "")).strip()
        qty = row.get("quantity", row.get("qty", 1))
        name = str(row.get("name") or sku or "—")
        rows.append({"name": name, "sku": sku or "—", "qty": str(qty)})
    return rows


def _labor_hours_display(answers: dict[str, Any]) -> str:
    total = 0.0
    raw = answers.get("labor_log")
    if isinstance(raw, list):
        for row in raw:
            if isinstance(row, dict) and row.get("hours") not in (None, "", 0):
                try:
                    total += float(row["hours"])
                except (TypeError, ValueError):
                    pass
    if total <= 0:
        elapsed = answers.get("time_elapsed_hours")
        if elapsed not in (None, "", 0):
            try:
                total = float(elapsed)
            except (TypeError, ValueError):
                total = 0.0
    if total <= 0:
        return "—"
    return f"{total:.2f} h"


def _text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback


def build_report_view_model(
    *,
    tenant_name: str,
    work_order_title: str,
    work_order_id: str,
    answers: dict[str, Any],
    platform_company_name: str = "Orbit Software",
    platform_copyright: str = "",
    lang: str = "ar",
    dir_: str | None = None,
) -> dict[str, Any]:
    lang = (lang or "ar").lower()[:2]
    direction = dir_ or ("rtl" if lang == "ar" else "ltr")
    labels = _labels(lang)
    condition = _text(answers.get("overall_condition"), "—")
    font_stack = (
        '"Noto Sans Arabic", "IBM Plex Sans Arabic", sans-serif'
        if lang == "ar"
        else '"Inter", "Plus Jakarta Sans", sans-serif'
    )

    return {
        "lang": lang,
        "dir": direction,
        "doc_title": _doc_title(lang),
        "platform_name": platform_company_name,
        "tenant_name": tenant_name,
        "work_order_title": work_order_title or "",
        "work_order_id": work_order_id or "",
        "wo_label": labels["wo"],
        "logo_data_uri": _logo_data_uri(),
        "primary": PRIMARY_500,
        "primary_light": PRIMARY_50,
        "neutral_0": "#ffffff",
        "neutral_50": NEUTRAL_50,
        "neutral_100": NEUTRAL_100,
        "neutral_200": NEUTRAL_200,
        "neutral_700": NEUTRAL_700,
        "neutral_900": "#1c1917",
        "font_stack": font_stack,
        "labels": labels,
        "site_name": _text(answers.get("property_site_name")),
        "site_address": _text(answers.get("property_full_address")),
        "asset_id": _text(answers.get("asset_unit_identification")),
        "inspection_date": _text(answers.get("inspection_date")),
        "inspection_type": _text(answers.get("inspection_type")),
        "scope": _text(answers.get("scope_systems_list")),
        "inspector_name": _text(answers.get("inspector_full_name")),
        "inspector_role": _text(answers.get("inspector_title")),
        "inspector_contact": _text(answers.get("inspector_contact")),
        "start_time": _text(answers.get("inspection_start_time")),
        "end_time": _text(answers.get("inspection_end_time")),
        "labor_hours": _labor_hours_display(answers),
        "overall_condition": condition,
        "condition_color": _condition_color(condition),
        "findings": _text(answers.get("findings_defects"), ""),
        "tests_performed": _text(answers.get("tests_performed"), ""),
        "parts_rows": _format_parts(answers),
        "recommended_actions": _text(answers.get("recommended_actions"), ""),
        "signature_html": "",
        "footer_note": platform_copyright or f"© {platform_company_name}",
    }


def render_maintenance_report_html(ctx: dict[str, Any]) -> str:
    template = _jinja.get_template("maintenance_report.html")
    return template.render(**ctx)


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    display = reshape_text(text)
    safe = html.escape(display).replace("\n", "<br/>")
    return Paragraph(safe, style)


def _panel_table(
    title: str,
    rows: list[tuple[str, str] | tuple[str, str, bool]],
    styles: dict[str, ParagraphStyle],
    panel_width: float,
) -> Table:
    label_w = panel_width * 0.36
    value_w = panel_width * 0.64
    data = [[_p(title, styles["panel_title"]), ""]]
    for item in rows:
        wrap = False
        if len(item) == 3:
            label, value, wrap = item
        else:
            label, value = item
        value_style = styles["value_wrap"] if wrap else styles["value"]
        data.append([_p(label, styles["label"]), _p(value, value_style)])
    t = Table(data, colWidths=[label_w, value_w])
    t.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NEUTRAL_50)),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(NEUTRAL_200)),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor(NEUTRAL_200)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def render_maintenance_report_pdf_reportlab(ctx: dict[str, Any]) -> bytes:
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
    align = TA_RIGHT if ctx.get("dir") == "rtl" else TA_LEFT
    styles = {
        "title": ParagraphStyle("RTitle", parent=base["Title"], fontName=font_name, fontSize=14, textColor=colors.HexColor(PRIMARY_500), alignment=align),
        "subtitle": ParagraphStyle("RSub", parent=base["Normal"], fontName=font_name, fontSize=9, textColor=colors.HexColor(NEUTRAL_700), alignment=align),
        "brand": ParagraphStyle("RBrand", parent=base["Normal"], fontName=font_name, fontSize=11, textColor=colors.HexColor(PRIMARY_500), alignment=align),
        "panel_title": ParagraphStyle("PT", parent=base["Normal"], fontName=font_name, fontSize=8, textColor=colors.HexColor(PRIMARY_500), alignment=align),
        "label": ParagraphStyle("PL", parent=base["Normal"], fontName=font_name, fontSize=8, textColor=colors.HexColor(NEUTRAL_700), alignment=align),
        "value": ParagraphStyle("PV", parent=base["Normal"], fontName=font_name, fontSize=9, alignment=align),
        "value_wrap": ParagraphStyle(
            "PVWrap",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            alignment=align,
            leading=11,
            wordWrap="CJK",
        ),
        "section": ParagraphStyle("Sec", parent=base["Heading3"], fontName=font_name, fontSize=11, textColor=colors.HexColor(PRIMARY_500), alignment=align),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontName=font_name, fontSize=9, alignment=align),
        "badge": ParagraphStyle(
            "Badge",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            textColor=colors.white,
            backColor=colors.HexColor(ctx.get("condition_color", PRIMARY_500)),
            alignment=align,
        ),
    }

    labels = ctx["labels"]
    story: list[Any] = []

    header_left = [
        [_p(ctx["platform_name"], styles["brand"])],
        [_p(ctx["tenant_name"], styles["subtitle"])],
    ]
    header_right = [
        [_p(ctx["doc_title"], styles["title"])],
        [_p(f"{labels['wo']}: {ctx.get('work_order_title') or ctx['work_order_id']}", styles["subtitle"])],
    ]
    header = Table(
        [[Table(header_left, colWidths=[GRID_COL_WIDTH]), Table(header_right, colWidths=[GRID_COL_WIDTH])]],
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

    context_row = Table(
        [
            [
                _panel_table(
                    labels["site_asset"],
                    [
                        (labels["site_name"], ctx["site_name"]),
                        (labels["address"], ctx["site_address"], True),
                        (labels["asset_id"], ctx["asset_id"]),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
                _panel_table(
                    labels["inspection"],
                    [
                        (labels["date"], ctx["inspection_date"]),
                        (labels["type"], ctx["inspection_type"]),
                        (labels["scope"], ctx["scope"]),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
            ]
        ],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
        hAlign="LEFT",
    )
    context_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(context_row)
    story.append(Spacer(1, 0.25 * cm))

    exec_row = Table(
        [
            [
                _panel_table(
                    labels["personnel"],
                    [
                        (
                            labels["inspector_role"],
                            f"{ctx['inspector_name']} — {ctx['inspector_role']}",
                        ),
                        (labels["contact"], ctx["inspector_contact"]),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
                _panel_table(
                    labels["time_logging"],
                    [
                        (labels["start_time"], ctx["start_time"]),
                        (labels["end_time"], ctx["end_time"]),
                        (labels["labor_hours"], ctx["labor_hours"]),
                    ],
                    styles,
                    GRID_COL_WIDTH,
                ),
            ]
        ],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
    )
    exec_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(exec_row)
    story.append(Spacer(1, 0.4 * cm))

    story.append(_p(labels["observations"], styles["section"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_p(f"{labels['overall_condition']}: {ctx['overall_condition']}", styles["badge"]))
    story.append(Spacer(1, 0.2 * cm))
    if ctx.get("findings"):
        story.append(_p(labels["findings"], styles["label"]))
        story.append(_p(ctx["findings"], styles["body"]))
        story.append(Spacer(1, 0.15 * cm))
    if ctx.get("tests_performed"):
        story.append(_p(labels["tests"], styles["label"]))
        story.append(_p(ctx["tests_performed"], styles["body"]))
        story.append(Spacer(1, 0.15 * cm))

    story.append(_p(labels["resolution"], styles["section"]))
    story.append(Spacer(1, 0.15 * cm))
    parts_rows = ctx.get("parts_rows") or []
    if parts_rows:
        table_data = [
            [
                _p(labels["part_name"], styles["label"]),
                _p(labels["sku"], styles["label"]),
                _p(labels["qty"], styles["label"]),
            ]
        ]
        for row in parts_rows:
            table_data.append([_p(row["name"], styles["body"]), _p(row["sku"], styles["body"]), _p(row["qty"], styles["body"])])
        parts_table = Table(table_data, colWidths=[7 * cm, 5 * cm, 3 * cm])
        parts_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY_500)),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor(NEUTRAL_200)),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(NEUTRAL_100)]),
                ]
            )
        )
        story.append(parts_table)
    else:
        story.append(_p(labels["no_parts"], styles["body"]))

    if ctx.get("recommended_actions"):
        story.append(Spacer(1, 0.2 * cm))
        story.append(_p(labels["recommended"], styles["label"]))
        story.append(_p(ctx["recommended_actions"], styles["body"]))

    story.append(Spacer(1, 0.5 * cm))
    signoff = Table([[_p(labels["signoff"], styles["label"])], [Spacer(1, 12 * mm)]], colWidths=[PAGE_CONTENT_WIDTH])
    signoff.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(NEUTRAL_200), None, (3, 3))]))
    story.append(signoff)
    story.append(Spacer(1, 0.3 * cm))
    story.append(_p(ctx.get("footer_note", ""), styles["subtitle"]))

    doc.build(story)
    return buf.getvalue()


def render_maintenance_report_pdf(
    *,
    tenant_name: str,
    work_order_title: str,
    work_order_id: str = "",
    answers: dict[str, Any],
    platform_company_name: str = "Orbit Software",
    platform_copyright: str = "",
    lang: str = "ar",
    dir_: str | None = None,
    **_kwargs: Any,
) -> bytes:
    ctx = build_report_view_model(
        tenant_name=tenant_name,
        work_order_title=work_order_title,
        work_order_id=work_order_id or work_order_title,
        answers=answers or {},
        platform_company_name=platform_company_name,
        platform_copyright=platform_copyright,
        lang=lang,
        dir_=dir_,
    )
    return render_maintenance_report_pdf_reportlab(ctx)


def resolve_report_locale(
    tenant_settings: dict[str, Any] | None,
    lang_override: str | None = None,
) -> tuple[str, str]:
    if lang_override:
        lang = str(lang_override).lower()[:2]
        if lang in ("ar", "en"):
            return lang, "rtl" if lang == "ar" else "ltr"
    settings = tenant_settings or {}
    lang = str(settings.get("language") or settings.get("locale") or "en").lower()[:2]
    if lang not in ("ar", "en"):
        lang = "en"
    direction = "rtl" if lang == "ar" else "ltr"
    return lang, direction
