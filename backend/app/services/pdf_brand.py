"""Design tokens for PDF/HTML reports — mirrors ``src/styles/tokens.css``."""

from __future__ import annotations

from pathlib import Path

# Primary — Industrial Teal
PRIMARY_500 = "#0d7c8c"
PRIMARY_600 = "#0a6270"
PRIMARY_50 = "#e6f4f7"

# Secondary — Warm Orange
SECONDARY_500 = "#f57c00"

# Neutrals
NEUTRAL_0 = "#ffffff"
NEUTRAL_50 = "#fafaf9"
NEUTRAL_100 = "#f5f5f4"
NEUTRAL_200 = "#e7e5e4"
NEUTRAL_500 = "#78716c"
NEUTRAL_700 = "#44403c"
NEUTRAL_900 = "#1c1917"

# Semantic
SUCCESS_MAIN = "#10b981"
WARNING_MAIN = "#f59e0b"
ERROR_MAIN = "#ef4444"
ERROR_DARK = "#b91c1c"

FONT_BODY_AR = '"Noto Sans Arabic", "IBM Plex Sans Arabic", "Segoe UI", sans-serif'
FONT_BODY_EN = '"Inter", "Plus Jakarta Sans", "Segoe UI", sans-serif'

CONDITION_COLORS: dict[str, str] = {
    "good": SUCCESS_MAIN,
    "fair": WARNING_MAIN,
    "poor": ERROR_MAIN,
    "critical": ERROR_DARK,
}

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
LOGO_SVG_PATH = STATIC_DIR / "brand" / "orbit-logo.svg"
