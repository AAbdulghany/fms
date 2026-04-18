from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Contract,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    MaintenanceReport,
    Part,
    PricingProfile,
    ReportStatus,
    Urgency,
    WorkOrder,
    WorkOrderStatus,
)


def _d(x: Any) -> Decimal:
    if x is None:
        return Decimal("0")
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def _sum_labor_hours(answers: dict[str, Any]) -> Decimal:
    total = Decimal("0")
    raw = answers.get("labor_log")
    if not raw:
        return total
    if isinstance(raw, list):
        for row in raw:
            if isinstance(row, dict) and "hours" in row:
                total += _d(row["hours"])
    return total


def _parts_lines(
    db: Session,
    tenant_id: UUID,
    answers: dict[str, Any],
    markup_percent: Decimal,
) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    raw = answers.get("parts_used")
    if not raw or not isinstance(raw, list):
        return lines
    for i, row in enumerate(raw):
        if not isinstance(row, dict):
            continue
        sku = str(row.get("sku", "")).strip()
        qty = _d(row.get("quantity", row.get("qty", 1)))
        if not sku:
            continue
        part = db.scalar(
            select(Part).where(Part.tenant_id == tenant_id, Part.sku == sku)
        )
        base = _d(part.unit_cost_sar) if part else Decimal("0")
        unit_with_markup = (base * (Decimal("1") + markup_percent / Decimal("100"))).quantize(
            Decimal("0.01")
        )
        amount = (qty * unit_with_markup).quantize(Decimal("0.01"))
        name = part.name if part else sku
        lines.append(
            {
                "line_type": "parts",
                "description": f"{name} ({sku})",
                "quantity": qty,
                "unit_price_sar": unit_with_markup,
                "amount_sar": amount,
                "source_ref": {"field": "parts_used", "index": i},
            }
        )
    return lines


def next_invoice_number(db: Session, tenant_id: UUID) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"{year}-"
    rows = db.scalars(
        select(Invoice.number).where(
            Invoice.tenant_id == tenant_id,
            Invoice.number.startswith(prefix),
        )
    ).all()
    max_n = 0
    for num in rows:
        try:
            n = int(num.split("-")[-1])
            max_n = max(max_n, n)
        except ValueError:
            continue
    return f"{prefix}{max_n + 1:05d}"


def ensure_can_invoice(wo: WorkOrder, report: Optional[MaintenanceReport]) -> None:
    if report is None:
        raise ValueError("REPORT_REQUIRED")
    if report.status != ReportStatus.approved:
        raise ValueError("REPORT_NOT_APPROVED")
    if wo.status not in (WorkOrderStatus.verified, WorkOrderStatus.closed):
        raise ValueError("WORK_ORDER_NOT_VERIFIED")


ALLOWED_INVOICE_CURRENCIES = frozenset({"EGP", "SAR", "USD", "EUR"})


def build_invoice_for_work_order(
    db: Session, wo: WorkOrder, currency_override: Optional[str] = None
) -> Invoice:
    """Create a draft invoice from an approved work order.

    All line items and totals are computed in **SAR** (pricing profiles use ``*_sar`` fields).
    ``Invoice.currency`` is the **presentation / contractual** currency code; there is **no FX
    conversion** yet—non-SAR values label the same SAR amounts for display until rates exist.
    """
    report = wo.report
    ensure_can_invoice(wo, report)
    existing = db.scalar(select(Invoice).where(Invoice.work_order_id == wo.id))
    if existing:
        raise ValueError("INVOICE_EXISTS")

    contract = db.scalar(
        select(Contract).where(
            Contract.client_id == wo.client_id,
            Contract.tenant_id == wo.tenant_id,
            Contract.status == "active",
        )
    )
    if not contract:
        raise ValueError("NO_ACTIVE_CONTRACT")

    profile = db.get(PricingProfile, contract.pricing_profile_id)
    if not profile:
        raise ValueError("PRICING_NOT_FOUND")

    hourly = _d(profile.hourly_rate_sar)
    markup = _d(profile.parts_markup_percent)
    service_fee = _d(profile.default_service_fee_sar)
    emergency_pct = _d(profile.emergency_surcharge_percent)

    answers = report.answers_json or {}
    labor_hours = _sum_labor_hours(answers)
    labor_amount = (labor_hours * hourly).quantize(Decimal("0.01"))

    line_payloads: list[dict[str, Any]] = []
    if labor_hours > 0:
        line_payloads.append(
            {
                "line_type": "labor",
                "description": "Labor",
                "quantity": labor_hours,
                "unit_price_sar": hourly,
                "amount_sar": labor_amount,
                "source_ref": {"field": "labor_log"},
            }
        )
    line_payloads.extend(_parts_lines(db, wo.tenant_id, answers, markup))

    if service_fee > 0:
        line_payloads.append(
            {
                "line_type": "fee",
                "description": "Service fee",
                "quantity": Decimal("1"),
                "unit_price_sar": service_fee,
                "amount_sar": service_fee,
                "source_ref": {"field": "pricing_profile", "id": str(profile.id)},
            }
        )

    subtotal = sum(_d(p["amount_sar"]) for p in line_payloads)
    if wo.urgency == Urgency.emergency and emergency_pct > 0:
        sur = (subtotal * emergency_pct / Decimal("100")).quantize(Decimal("0.01"))
        line_payloads.append(
            {
                "line_type": "surcharge",
                "description": "Emergency surcharge",
                "quantity": Decimal("1"),
                "unit_price_sar": sur,
                "amount_sar": sur,
                "source_ref": {"rule": "emergency_surcharge_percent"},
            }
        )
        subtotal += sur

    subtotal = subtotal.quantize(Decimal("0.01"))
    tax = Decimal("0")
    total = (subtotal + tax).quantize(Decimal("0.01"))

    cur = (currency_override or contract.currency or "SAR").strip().upper()
    if cur not in ALLOWED_INVOICE_CURRENCIES:
        raise ValueError("INVALID_CURRENCY")

    inv = Invoice(
        tenant_id=wo.tenant_id,
        client_id=wo.client_id,
        work_order_id=wo.id,
        contract_id=contract.id,
        number=next_invoice_number(db, wo.tenant_id),
        status=InvoiceStatus.draft,
        subtotal_sar=subtotal,
        tax_sar=tax,
        total_sar=total,
        currency=cur,
        due_date=date.today(),
        metadata_json={"work_order_id": str(wo.id)},
    )
    db.add(inv)
    db.flush()
    for p in line_payloads:
        db.add(
            InvoiceLineItem(
                invoice_id=inv.id,
                line_type=p["line_type"],
                description=p["description"],
                quantity=p["quantity"],
                unit_price_sar=p["unit_price_sar"],
                amount_sar=p["amount_sar"],
                source_ref=p.get("source_ref") or {},
            )
        )
    db.flush()
    return inv
