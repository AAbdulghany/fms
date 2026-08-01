import re

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_LIBS = True
except ImportError:
    HAS_ARABIC_LIBS = False

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def _contains_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text))


def reshape_text(text: str) -> str:
    """
    Reshapes Arabic text for correct rendering in PDF engines.
    Latin-only strings are returned unchanged.
    """
    if not text or not HAS_ARABIC_LIBS or not _contains_arabic(text):
        return text

    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)
