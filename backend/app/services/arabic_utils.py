"""Arabic reshape helpers for PDF (ReportLab has no HarfBuzz)."""

from __future__ import annotations

import re

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def contains_arabic(text: str) -> bool:
    return bool(text and _ARABIC_RE.search(text))


def _contains_arabic(text: str) -> bool:
    return contains_arabic(text)


def _load_libs():
    """Lazy import so a late `pip install` is picked up without process tricks."""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return arabic_reshaper, get_display
    except ImportError:
        return None, None


# Back-compat for callers that check the flag at import time
try:
    import arabic_reshaper as _ar  # noqa: F401
    from bidi.algorithm import get_display as _gd  # noqa: F401

    HAS_ARABIC_LIBS = True
except ImportError:
    HAS_ARABIC_LIBS = False


def reshape_text(
    text: str,
    *,
    for_ltr_draw: bool = True,
    base_dir: str | None = None,
) -> str:
    """
    Prepare Arabic for engines that draw left-to-right without shaping.

    ``for_ltr_draw=True`` (default): reshape + bidi visual order for ReportLab/PIL LTR.
    ``for_ltr_draw=False``: reshape only (joined glyphs, logical order).
    ``base_dir``: optional ``'L'`` / ``'R'`` for python-bidi (use ``'R'`` on RTL pages
    so mixed Arabic+Latin lines like «مُعدّ لـ Hospital» keep natural order).
    """
    if not text or not contains_arabic(text):
        return text

    arabic_reshaper, get_display = _load_libs()
    if arabic_reshaper is None or get_display is None:
        return text

    reshaped = arabic_reshaper.reshape(text)
    if for_ltr_draw:
        if base_dir in ("L", "R"):
            return get_display(reshaped, base_dir=base_dir)
        return get_display(reshaped)
    return reshaped
