"""Enterprise maintenance report PDF — HTML template + ReportLab renderer."""

from __future__ import annotations

import html
from io import BytesIO
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.arabic_utils import reshape_text
from app.services.pdf_fonts import ensure_pdf_fonts, pdf_font_faces
from app.services.pdf_brand import (
    CONDITION_COLORS,
    NEUTRAL_100,
    NEUTRAL_200,
    NEUTRAL_50,
    NEUTRAL_700,
    NEUTRAL_900,
    PRIMARY_500,
    PRIMARY_50,
    SECONDARY_500,
    company_initials,
)

# Match SimpleDocTemplate margins so columns / sign-off share the same content box.
PAGE_MARGIN = 1.4 * cm
PAGE_CONTENT_WIDTH = A4[0] - 2 * PAGE_MARGIN
GRID_COL_WIDTH = PAGE_CONTENT_WIDTH / 2
PANEL_GAP = 0.2 * cm
PANEL_WIDTH = GRID_COL_WIDTH - PANEL_GAP / 2

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _labels(lang: str) -> dict[str, str]:
    if lang == "ar":
        return {
            "site_asset": "الموقع والأصل",
            "client": "العميل",
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
            "parts_used": "القطع المستخدمة",
            "part_name": "القطعة",
            "sku": "رمز SKU",
            "qty": "الكمية",
            "no_parts": "لم تُستخدم قطع.",
            "recommended": "الإجراءات الموصى بها",
            "signoff": "التوقيع / الختم",
            "wo": "أمر العمل",
            "prepared_for": "مُعدّ لـ",
            "company_tagline": "صيانة وإدارة مرافق",
            "corrective_chip": "تصحيحي",
            "preventive_chip": "وقائي",
        }
    return {
        "site_asset": "Site & asset",
        "client": "Client",
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
        "parts_used": "Parts used",
        "part_name": "Part",
        "sku": "SKU",
        "qty": "Qty",
        "no_parts": "No parts used.",
        "recommended": "Recommended actions",
        "signoff": "Verification signature / stamp",
        "wo": "Work order",
        "prepared_for": "Prepared for",
        "company_tagline": "Maintenance & FM",
        "corrective_chip": "CORRECTIVE",
        "preventive_chip": "PREVENTIVE",
    }


def _doc_title(lang: str) -> str:
    if lang == "ar":
        return "تقرير صيانة"
    return "Maintenance Report"


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
        try:
            qty_label = str(max(1, int(round(float(qty)))))
        except (TypeError, ValueError):
            qty_label = "1"
        name = str(row.get("name") or sku or "—")
        rows.append({"name": name, "sku": sku or "—", "qty": qty_label})
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


def _wo_type_chip(answers: dict[str, Any], inspection_type: str) -> str | None:
    """Return 'corrective' | 'preventive' | None for the L1 type chip."""
    source = str(answers.get("wo_source") or "").strip().lower()
    t = (inspection_type or "").strip().lower()
    tags = answers.get("maintenance_tags") or []
    tag_l = [str(x).strip().lower() for x in tags] if isinstance(tags, list) else []

    if source == "preventive" or "preventive" in t or "وقائي" in t or "preventive" in tag_l:
        return "preventive"
    if (
        source in ("corrective", "request")
        or any(k in t for k in ("corrective", "تصحيحي", "reactive", "breakdown", "emergency", "request"))
        or "corrective" in tag_l
    ):
        return "corrective"
    if any(k in t for k in ("corrective", "تصحيحي")):
        return "corrective"
    return None


def build_report_view_model(
    *,
    tenant_name: str,
    work_order_title: str,
    work_order_id: str,
    answers: dict[str, Any],
    platform_company_name: str = "",
    platform_copyright: str = "",
    client_name: str = "",
    lang: str = "ar",
    dir_: str | None = None,
) -> dict[str, Any]:
    """L1 Classic ledger view-model — tenant company brand, hospital/client as recipient."""
    lang = (lang or "ar").lower()[:2]
    direction = dir_ or ("rtl" if lang == "ar" else "ltr")
    labels = _labels(lang)
    condition = _text(answers.get("overall_condition"), "—")
    company = (tenant_name or "").strip() or (platform_company_name or "").strip() or "—"
    client = _text(client_name or answers.get("client_legal_name"), "—")
    inspection_type = _text(answers.get("inspection_type"))
    # Localize inspection type for Arabic display when value is the English catalog label.
    inspection_type_display = inspection_type
    if lang == "ar":
        _type_ar = {
            "Corrective": "تصحيحي",
            "Preventive": "وقائي",
            "Request": "طلب",
        }
        inspection_type_display = _type_ar.get(inspection_type, inspection_type)
    font_stack = (
        '"Noto Sans Arabic", "IBM Plex Sans Arabic", sans-serif'
        if lang == "ar"
        else '"IBM Plex Sans", "Inter", "Plus Jakarta Sans", sans-serif'
    )
    prepared = ""
    if client != "—":
        prepared = f"{labels['prepared_for']} {client}"
    type_chip = _wo_type_chip(answers or {}, inspection_type)

    return {
        "lang": lang,
        "dir": direction,
        "doc_title": _doc_title(lang),
        # L1: company brand is the tenant — never Orbit platform name in the header.
        "company_name": company,
        "company_initials": company_initials(company),
        "company_tagline": labels["company_tagline"],
        "platform_name": company,
        "tenant_name": company,
        "client_name": client,
        "prepared_for": prepared,
        "work_order_title": work_order_title or "",
        "work_order_id": work_order_id or "",
        "wo_label": labels["wo"],
        "logo_data_uri": None,
        "show_corrective_chip": type_chip == "corrective",
        "show_type_chip": type_chip is not None,
        "type_chip_kind": type_chip,
        "corrective_chip": labels["corrective_chip"],
        "type_chip_label": (
            labels["preventive_chip"]
            if type_chip == "preventive"
            else labels["corrective_chip"]
        ),
        "secondary": SECONDARY_500,
        "primary": PRIMARY_500,
        "primary_light": PRIMARY_50,
        "neutral_0": "#ffffff",
        "neutral_50": NEUTRAL_50,
        "neutral_100": NEUTRAL_100,
        "neutral_200": NEUTRAL_200,
        "neutral_700": NEUTRAL_700,
        "neutral_900": NEUTRAL_900,
        "font_stack": font_stack,
        "labels": labels,
        "site_name": _text(answers.get("property_site_name")),
        "site_address": _text(answers.get("property_full_address")),
        "asset_id": _text(answers.get("asset_unit_identification")),
        "inspection_date": _text(answers.get("inspection_date")),
        "inspection_type": inspection_type_display,
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
        # Build stamp so exports prove which renderer ran (remove after UAT).
        "footer_note": (
            (platform_copyright.strip() if platform_copyright else f"© {company}")
            + " · L1-obs-v3"
        ),
    }


def render_maintenance_report_html(ctx: dict[str, Any]) -> str:
    template = _jinja.get_template("maintenance_report.html")
    return template.render(**ctx)


_AR_CP_MIN, _AR_CP_MAX = 0x0600, 0x06FF


def _has_arabic(text: str) -> bool:
    return any(_AR_CP_MIN <= ord(c) <= _AR_CP_MAX for c in text)


def _has_latin(text: str) -> bool:
    return any(("A" <= c <= "Z") or ("a" <= c <= "z") for c in text)


def _font_for_text(
    text: str,
    *,
    bold: bool,
    ar_reg: str,
    ar_bold: str,
    lat_reg: str,
    lat_bold: str,
) -> str:
    """Pick a face that actually has glyphs for ``text``.

    Noto Sans Arabic Bold ships without Latin codepoints — using it for
    company names / English values makes them disappear. Mixed AR+EN
    strings fall back to Arabic Regular (which includes Latin).
    """
    ar, lat = _has_arabic(text), _has_latin(text)
    if ar and lat:
        return ar_reg
    if ar:
        return ar_bold if bold else ar_reg
    return lat_bold if bold else lat_reg


_RTL_DRAW = False  # set True while building an RTL report so mixed lines bidi correctly


def _p(
    text: str,
    style: ParagraphStyle,
    *,
    font_name: str | None = None,
) -> Paragraph:
    display = reshape_text(text, base_dir="R" if _RTL_DRAW else None)
    safe = html.escape(display).replace("\n", "<br/>")
    if font_name and font_name != style.fontName:
        style = ParagraphStyle(
            f"{style.name}_{font_name}",
            parent=style,
            fontName=font_name,
        )
    return Paragraph(safe, style)


def _section_title(text: str, lang: str) -> str:
    """L1 panel/section titles are uppercase in Latin; keep Arabic as-is."""
    if (lang or "").startswith("ar"):
        return text
    return text.upper()


def _panel_table(
    title: str,
    rows: list[tuple[str, str] | tuple[str, str, bool]],
    styles: dict[str, ParagraphStyle],
    panel_width: float,
    *,
    lang: str = "en",
    rtl: bool = False,
    fonts: dict[str, str] | None = None,
) -> Table:
    """L1 Classic panel — light fill, hairline border; RTL flips label/value columns."""
    fonts = fonts or {}
    label_w = panel_width * 0.36
    value_w = panel_width * 0.64
    # ReportLab columns run L→R. For RTL, put value on the left so label sits on the right.
    # SPAN uses cell (0,0) content — always put the title there; Paragraph alignment does the rest.

    def _f(text: str, *, bold: bool) -> str:
        return _font_for_text(
            text,
            bold=bold,
            ar_reg=fonts.get("ar_reg", styles["label"].fontName),
            ar_bold=fonts.get("ar_bold", styles["panel_title"].fontName),
            lat_reg=fonts.get("lat_reg", styles["label"].fontName),
            lat_bold=fonts.get("lat_bold", styles["panel_title"].fontName),
        )

    if rtl:
        col_widths = [value_w, label_w]
    else:
        col_widths = [label_w, value_w]
    title_text = _section_title(title, lang)
    data: list[list[Any]] = [
        [_p(title_text, styles["panel_title"], font_name=_f(title_text, bold=True)), ""]
    ]
    for item in rows:
        wrap = False
        if len(item) == 3:
            label, value, wrap = item
        else:
            label, value = item
        value_style = styles["value_wrap"] if wrap else styles["value"]
        label_p = _p(label, styles["label"], font_name=_f(label, bold=False))
        value_p = _p(value, value_style, font_name=_f(value, bold=True))
        if rtl:
            data.append([value_p, label_p])
        else:
            data.append([label_p, value_p])
    t = Table(data, colWidths=col_widths)
    title_align = "RIGHT" if rtl else "LEFT"
    t.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("ALIGN", (0, 0), (-1, 0), title_align),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NEUTRAL_50)),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor(NEUTRAL_200)),
                ("LINEBELOW", (0, 0), (-1, 0), 0.4, colors.HexColor(NEUTRAL_200)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("TOPPADDING", (0, 1), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
            ]
        )
    )
    return t


def _pill(
    text: str,
    bg: str,
    styles: dict[str, ParagraphStyle],
    width: float = 2.4 * cm,
    *,
    font_name: str | None = None,
) -> Table:
    chip = Table([[_p(text, styles["chip_text"], font_name=font_name)]], colWidths=[width])
    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return chip


def render_maintenance_report_pdf_reportlab(ctx: dict[str, Any]) -> bytes:
    """Render locked L1 Classic ledger composition (A4)."""
    buf = BytesIO()
    # Tight top margin — design sits close to the page edge (no large header padding).
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=0.25 * cm,
        bottomMargin=1.0 * cm,
    )
    base = getSampleStyleSheet()
    lang = str(ctx.get("lang") or "en")
    rtl = ctx.get("dir") == "rtl"
    align = TA_RIGHT if rtl else TA_LEFT
    fonts = pdf_font_faces()
    # Default face for the report language; per-string overrides via _font_for_text.
    font_name, font_bold = ensure_pdf_fonts(lang=lang)
    global _RTL_DRAW
    _RTL_DRAW = rtl

    def _ff(text: str, *, bold: bool) -> str:
        return _font_for_text(text, bold=bold, **fonts)

    styles = {
        "title": ParagraphStyle(
            "RTitle",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=16,
            leading=19,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=align,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "subtitle": ParagraphStyle(
            "RSub",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=align,
        ),
        "brand": ParagraphStyle(
            "RBrand",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=16,
            leading=19,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=align,
        ),
        "panel_title": ParagraphStyle(
            "PT",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=align,
        ),
        "label": ParagraphStyle(
            "PL",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=align,
        ),
        "value": ParagraphStyle(
            "PV",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor(NEUTRAL_900),
            alignment=align,
        ),
        "value_wrap": ParagraphStyle(
            "PVWrap",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=9,
            alignment=align,
            leading=11,
            textColor=colors.HexColor(NEUTRAL_900),
            wordWrap="CJK",
        ),
        "section": ParagraphStyle(
            "Sec",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=align,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=align,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
        ),
        "mark": ParagraphStyle(
            "CompanyMark",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "chip_text": ParagraphStyle(
            "ChipText",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "mono": ParagraphStyle(
            "MonoMeta",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=align,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=7,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=TA_LEFT if rtl else TA_RIGHT,
        ),
        "sign_label": ParagraphStyle(
            "SignLabel",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=7,
            leading=9,
            textColor=colors.HexColor(NEUTRAL_700),
            alignment=align,
        ),
        "field_title": ParagraphStyle(
            "FieldTitle",
            parent=base["Normal"],
            fontName=font_bold,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(PRIMARY_500),
            alignment=align,
            leftIndent=0,
            rightIndent=0,
            firstLineIndent=0,
            spaceBefore=0,
            spaceAfter=0,
        ),
    }

    labels = ctx["labels"]
    story: list[Any] = []
    gap = 0.22 * cm

    # ── Header: company mark + name | doc title ──
    initials = ctx.get("company_initials") or "CO"
    brand_mark = Table(
        [[_p(initials, styles["mark"], font_name=_ff(initials, bold=True))]],
        colWidths=[1.0 * cm],
        rowHeights=[1.0 * cm],
    )
    brand_mark.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PRIMARY_500)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    company_name = str(ctx["company_name"])
    tagline = str(ctx.get("company_tagline") or "")
    prepared = str(ctx.get("prepared_for") or "")
    brand_text = Table(
        [
            [_p(company_name, styles["brand"], font_name=_ff(company_name, bold=True))],
            [_p(tagline, styles["subtitle"], font_name=_ff(tagline, bold=False))],
            [_p(prepared, styles["subtitle"], font_name=_ff(prepared, bold=False))],
        ],
        colWidths=[GRID_COL_WIDTH - 1.5 * cm],
    )
    brand_row = Table(
        [[brand_mark, brand_text]] if not rtl else [[brand_text, brand_mark]],
        colWidths=[1.15 * cm, GRID_COL_WIDTH - 1.15 * cm]
        if not rtl
        else [GRID_COL_WIDTH - 1.15 * cm, 1.15 * cm],
    )
    brand_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    doc_title = str(ctx["doc_title"])
    wo_sub = f"{labels['wo']}: {ctx.get('work_order_title') or ctx['work_order_id']}"
    header_right = Table(
        [
            [_p(doc_title, styles["title"], font_name=_ff(doc_title, bold=True))],
            [_p(wo_sub, styles["subtitle"], font_name=_ff(wo_sub, bold=False))],
        ],
        colWidths=[GRID_COL_WIDTH],
    )
    header = Table(
        [[brand_row, header_right]] if not rtl else [[header_right, brand_row]],
        colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LINEBELOW", (0, 0), (-1, -1), 2, colors.HexColor(PRIMARY_500)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(header)
    story.append(Spacer(1, gap))

    # ── Meta row: WO id + type chip (corrective copper / preventive navy) ──
    wo_id = str(ctx.get("work_order_id") or "")
    wo_id_cell = _p(wo_id, styles["mono"], font_name=_ff(wo_id, bold=False))
    if ctx.get("show_type_chip"):
        chip_color = (
            PRIMARY_500 if ctx.get("type_chip_kind") == "preventive" else SECONDARY_500
        )
        chip_label = str(
            ctx.get("type_chip_label") or ctx.get("corrective_chip") or "CORRECTIVE"
        )
        chip = _pill(
            chip_label,
            chip_color,
            styles,
            2.8 * cm,
            font_name=_ff(chip_label, bold=True),
        )
        chip_w = 2.9 * cm
        chip_row = Table(
            [[wo_id_cell, chip]] if not rtl else [[chip, wo_id_cell]],
            colWidths=[PAGE_CONTENT_WIDTH - chip_w, chip_w]
            if not rtl
            else [chip_w, PAGE_CONTENT_WIDTH - chip_w],
        )
        chip_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        story.append(chip_row)
    else:
        story.append(wo_id_cell)
    story.append(Spacer(1, gap))

    # ── 2×2 panels (RTL: value|label inside panels + mirrored column order) ──
    site_panel = _panel_table(
        labels["site_asset"],
        [
            (labels["client"], ctx["client_name"]),
            (labels["site_name"], ctx["site_name"]),
            (labels["address"], ctx["site_address"], True),
            (labels["asset_id"], ctx["asset_id"]),
        ],
        styles,
        PANEL_WIDTH,
        lang=lang,
        rtl=rtl,
        fonts=fonts,
    )
    insp_panel = _panel_table(
        labels["inspection"],
        [
            (labels["date"], ctx["inspection_date"]),
            (labels["type"], ctx["inspection_type"]),
            (labels["scope"], ctx["scope"]),
        ],
        styles,
        PANEL_WIDTH,
        lang=lang,
        rtl=rtl,
        fonts=fonts,
    )
    # LTR: site | inspection · RTL: inspection | site (reading order)
    context_cells = [site_panel, insp_panel] if not rtl else [insp_panel, site_panel]
    context_row = Table([context_cells], colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH])
    context_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), PANEL_GAP / 2),
                ("LEFTPADDING", (1, 0), (1, 0), PANEL_GAP / 2),
            ]
        )
    )
    story.append(context_row)
    story.append(Spacer(1, gap))

    pe_panel = _panel_table(
        labels["personnel"],
        [
            (labels["inspector_role"], f"{ctx['inspector_name']} — {ctx['inspector_role']}"),
            (labels["contact"], ctx["inspector_contact"]),
        ],
        styles,
        PANEL_WIDTH,
        lang=lang,
        rtl=rtl,
        fonts=fonts,
    )
    tl_panel = _panel_table(
        labels["time_logging"],
        [
            (labels["start_time"], ctx["start_time"]),
            (labels["end_time"], ctx["end_time"]),
            (labels["labor_hours"], ctx["labor_hours"]),
        ],
        styles,
        PANEL_WIDTH,
        lang=lang,
        rtl=rtl,
        fonts=fonts,
    )
    exec_cells = [pe_panel, tl_panel] if not rtl else [tl_panel, pe_panel]
    exec_row = Table([exec_cells], colWidths=[GRID_COL_WIDTH, GRID_COL_WIDTH])
    exec_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), PANEL_GAP / 2),
                ("LEFTPADDING", (1, 0), (1, 0), PANEL_GAP / 2),
            ]
        )
    )
    story.append(exec_row)
    story.append(Spacer(1, 0.35 * cm))

    # ── Observations (full-width, bold field titles, padded blocks) ──
    obs_gap = 0.28 * cm
    obs_title = _section_title(labels["observations"], lang)
    story.append(_p(obs_title, styles["section"], font_name=_ff(obs_title, bold=True)))
    story.append(Spacer(1, 0.14 * cm))

    def _obs_title(text: str) -> Paragraph:
        return _p(text, styles["field_title"], font_name=_ff(text, bold=True))

    def _obs_body(text: str) -> Paragraph:
        return _p(text, styles["body"], font_name=_ff(text, bold=False))

    cond_text = str(ctx.get("overall_condition") or "—")
    cond_chip = _pill(
        cond_text,
        str(ctx.get("condition_color") or PRIMARY_500),
        styles,
        2.2 * cm,
        font_name=_ff(cond_text, bold=True),
    )
    cond_label = labels["overall_condition"]
    chip_w = 2.4 * cm
    label_w = PAGE_CONTENT_WIDTH - chip_w
    cond_row = Table(
        [[_obs_title(cond_label), cond_chip]]
        if not rtl
        else [[cond_chip, _obs_title(cond_label)]],
        colWidths=[label_w, chip_w] if not rtl else [chip_w, label_w],
    )
    cond_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("ALIGN", (0, 0), (0, 0), "LEFT" if not rtl else "RIGHT"),
                ("ALIGN", (-1, 0), (-1, 0), "RIGHT" if not rtl else "LEFT"),
            ]
        )
    )
    story.append(cond_row)

    if ctx.get("findings"):
        story.append(Spacer(1, obs_gap))
        story.append(_obs_title(labels["findings"]))
        story.append(Spacer(1, 0.1 * cm))
        story.append(_obs_body(ctx["findings"]))

    if ctx.get("tests_performed"):
        story.append(Spacer(1, obs_gap))
        story.append(_obs_title(labels["tests"]))
        story.append(Spacer(1, 0.1 * cm))
        story.append(_obs_body(ctx["tests_performed"]))

    # ── Parts used (L1 light header row) ──
    story.append(Spacer(1, 0.1 * cm))
    parts_title = _section_title(labels.get("parts_used") or labels["resolution"], lang)
    story.append(_p(parts_title, styles["section"], font_name=_ff(parts_title, bold=True)))
    story.append(Spacer(1, 0.12 * cm))
    parts_rows = ctx.get("parts_rows") or []
    if parts_rows:
        # LTR: Part | SKU | Qty · RTL: Qty | SKU | Part (natural reading order)
        name_w = PAGE_CONTENT_WIDTH * 0.48
        sku_w = PAGE_CONTENT_WIDTH * 0.32
        qty_w = PAGE_CONTENT_WIDTH * 0.20

        def _ph(text: str) -> Paragraph:
            return _p(text, styles["panel_title"], font_name=_ff(text, bold=True))

        def _pb(text: str, style_key: str = "body") -> Paragraph:
            return _p(text, styles[style_key], font_name=_ff(text, bold=False))

        if rtl:
            header = [_ph(labels["qty"]), _ph(labels["sku"]), _ph(labels["part_name"])]
            col_widths = [qty_w, sku_w, name_w]
        else:
            header = [_ph(labels["part_name"]), _ph(labels["sku"]), _ph(labels["qty"])]
            col_widths = [name_w, sku_w, qty_w]
        table_data: list[list[Any]] = [header]
        for row in parts_rows:
            cells = [
                _pb(row["name"]),
                _pb(row["sku"], "mono"),
                _pb(row["qty"]),
            ]
            table_data.append(list(reversed(cells)) if rtl else cells)
        parts_table = Table(table_data, colWidths=col_widths)
        parts_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(NEUTRAL_100)),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor(NEUTRAL_200)),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor(NEUTRAL_100)),
                    ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor(NEUTRAL_200)),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(parts_table)
    else:
        np_ = labels["no_parts"]
        story.append(_p(np_, styles["body"], font_name=_ff(np_, bold=False)))

    if ctx.get("recommended_actions"):
        story.append(Spacer(1, 0.18 * cm))
        ra = ctx["recommended_actions"]
        story.append(_p(ra, styles["body"], font_name=_ff(ra, bold=False)))

    # ── Sign-off flush to content edges (full-width rule + signature line) ──
    story.append(Spacer(1, 0.45 * cm))
    rule = Table([[""]], colWidths=[PAGE_CONTENT_WIDTH], rowHeights=[0.5])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(NEUTRAL_200))]))
    story.append(rule)
    story.append(Spacer(1, 0.25 * cm))
    sign_txt = labels["signoff"]
    story.append(_p(sign_txt, styles["sign_label"], font_name=_ff(sign_txt, bold=True)))
    story.append(Spacer(1, 0.55 * cm))
    sig_line = Table([[""]], colWidths=[PAGE_CONTENT_WIDTH], rowHeights=[0.6])
    sig_line.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor(NEUTRAL_700)),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(sig_line)
    story.append(Spacer(1, 0.3 * cm))
    footer = str(ctx.get("footer_note", ""))
    story.append(_p(footer, styles["footer"], font_name=_ff(footer, bold=False)))

    try:
        doc.build(story)
        return buf.getvalue()
    finally:
        _RTL_DRAW = False


def render_maintenance_report_pdf(
    *,
    tenant_name: str,
    work_order_title: str,
    work_order_id: str = "",
    answers: dict[str, Any],
    platform_company_name: str = "",
    platform_copyright: str = "",
    client_name: str = "",
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
        client_name=client_name,
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
