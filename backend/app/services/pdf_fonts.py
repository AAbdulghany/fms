"""Register Unicode fonts for ReportLab PDF output (regular + bold)."""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"

_AR_REG = _FONT_DIR / "NotoSansArabic-Regular.ttf"
_AR_BOLD = _FONT_DIR / "NotoSansArabic-Bold.ttf"
_AR_XBOLD = _FONT_DIR / "NotoSansArabic-ExtraBold.ttf"
_LAT_REG = _FONT_DIR / "NotoSans-Regular.ttf"
_LAT_BOLD = _FONT_DIR / "NotoSans-Bold.ttf"
_LAT_XBOLD = _FONT_DIR / "NotoSans-ExtraBold.ttf"

_AR_FAMILY = "NotoSansArabic"
_LAT_FAMILY = "NotoSans"
_registered = False


def _register_face(name: str, path: Path) -> bool:
    if not path.is_file():
        return False
    pdfmetrics.registerFont(TTFont(name, str(path)))
    return True


def ensure_pdf_fonts(*, lang: str = "en") -> tuple[str, str]:
    """Register bundled fonts; return ``(regular_name, bold_name)`` for Paragraph styles.

    Arabic reports use Noto Sans Arabic; English uses Noto Sans (falls back to Helvetica).
    Callers that mix Latin + Arabic (company names, EN values on AR pages) should also
    use :func:`pdf_font_faces` — Arabic Bold/ExtraBold have no Latin glyphs.
    """
    faces = pdf_font_faces()
    use_ar = (lang or "en").lower().startswith("ar") and _AR_REG.is_file()
    if use_ar:
        return faces["ar_reg"], faces["ar_bold"]
    return faces["lat_reg"], faces["lat_bold"]


def pdf_font_faces() -> dict[str, str]:
    """Register all bundled faces; return ``ar_reg/ar_bold/lat_reg/lat_bold`` names.

    ``*_bold`` prefers ExtraBold when present (clearer title weight than Bold).
    """
    global _registered
    if not _registered:
        if _register_face(_AR_FAMILY, _AR_REG):
            bold_face = _AR_FAMILY
            if _register_face(f"{_AR_FAMILY}-Bold", _AR_BOLD):
                bold_face = f"{_AR_FAMILY}-Bold"
            if _register_face(f"{_AR_FAMILY}-ExtraBold", _AR_XBOLD):
                bold_face = f"{_AR_FAMILY}-ExtraBold"
            pdfmetrics.registerFontFamily(
                _AR_FAMILY,
                normal=_AR_FAMILY,
                bold=bold_face,
            )
        if _register_face(_LAT_FAMILY, _LAT_REG):
            bold_face = _LAT_FAMILY
            if _register_face(f"{_LAT_FAMILY}-Bold", _LAT_BOLD):
                bold_face = f"{_LAT_FAMILY}-Bold"
            if _register_face(f"{_LAT_FAMILY}-ExtraBold", _LAT_XBOLD):
                bold_face = f"{_LAT_FAMILY}-ExtraBold"
            pdfmetrics.registerFontFamily(
                _LAT_FAMILY,
                normal=_LAT_FAMILY,
                bold=bold_face,
            )
        _registered = True

    ar_reg = _AR_FAMILY if _AR_REG.is_file() else "Helvetica"
    if _AR_XBOLD.is_file():
        ar_bold = f"{_AR_FAMILY}-ExtraBold"
    elif _AR_BOLD.is_file():
        ar_bold = f"{_AR_FAMILY}-Bold"
    else:
        ar_bold = ar_reg

    lat_reg = _LAT_FAMILY if _LAT_REG.is_file() else "Helvetica"
    if _LAT_XBOLD.is_file():
        lat_bold = f"{_LAT_FAMILY}-ExtraBold"
    elif _LAT_BOLD.is_file():
        lat_bold = f"{_LAT_FAMILY}-Bold"
    elif lat_reg == "Helvetica":
        lat_bold = "Helvetica-Bold"
    else:
        lat_bold = lat_reg

    return {
        "ar_reg": ar_reg,
        "ar_bold": ar_bold,
        "lat_reg": lat_reg,
        "lat_bold": lat_bold,
    }
