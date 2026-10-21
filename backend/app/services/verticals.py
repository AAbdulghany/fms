"""A1 — Helper: resolve a vertical from a code or activity_type alias.

Used by client create / update / provision and the backfill CLI.
Single entry-point: ``resolve_vertical(db, code)`` keeps the alias map
in one place (``asset_type_catalog_data.ACTIVITY_TYPE_ALIAS_MAP``).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_types import Vertical
from app.services.asset_type_catalog_data import ACTIVITY_TYPE_ALIAS_MAP


def resolve_vertical(db: Session, code: str | None) -> Vertical | None:
    """Return the Vertical row for *code* (identity or alias), or ``None``.

    The lookup is case-insensitive.  Unknown codes return ``None``.
    Callers that treat unknown codes as an error should raise 400 themselves.
    """
    if not code:
        return None
    normalised = code.strip().lower()
    canonical = ACTIVITY_TYPE_ALIAS_MAP.get(normalised, normalised)
    return db.scalar(
        select(Vertical).where(Vertical.code == canonical, Vertical.is_active.is_(True))
    )
