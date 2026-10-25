"""Design tokens for PDF/HTML reports — mirrors ``src/styles/tokens.css`` (Concept D)."""

from __future__ import annotations

from pathlib import Path

# Primary — Harbor Navy (Concept D · P1)
PRIMARY_500 = "#1d4e89"
PRIMARY_600 = "#173e6e"
PRIMARY_50 = "#e8eef7"

# Secondary — Copper Signal
SECONDARY_500 = "#e85d04"

# Neutrals — cool slate
NEUTRAL_0 = "#ffffff"
NEUTRAL_50 = "#f7f9fc"
NEUTRAL_100 = "#e8eef7"
NEUTRAL_200 = "#d5deea"
NEUTRAL_500 = "#64748b"
NEUTRAL_700 = "#334155"
NEUTRAL_900 = "#0f172a"

# Semantic
SUCCESS_MAIN = "#10b981"
WARNING_MAIN = "#f59e0b"
ERROR_MAIN = "#ef4444"
ERROR_DARK = "#b91c1c"

FONT_BODY_AR = '"Noto Sans Arabic", "IBM Plex Sans Arabic", "Segoe UI", sans-serif'
FONT_BODY_EN = '"IBM Plex Sans", "Inter", "Plus Jakarta Sans", "Segoe UI", sans-serif'

CONDITION_COLORS: dict[str, str] = {
    "good": SUCCESS_MAIN,
    "fair": WARNING_MAIN,
    "poor": ERROR_MAIN,
    "critical": ERROR_DARK,
}

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
# Kept for optional platform assets; customer PDFs use tenant initials, not Orbit mark.
LOGO_SVG_PATH = STATIC_DIR / "brand" / "orbit-logo.svg"


def company_initials(name: str) -> str:
    """Two-letter mark for the maintenance company header badge."""
    parts = [p for p in (name or "").split() if p and p[0].isalnum()]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    if parts:
        return parts[0][:2].upper()
    return "CO"
