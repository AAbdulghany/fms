"""Register Unicode fonts for ReportLab PDF output."""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"
_NOTO_PATH = _FONT_DIR / "NotoSansArabic-Regular.ttf"
_NOTO_NAME = "NotoSansArabic"
_registered = False


def ensure_pdf_fonts() -> str:
    """Register Noto Sans Arabic when bundled; return body font name for Paragraph styles."""
    global _registered
    if not _registered and _NOTO_PATH.is_file():
        pdfmetrics.registerFont(TTFont(_NOTO_NAME, str(_NOTO_PATH)))
        _registered = True
        return _NOTO_NAME
    if _registered:
        return _NOTO_NAME
    return "Helvetica"
