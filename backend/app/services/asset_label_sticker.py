"""A2 printable asset QR stickers (vector QR + periapsis mark, CMYK).

Design A — Docked Square: company, asset name, ID, serial, QR+logo.
Design C — Field Tag: copper spine, hang hole, QR left, copy right (no Orbit wordmark).

`size_mm`: side for A, width for C (height = width × 35/60).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Shape
from reportlab.lib.colors import CMYKColor, Color, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from app.models import Asset
from app.services.arabic_utils import reshape_text
from app.services.pdf_fonts import ensure_pdf_fonts

_SYMBOL_SVG = Path(__file__).resolve().parents[1] / "static" / "brand" / "orbit-symbol.svg"
_SYMBOL_DRAWING: Drawing | None = None

# Print CMYK (approx from Harbor Navy #123056 / Copper #e85d04 / ink #0f172a)
NAVY = CMYKColor(0.79, 0.44, 0.0, 0.66)
COPPER = CMYKColor(0.0, 0.60, 0.98, 0.09)
INK = CMYKColor(0.70, 0.55, 0.40, 0.80)
MUTED = CMYKColor(0.35, 0.20, 0.10, 0.45)
PAPER = CMYKColor(0.02, 0.01, 0.0, 0.02)

LABEL_SIZE_MM_DEFAULT = 70.0
LABEL_SIZE_MM_DEFAULT_C = 80.0
LABEL_SIZE_MM_MIN = 40.0
LABEL_SIZE_MM_MAX = 120.0
FIELD_TAG_ASPECT = 35.0 / 60.0

DESIGN_A = "a"
DESIGN_C = "c"


def normalize_label_design(design: str | None) -> str:
    raw = (design or DESIGN_A).strip().lower()
    if raw in ("c", "field", "field_tag", "tag"):
        return DESIGN_C
    return DESIGN_A


def clamp_label_size_mm(size_mm: float | int | None, *, design: str = DESIGN_A) -> float:
    default = LABEL_SIZE_MM_DEFAULT_C if design == DESIGN_C else LABEL_SIZE_MM_DEFAULT
    if size_mm is None:
        return default
    try:
        value = float(size_mm)
    except (TypeError, ValueError):
        return default
    return max(LABEL_SIZE_MM_MIN, min(LABEL_SIZE_MM_MAX, value))


def _pick_font() -> str:
    ensure_pdf_fonts()
    body = ensure_pdf_fonts()
    for candidate in (body, "Helvetica-Bold", "Helvetica"):
        try:
            pdfmetrics.getFont(candidate)
            return candidate
        except Exception:
            continue
    return "Helvetica"


def _fit_text(c: canvas.Canvas, text: str, font: str, max_size: float, max_width: float) -> float:
    size = max_size
    while size >= 4.5:
        if c.stringWidth(text, font, size) <= max_width:
            return size
        size -= 0.35
    return 4.5


def _display_company(name: str) -> str:
    return name.upper() if name.isascii() else name


def _asset_fields(asset: Asset, client_name: str | None) -> dict[str, str]:
    company = reshape_text((client_name or "").strip()) or "—"
    name = reshape_text((asset.name or asset.label_code or "Asset").strip())
    label = reshape_text((asset.label_code or "").strip()) or "—"
    serial = reshape_text((asset.serial or "").strip()) or "—"
    payload = (asset.qr_payload or "").strip()
    return {
        "company": company,
        "company_disp": _display_company(company),
        "name": name,
        "label": label,
        "serial": serial,
        "payload": payload,
    }


def _draw_vector_qr(
    c: canvas.Canvas,
    payload: str,
    *,
    x: float,
    y: float,
    size: float,
) -> None:
    """Draw QR modules as vector rectangles (CMYK navy) + vector periapsis eye."""
    if not payload:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", max(6, size * 0.08))
        c.drawCentredString(x + size / 2, y + size / 2, "No tag")
        return
    try:
        import qrcode
    except ImportError:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", max(6, size * 0.08))
        c.drawCentredString(x + size / 2, y + size / 2, "QR unavailable")
        return

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    if n == 0:
        return

    cell = size / n
    c.setFillColor(white)
    c.rect(x, y, size, size, fill=1, stroke=0)
    c.setFillColor(NAVY)
    # QR matrix[0][0] is top-left in image space; PDF y grows up
    for row in range(n):
        for col in range(n):
            if matrix[row][col]:
                c.rect(
                    x + col * cell,
                    y + (n - 1 - row) * cell,
                    cell + 0.02,
                    cell + 0.02,
                    fill=1,
                    stroke=0,
                )

    # White eye + vector periapsis mark (~22% of QR)
    eye = size * 0.22
    cx = x + size / 2
    cy = y + size / 2
    pad = eye * 1.2
    c.setFillColor(white)
    c.roundRect(cx - pad / 2, cy - pad / 2, pad, pad, pad * 0.18, fill=1, stroke=0)
    _draw_periapsis_mark(c, cx, cy, eye)


def _load_symbol_drawing() -> Drawing | None:
    """Load the same periapsis SVG used by the FE preview (vector)."""
    global _SYMBOL_DRAWING
    if _SYMBOL_DRAWING is not None:
        return _SYMBOL_DRAWING
    if not _SYMBOL_SVG.is_file():
        return None
    try:
        from svglib.svglib import svg2rlg
    except ImportError:
        return None
    drawing = svg2rlg(str(_SYMBOL_SVG))
    if drawing is None:
        return None
    _recolor_drawing_cmyk(drawing)
    _SYMBOL_DRAWING = drawing
    return drawing


def _recolor_drawing_cmyk(node: Shape | Group | Drawing) -> None:
    """Map brand RGB fills from the SVG to print CMYK navy/copper."""
    fill = getattr(node, "fillColor", None)
    if isinstance(fill, Color) and not isinstance(fill, CMYKColor):
        # Copper is warm/orange; everything else navy
        r, g, b = float(fill.red), float(fill.green), float(fill.blue)
        if r > 0.5 and g < 0.5:
            node.fillColor = COPPER
        else:
            node.fillColor = NAVY
    contents = getattr(node, "contents", None)
    if contents:
        for child in contents:
            _recolor_drawing_cmyk(child)


def _draw_periapsis_mark(c: canvas.Canvas, cx: float, cy: float, size: float) -> None:
    """Draw the official Orbit periapsis mark (same SVG as the in-app preview)."""
    drawing = _load_symbol_drawing()
    if drawing is None:
        # Minimal fallback if svglib/SVG missing
        c.setFillColor(NAVY)
        c.circle(cx, cy, size * 0.35, fill=0, stroke=1)
        c.setFillColor(COPPER)
        seat = size * 0.2
        c.roundRect(cx + size * 0.05, cy + size * 0.05, seat, seat, seat * 0.2, fill=1, stroke=0)
        return

    # Clone via svg2rlg cache: scale a copy by mutating a shallow scale transform
    src_w = float(drawing.width or 256)
    src_h = float(drawing.height or 256)
    scale = size / max(src_w, src_h)

    c.saveState()
    # SVG origin is top-left; reportlab Drawing draws with y-up from bottom-left of draw point
    origin_x = cx - (src_w * scale) / 2
    origin_y = cy - (src_h * scale) / 2
    c.translate(origin_x, origin_y)
    c.scale(scale, scale)
    renderPDF.draw(drawing, c, 0, 0)
    c.restoreState()


def _draw_meta_lines(
    c: canvas.Canvas,
    *,
    font: str,
    x: float,
    y: float,
    width: float,
    label: str,
    serial: str,
    size_ref: float,
    centered: bool = False,
) -> float:
    """Draw ID + serial; returns y after drawing (below)."""
    line = f"ID {label}  ·  SN {serial}"
    sz = _fit_text(c, line, font, size_ref * 0.035, width)
    c.setFillColor(MUTED)
    c.setFont(font, sz)
    if centered:
        c.drawCentredString(x + width / 2, y, line)
    else:
        c.drawString(x, y, line)
    return y - sz * 1.4


def render_docked_square_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
) -> bytes:
    side = clamp_label_size_mm(size_mm, design=DESIGN_A) * mm
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(side, side))
    # CMYK output
    c.setTitle("Orbit asset sticker A")
    font = _pick_font()
    fields = _asset_fields(asset, client_name)

    margin = side * 0.04
    inner = side - 2 * margin
    radius = side * 0.07
    border_w = max(2.8, side * 0.045)

    c.setFillColor(white)
    c.roundRect(margin, margin, inner, inner, radius, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(border_w)
    c.roundRect(margin, margin, inner, inner, radius, fill=0, stroke=1)

    # Copper corner
    corner = side * 0.1
    c.setFillColor(COPPER)
    path = c.beginPath()
    path.moveTo(side - margin, side - margin)
    path.lineTo(side - margin - corner, side - margin)
    path.lineTo(side - margin, side - margin - corner)
    path.close()
    c.drawPath(path, fill=1, stroke=0)

    # Company
    co = fields["company_disp"]
    co_size = _fit_text(c, co, font, side * 0.048, inner - side * 0.1)
    c.setFillColor(NAVY)
    c.setFont(font, co_size)
    c.drawCentredString(side / 2, side - margin - side * 0.08, co)

    # QR (larger)
    qr_size = side * 0.52
    qr_x = (side - qr_size) / 2
    qr_y = margin + side * 0.22
    _draw_vector_qr(c, fields["payload"], x=qr_x, y=qr_y, size=qr_size)

    # Asset name
    an = fields["name"]
    an_size = _fit_text(c, an, font, side * 0.05, inner - side * 0.1)
    c.setFillColor(INK)
    c.setFont(font, an_size)
    c.drawCentredString(side / 2, margin + side * 0.12, an)

    # ID + serial
    _draw_meta_lines(
        c,
        font=font,
        x=margin,
        y=margin + side * 0.055,
        width=inner,
        label=fields["label"],
        serial=fields["serial"],
        size_ref=side,
        centered=True,
    )

    c.showPage()
    c.save()
    return buf.getvalue()


def render_field_tag_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
) -> bytes:
    width = clamp_label_size_mm(size_mm, design=DESIGN_C) * mm
    height = width * FIELD_TAG_ASPECT
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setTitle("Orbit asset sticker C")
    font = _pick_font()
    fields = _asset_fields(asset, client_name)

    border_w = max(2.4, width * 0.022)
    radius = height * 0.12

    c.setFillColor(white)
    c.roundRect(0, 0, width, height, radius, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(border_w)
    c.roundRect(border_w / 2, border_w / 2, width - border_w, height - border_w, radius, fill=0, stroke=1)

    spine_w = max(border_w * 1.4, width * 0.035)
    c.setFillColor(COPPER)
    c.rect(0, 0, spine_w, height, fill=1, stroke=0)

    hole_r = height * 0.085
    hole_cx = width - height * 0.2
    hole_cy = height / 2
    c.setFillColor(PAPER)
    c.circle(hole_cx, hole_cy, hole_r, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(max(1.2, border_w * 0.55))
    c.circle(hole_cx, hole_cy, hole_r, fill=0, stroke=1)
    c.setFillColor(white)
    c.circle(hole_cx, hole_cy, hole_r * 0.52, fill=1, stroke=0)

    qr_size = height * 0.7
    qr_x = spine_w + width * 0.035
    qr_y = (height - qr_size) / 2
    _draw_vector_qr(c, fields["payload"], x=qr_x, y=qr_y, size=qr_size)

    copy_x = qr_x + qr_size + width * 0.03
    copy_right = hole_cx - hole_r - width * 0.035
    copy_w = max(24, copy_right - copy_x)

    co = fields["company_disp"]
    co_size = _fit_text(c, co, font, height * 0.085, copy_w)
    c.setFillColor(COPPER)
    c.setFont(font, co_size)
    c.drawString(copy_x, height * 0.72, co)

    an = fields["name"]
    an_size = _fit_text(c, an, font, height * 0.13, copy_w)
    c.setFillColor(NAVY)
    c.setFont(font, an_size)
    if c.stringWidth(an, font, an_size) <= copy_w:
        c.drawString(copy_x, height * 0.5, an)
        meta_y = height * 0.32
    else:
        parts = an.split()
        line1, line2 = an, ""
        for i in range(len(parts) - 1, 0, -1):
            left = " ".join(parts[:i])
            right = " ".join(parts[i:])
            if c.stringWidth(left, font, an_size) <= copy_w:
                line1, line2 = left, right
                break
        c.drawString(copy_x, height * 0.54, line1)
        if line2:
            ls = _fit_text(c, line2, font, an_size, copy_w)
            c.setFont(font, ls)
            c.drawString(copy_x, height * 0.4, line2)
            meta_y = height * 0.26
        else:
            meta_y = height * 0.32

    # ID + serial (no Orbit wordmark)
    line = f"ID {fields['label']}"
    sn = f"SN {fields['serial']}"
    id_sz = _fit_text(c, line, font, height * 0.075, copy_w)
    c.setFillColor(MUTED)
    c.setFont(font, id_sz)
    c.drawString(copy_x, meta_y, line)
    sn_sz = _fit_text(c, sn, font, height * 0.075, copy_w)
    c.setFont(font, sn_sz)
    c.drawString(copy_x, meta_y - id_sz * 1.35, sn)

    c.showPage()
    c.save()
    return buf.getvalue()


def render_asset_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
    design: str | None = None,
) -> bytes:
    kind = normalize_label_design(design)
    if kind == DESIGN_C:
        return render_field_tag_sticker_pdf(asset, client_name=client_name, size_mm=size_mm)
    return render_docked_square_sticker_pdf(asset, client_name=client_name, size_mm=size_mm)
