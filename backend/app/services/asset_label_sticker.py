"""A2 printable asset QR stickers (vector QR + periapsis mark).

Design A — Docked Square: company, asset name, ID, serial, QR+logo.
Design C — Field Tag: copper spine, QR left, copy right (no hang hole / Orbit wordmark).

Layout and RGB brand colors match the in-app ``AssetStickerPreview`` so preview === print.

`size_mm`: side for A, width for C (height = width × 35/60).
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing, Group, Shape
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from app.models import Asset
from app.services.arabic_utils import contains_arabic, reshape_text
from app.services.pdf_fonts import ensure_pdf_fonts

_SYMBOL_SVG = Path(__file__).resolve().parents[1] / "static" / "brand" / "orbit-symbol.svg"
_FONT_DIR = Path(__file__).resolve().parents[1] / "static" / "fonts"
_NOTO_PATH = _FONT_DIR / "NotoSansArabic-Regular.ttf"
_SYMBOL_DRAWING: Drawing | None = None

# Same hex tokens as FE preview (AssetStickerPreview.tsx)
_RGB_NAVY = (0x12, 0x30, 0x56)
_RGB_COPPER = (0xE8, 0x5D, 0x04)
_RGB_INK = (0x0F, 0x17, 0x2A)
_RGB_MUTED = (0x5B, 0x6B, 0x7C)

NAVY = HexColor("#123056")
COPPER = HexColor("#e85d04")
INK = HexColor("#0f172a")
MUTED = HexColor("#5b6b7c")
PAPER = HexColor("#f7f9fc")

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


def _asset_fields(
    asset: Asset,
    client_name: str | None,
    *,
    qr_payload: str | None = None,
) -> dict[str, str]:
    """Return *logical* strings; Arabic shaping happens at draw time (PIL)."""
    company_raw = (client_name or "").strip() or "—"
    name_raw = (asset.name or asset.label_code or "Asset").strip()
    label_raw = (asset.label_code or "").strip() or "—"
    serial_raw = (asset.serial or "").strip() or "—"
    payload = (qr_payload if qr_payload is not None else asset.qr_payload or "").strip()
    return {
        "company": company_raw,
        "company_disp": _display_company(company_raw),
        "name": name_raw,
        "label": label_raw,
        "serial": serial_raw,
        "payload": payload,
    }


def _draw_text_line(
    c: canvas.Canvas,
    text: str,
    *,
    x: float,
    y: float,
    max_width: float,
    max_size: float,
    font: str,
    fill_cmyk: Color,  # brand Color (param name kept for call-site compatibility)
    fill_rgb: tuple[int, int, int],
    centered: bool = False,
) -> float:
    """Draw one line. Arabic → PIL bitmap (no PDF-viewer bidi double-reverse)."""
    if not text:
        return y

    if contains_arabic(text) and _NOTO_PATH.is_file():
        return _draw_arabic_pil_line(
            c,
            text,
            x=x,
            y=y,
            max_width=max_width,
            max_size=max_size,
            fill_rgb=fill_rgb,
            centered=centered,
        )

    # Latin / digits — vector
    display = text
    sz = _fit_text(c, display, font, max_size, max_width)
    c.setFillColor(fill_cmyk)
    c.setFont(font, sz)
    if centered:
        c.drawCentredString(x + max_width / 2, y, display)
    else:
        c.drawString(x, y, display)
    return y - sz * 1.35


def _arabic_visual_line(text: str) -> str:
    """Joined Arabic glyphs in LTR paint order (matches browser RTL pixel order)."""
    return reshape_text(text, for_ltr_draw=True)


def _draw_arabic_pil_line(
    c: canvas.Canvas,
    text: str,
    *,
    x: float,
    y: float,
    max_width: float,
    max_size: float,
    fill_rgb: tuple[int, int, int],
    centered: bool,
) -> float:
    """Rasterize reshaped Arabic so PDF viewers cannot re-apply Unicode bidi."""
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.utils import ImageReader

    visual = _arabic_visual_line(text)
    # High DPI so print stays sharp
    scale = 4.0
    size_px = max(10, int(max_size * scale))
    font = ImageFont.truetype(str(_NOTO_PATH), size_px)

    while size_px >= 10:
        font = ImageFont.truetype(str(_NOTO_PATH), size_px)
        bbox = font.getbbox(visual)
        text_w = bbox[2] - bbox[0]
        if text_w <= max_width * scale:
            break
        size_px -= 1

    bbox = font.getbbox(visual)
    pad = 6
    img_w = max(1, (bbox[2] - bbox[0]) + pad * 2)
    img_h = max(1, (bbox[3] - bbox[1]) + pad * 2)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), visual, font=font, fill=(*fill_rgb, 255))

    draw_w = img_w / scale
    draw_h = img_h / scale
    if centered:
        draw_x = x + (max_width - draw_w) / 2
    else:
        draw_x = x
    draw_y = y - draw_h * 0.72

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), draw_x, draw_y, width=draw_w, height=draw_h, mask="auto")
    return y - max_size * 1.35


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

    # Match FE `QRCodeSVG` (level H, includeMargin=false → quiet zone 0 modules)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=0,
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
    _recolor_drawing_brand(drawing)
    _SYMBOL_DRAWING = drawing
    return drawing


def _recolor_drawing_brand(node: Shape | Group | Drawing) -> None:
    """Map SVG fills to brand navy / copper (same hex as the FE preview)."""
    fill = getattr(node, "fillColor", None)
    if isinstance(fill, Color):
        r, g, b = float(fill.red), float(fill.green), float(fill.blue)
        if r > 0.5 and g < 0.5:
            node.fillColor = COPPER
        else:
            node.fillColor = NAVY
    contents = getattr(node, "contents", None)
    if contents:
        for child in contents:
            _recolor_drawing_brand(child)


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
    stacked: bool = False,
    line_size: float | None = None,
    line_gap: float = 1.65,
) -> float:
    """Draw ID + serial at the *same* font size; returns y below last line.

    Design A / C use ``stacked=True`` so SN sits on its own line under Asset ID.
    """
    # One shared size for ID and SN (fit to the longer of the two lines)
    target = line_size if line_size is not None else size_ref * 0.034
    id_probe = f"ID {label}"
    sn_probe = f"SN {serial}"
    shared_sz = min(
        _fit_text(c, id_probe if not contains_arabic(label) else f"ID {'م' * max(4, len(label))}", font, target, width),
        _fit_text(c, sn_probe if not contains_arabic(serial) else f"SN {'م' * max(4, len(serial))}", font, target, width),
    )

    def _draw_prefix_value(y_pos: float, prefix: str, value: str) -> float:
        prefix_disp = f"{prefix} "
        sz = shared_sz
        c.setFillColor(MUTED)
        c.setFont(font, sz)
        prefix_w = c.stringWidth(prefix_disp, font, sz)

        if contains_arabic(value):
            if centered:
                from PIL import ImageFont

                visual = reshape_text(value, for_ltr_draw=True)
                scale = 3.0
                pf = ImageFont.truetype(str(_NOTO_PATH), max(8, int(sz * scale)))
                bb = pf.getbbox(visual)
                val_w = (bb[2] - bb[0]) / scale
                total = prefix_w + val_w
                left = x + (width - total) / 2
                val_max = max(8.0, width - prefix_w)
            else:
                left = x
                val_max = max(8.0, width - prefix_w)
            c.drawString(left, y_pos, prefix_disp)
            _draw_arabic_pil_line(
                c,
                value,
                x=left + prefix_w,
                y=y_pos,
                max_width=val_max,
                max_size=sz,
                fill_rgb=_RGB_MUTED,
                centered=False,
            )
            return y_pos - sz * line_gap

        value_w = c.stringWidth(value, font, sz)
        total = prefix_w + value_w
        left = x + (width - total) / 2 if centered else x
        c.drawString(left, y_pos, prefix_disp)
        c.drawString(left + prefix_w, y_pos, value)
        return y_pos - sz * line_gap

    if stacked or contains_arabic(label) or contains_arabic(serial):
        sn_y = _draw_prefix_value(y, "ID", label)
        return _draw_prefix_value(sn_y, "SN", serial)

    line_probe = f"ID {label}  ·  SN {serial}"
    sz = _fit_text(c, line_probe, font, target, width)
    c.setFillColor(MUTED)
    c.setFont(font, sz)
    if centered:
        c.drawCentredString(x + width / 2, y, line_probe)
    else:
        c.drawString(x, y, line_probe)
    return y - sz * line_gap


def render_docked_square_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
    qr_payload: str | None = None,
) -> bytes:
    """Design A — matches FE ``AssetStickerPreview`` (square, copper ear, stacked copy)."""
    side = clamp_label_size_mm(size_mm, design=DESIGN_A) * mm
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(side, side))
    c.setTitle("Orbit asset sticker A")
    font = _pick_font()
    fields = _asset_fields(asset, client_name, qr_payload=qr_payload)

    # FE: rounded-[18px] border-[4.5px] p-3 on ~280px card
    pad = side * 0.055
    radius = side * 0.064
    border_w = max(2.4, side * 0.016)

    c.setFillColor(white)
    c.roundRect(0, 0, side, side, radius, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(border_w)
    c.roundRect(border_w / 2, border_w / 2, side - border_w, side - border_w, radius, fill=0, stroke=1)

    # Copper ear — FE clip-path top-right triangle (~h-5 w-5 on 280px ≈ 7%)
    corner = side * 0.075
    c.setFillColor(COPPER)
    path = c.beginPath()
    path.moveTo(side, side)
    path.lineTo(side - corner, side)
    path.lineTo(side, side - corner)
    path.close()
    c.drawPath(path, fill=1, stroke=0)

    text_w = side - 2 * pad
    text_x = pad
    # FE type scale on 280px: company 10px, name 12px, meta 10px → ~3.6% / 4.3% / 3.6%
    company_size = side * 0.036
    name_size = side * 0.043
    meta_size = side * 0.036
    gap = side * 0.018

    # Top → bottom stack (same order as FE)
    y = side - pad - company_size * 0.15
    y = _draw_text_line(
        c,
        fields["company_disp"],
        x=text_x,
        y=y,
        max_width=text_w,
        max_size=company_size,
        font=font,
        fill_cmyk=NAVY,
        fill_rgb=_RGB_NAVY,
        centered=True,
    )
    y -= gap

    # FE QR ≈ 156/280 ≈ 55.7% of side
    qr_size = side * 0.555
    qr_x = (side - qr_size) / 2
    # Place QR just below company; keep room for name + ID + SN under it
    bottom_block = pad + meta_size * 3.6 + name_size * 1.5 + gap * 2
    qr_y = max(bottom_block, y - gap - qr_size)
    # If company sat high, center QR in the middle band
    if qr_y + qr_size > y - gap:
        qr_y = y - gap - qr_size
    _draw_vector_qr(c, fields["payload"], x=qr_x, y=qr_y, size=qr_size)

    y = qr_y - gap * 1.2
    y = _draw_text_line(
        c,
        fields["name"],
        x=text_x,
        y=y,
        max_width=text_w,
        max_size=name_size,
        font=font,
        fill_cmyk=INK,
        fill_rgb=_RGB_INK,
        centered=True,
    )
    y -= gap * 0.85
    _draw_meta_lines(
        c,
        font=font,
        x=text_x,
        y=y,
        width=text_w,
        label=fields["label"],
        serial=fields["serial"],
        size_ref=side,
        centered=True,
        stacked=True,
        line_size=meta_size,
        line_gap=1.7,
    )

    c.showPage()
    c.save()
    return buf.getvalue()


def render_field_tag_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
    qr_payload: str | None = None,
) -> bytes:
    """Design C — matches FE preview: copper spine · QR · stacked copy (no hang hole)."""
    width = clamp_label_size_mm(size_mm, design=DESIGN_C) * mm
    height = width * FIELD_TAG_ASPECT
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setTitle("Orbit asset sticker C")
    font = _pick_font()
    fields = _asset_fields(asset, client_name, qr_payload=qr_payload)

    # FE: border-[3.5px] rounded-[14px] on ~340×198, spine 3.5%, QR ~112px (~56% of height)
    border_w = max(2.0, width * 0.0105)
    radius = height * 0.07
    pad_y = height * 0.07
    pad_r = width * 0.05

    c.setFillColor(white)
    c.roundRect(0, 0, width, height, radius, fill=1, stroke=0)
    c.setStrokeColor(NAVY)
    c.setLineWidth(border_w)
    c.roundRect(border_w / 2, border_w / 2, width - border_w, height - border_w, radius, fill=0, stroke=1)

    spine_w = width * 0.035
    c.setFillColor(COPPER)
    c.rect(0, 0, spine_w, height, fill=1, stroke=0)

    qr_size = height * 0.565
    qr_x = spine_w + width * 0.035
    qr_y = (height - qr_size) / 2
    _draw_vector_qr(c, fields["payload"], x=qr_x, y=qr_y, size=qr_size)

    copy_x = qr_x + qr_size + width * 0.03
    copy_w = max(28.0, width - pad_r - copy_x)

    # FE on ~198px height: company 9px, name 13px, meta 10px
    company_size = height * 0.045
    name_size = height * 0.066
    meta_size = height * 0.050
    gap = height * 0.028

    # Vertically center the text stack in the copy column (like FE flex justify-center)
    stack_h = company_size * 1.35 + gap + name_size * 1.45 + gap * 1.2 + meta_size * 1.7 * 2
    y = (height + stack_h) / 2 - company_size * 0.2
    y = min(y, height - pad_y - company_size * 0.1)

    y = _draw_text_line(
        c,
        fields["company_disp"],
        x=copy_x,
        y=y,
        max_width=copy_w,
        max_size=company_size,
        font=font,
        fill_cmyk=COPPER,
        fill_rgb=_RGB_COPPER,
        centered=False,
    )
    y -= gap * 0.4

    name = fields["name"]
    if contains_arabic(name) or len(name) < 32:
        y = _draw_text_line(
            c,
            name,
            x=copy_x,
            y=y,
            max_width=copy_w,
            max_size=name_size,
            font=font,
            fill_cmyk=NAVY,
            fill_rgb=_RGB_NAVY,
            centered=False,
        )
    else:
        parts = name.split()
        line1, line2 = name, ""
        for i in range(len(parts) - 1, 0, -1):
            left = " ".join(parts[:i])
            right = " ".join(parts[i:])
            if c.stringWidth(left, font, name_size) <= copy_w:
                line1, line2 = left, right
                break
        y = _draw_text_line(
            c,
            line1,
            x=copy_x,
            y=y,
            max_width=copy_w,
            max_size=name_size,
            font=font,
            fill_cmyk=NAVY,
            fill_rgb=_RGB_NAVY,
            centered=False,
        )
        if line2:
            y = _draw_text_line(
                c,
                line2,
                x=copy_x,
                y=y,
                max_width=copy_w,
                max_size=name_size * 0.92,
                font=font,
                fill_cmyk=NAVY,
                fill_rgb=_RGB_NAVY,
                centered=False,
            )

    y -= gap * 1.1
    _draw_meta_lines(
        c,
        font=font,
        x=copy_x,
        y=y,
        width=copy_w,
        label=fields["label"],
        serial=fields["serial"],
        size_ref=height,
        centered=False,
        stacked=True,
        line_size=meta_size,
        line_gap=1.85,
    )

    c.showPage()
    c.save()
    return buf.getvalue()


def render_asset_sticker_pdf(
    asset: Asset,
    *,
    client_name: str | None = None,
    size_mm: float | None = None,
    design: str | None = None,
    qr_payload: str | None = None,
) -> bytes:
    kind = normalize_label_design(design)
    if kind == DESIGN_C:
        return render_field_tag_sticker_pdf(
            asset, client_name=client_name, size_mm=size_mm, qr_payload=qr_payload
        )
    return render_docked_square_sticker_pdf(
        asset, client_name=client_name, size_mm=size_mm, qr_payload=qr_payload
    )


def sticker_pdf_to_png(pdf_bytes: bytes, *, scale: float = 2.75) -> bytes:
    """Rasterize the first PDF page so the in-app preview matches print exactly."""
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        page = doc[0]
        pil = page.render(scale=scale).to_pil().convert("RGB")
        out = BytesIO()
        pil.save(out, format="PNG", optimize=True)
        return out.getvalue()
    finally:
        doc.close()
