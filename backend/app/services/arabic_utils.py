from typing import Any

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_LIBS = True
except ImportError:
    HAS_ARABIC_LIBS = False

def reshape_text(text: str) -> str:
    """
    Reshapes Arabic text for correct rendering in PDF engines.
    If libraries are missing, returns the original text.
    """
    if not text or not HAS_ARABIC_LIBS:
        return text
    
    # 1. Reshape characters (connects the letters)
    reshaped_text = arabic_reshaper.reshape(text)
    
    # 2. Apply Bidi algorithm (fixes the Right-to-Left direction)
    bidi_text = get_display(reshaped_text)
    
    return bidi_text
