"""A3 — TaxProfile VAT matrix (U-TAX-01..07)."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.models import TaxProfile
from app.services.tax_profiles import apply_tax, ensure_default_tax_profile, snapshot_tax_profile


def test_u_tax_01_default_profile(db_session, sample_tenant):
    tp = ensure_default_tax_profile(db_session, sample_tenant.id)
    db_session.commit()
    assert tp.rate_percent == Decimal("15")
    assert tp.tax_inclusive is False
    assert tp.is_default is True
    again = ensure_default_tax_profile(db_session, sample_tenant.id)
    assert again.id == tp.id


def test_u_tax_02_exclusive_15():
    tp = TaxProfile(
        id=uuid4(),
        tenant_id=uuid4(),
        name="t",
        rate_percent=Decimal("15"),
        tax_inclusive=False,
        rounding="HALF_UP",
        is_default=True,
    )
    tax, total, snap = apply_tax(Decimal("1000"), tp)
    assert tax == Decimal("150.00")
    assert total == Decimal("1150.00")
    assert snap["rate_percent"] == "15"


def test_u_tax_03_zero_rate():
    tp = TaxProfile(
        id=uuid4(),
        tenant_id=uuid4(),
        name="t",
        rate_percent=Decimal("0"),
        tax_inclusive=False,
        rounding="HALF_UP",
        is_default=True,
    )
    tax, total, _ = apply_tax(Decimal("1000"), tp)
    assert tax == Decimal("0")
    assert total == Decimal("1000.00")


def test_u_tax_04_inclusive_15():
    tp = TaxProfile(
        id=uuid4(),
        tenant_id=uuid4(),
        name="t",
        rate_percent=Decimal("15"),
        tax_inclusive=True,
        rounding="HALF_UP",
        is_default=True,
    )
    tax, total, _ = apply_tax(Decimal("1150"), tp)
    assert total == Decimal("1150.00")
    assert tax == Decimal("150.00")


def test_u_tax_05_rounding_half_up():
    tp = TaxProfile(
        id=uuid4(),
        tenant_id=uuid4(),
        name="t",
        rate_percent=Decimal("15"),
        tax_inclusive=False,
        rounding="HALF_UP",
        is_default=True,
    )
    # 10.01 * 15% = 1.5015 → 1.50
    tax, total, _ = apply_tax(Decimal("10.01"), tp)
    assert tax == Decimal("1.50")
    assert total == Decimal("11.51")


def test_u_tax_06_snapshot_shape(db_session, sample_tenant):
    tp = ensure_default_tax_profile(db_session, sample_tenant.id)
    snap = snapshot_tax_profile(tp)
    assert set(snap.keys()) >= {"id", "name", "rate_percent", "tax_inclusive", "rounding"}


def test_u_tax_07_snapshot_immutable_after_rate_change(db_session, sample_tenant):
    tp = ensure_default_tax_profile(db_session, sample_tenant.id)
    tax1, _, snap1 = apply_tax(Decimal("1000"), tp)
    tp.rate_percent = Decimal("0")
    db_session.commit()
    # Re-apply with mutated live profile
    tax2, _, _ = apply_tax(Decimal("1000"), tp)
    assert tax1 == Decimal("150.00")
    assert tax2 == Decimal("0")
    # Snapshot from before still records 15
    assert snap1["rate_percent"] == "15"
