"""A3 — TaxProfile ensure + VAT apply (AgDR-A3)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TaxProfile

DEFAULT_TAX_NAME = "Standard VAT"
_TWOPLACES = Decimal("0.01")


def _round(amount: Decimal, mode: str = "HALF_UP") -> Decimal:
    # Only HALF_UP in MVP; mode kept for snapshot / future modes
    _ = mode
    return amount.quantize(_TWOPLACES, rounding=ROUND_HALF_UP)


def ensure_default_tax_profile(db: Session, tenant_id: UUID) -> TaxProfile:
    existing = db.scalar(
        select(TaxProfile).where(
            TaxProfile.tenant_id == tenant_id,
            TaxProfile.is_default.is_(True),
        )
    )
    if existing:
        return existing
    named = db.scalar(
        select(TaxProfile).where(
            TaxProfile.tenant_id == tenant_id,
            TaxProfile.name == DEFAULT_TAX_NAME,
        )
    )
    if named:
        named.is_default = True
        db.flush()
        return named
    profile = TaxProfile(
        tenant_id=tenant_id,
        name=DEFAULT_TAX_NAME,
        rate_percent=Decimal("15"),
        tax_inclusive=False,
        rounding="HALF_UP",
        is_default=True,
    )
    db.add(profile)
    db.flush()
    return profile


def get_default_tax_profile(db: Session, tenant_id: UUID) -> TaxProfile:
    return ensure_default_tax_profile(db, tenant_id)


def snapshot_tax_profile(profile: TaxProfile) -> dict[str, Any]:
    return {
        "id": str(profile.id),
        "name": profile.name,
        "rate_percent": str(profile.rate_percent),
        "tax_inclusive": bool(profile.tax_inclusive),
        "rounding": profile.rounding or "HALF_UP",
    }


def apply_tax_rates(
    subtotal: Decimal,
    *,
    rate_percent: Decimal,
    tax_inclusive: bool = False,
    rounding: str = "HALF_UP",
    snapshot: dict[str, Any] | None = None,
) -> tuple[Decimal, Decimal, dict[str, Any]]:
    """Return (tax, total, snapshot) from explicit rate fields (per-client overrides)."""
    rate = Decimal(str(rate_percent or 0))
    snap = snapshot or {
        "rate_percent": str(rate),
        "tax_inclusive": bool(tax_inclusive),
        "rounding": rounding or "HALF_UP",
    }

    if rate <= 0:
        tax = Decimal("0")
        total = _round(subtotal, rounding)
        return tax, total, snap

    if tax_inclusive:
        divisor = Decimal("1") + (rate / Decimal("100"))
        net = _round(subtotal / divisor, rounding)
        tax = _round(subtotal - net, rounding)
        total = _round(subtotal, rounding)
        return tax, total, snap

    tax = _round(subtotal * rate / Decimal("100"), rounding)
    total = _round(subtotal + tax, rounding)
    return tax, total, snap


def apply_tax(
    subtotal: Decimal,
    profile: TaxProfile,
) -> tuple[Decimal, Decimal, dict[str, Any]]:
    """Return (tax, total, snapshot) for a money subtotal."""
    return apply_tax_rates(
        subtotal,
        rate_percent=Decimal(str(profile.rate_percent or 0)),
        tax_inclusive=bool(profile.tax_inclusive),
        rounding=profile.rounding or "HALF_UP",
        snapshot=snapshot_tax_profile(profile),
    )
