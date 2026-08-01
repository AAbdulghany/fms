from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Contract,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    MaintenanceReport,
    Part,
    PricingProfile,
    ReportStatus,
    User,
    Urgency,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.services.report_context import merge_report_answers


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


def _billing_inspector(db: Session, wo: WorkOrder) -> User | None:
    if wo.assignee_user:
        return wo.assignee_user
    if wo.assignee_user_id:
        return db.get(User, wo.assignee_user_id)
    return None


def _billing_answers(db: Session, wo: WorkOrder, report: MaintenanceReport) -> dict[str, Any]:
    raw = report.answers_json or {}
    inspector = _billing_inspector(db, wo)
    if inspector:
        return merge_report_answers(db, wo, inspector, raw)
    return raw


def _resolve_labor_hours(answers: dict[str, Any]) -> Decimal:
    hours = _sum_labor_hours(answers)
    if hours > 0:
        return hours
    elapsed = answers.get("time_elapsed_hours")
    if elapsed not in (None, "", 0):
        return _d(elapsed)
    return Decimal("0")


def _labor_line_description(wo: WorkOrder) -> str:
    parts = ["Labor"]
    if wo.title:
        parts.append(f"— {wo.title.strip()}")
    asset = wo.asset
    if asset:
        label = (asset.name or asset.label_code or "").strip()
        if label:
            parts.append(f"({label})")
    site = wo.site
    if site and site.name:
        parts.append(f"@ {site.name.strip()}")
    return " ".join(parts)


def _service_fee_description(wo: WorkOrder) -> str:
    source_label = wo.source.value.replace("_", " ").title()
    if wo.title:
        return f"Service fee — {source_label}: {wo.title.strip()}"
    return f"Service fee — {source_label} maintenance"


def _work_summary_from_answers(answers: dict[str, Any], wo: WorkOrder) -> str:
    for key in (
        "findings_defects",
        "recommended_actions",
        "tests_performed",
        "work_summary",
        "summary",
    ):
        val = answers.get(key)
        if val and str(val).strip():
            return str(val).strip()[:500]
    return (wo.description or "")[:500]


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
    if report.status not in (ReportStatus.submitted, ReportStatus.approved):
        raise ValueError("REPORT_NOT_APPROVED")
    if wo.status not in (WorkOrderStatus.verified, WorkOrderStatus.closed):
        raise ValueError("WORK_ORDER_NOT_VERIFIED")


ALLOWED_INVOICE_CURRENCIES = frozenset({"EGP", "SAR", "USD", "EUR"})


def _compute_invoice_lines(
    db: Session,
    wo: WorkOrder,
    report: MaintenanceReport,
    currency_override: Optional[str] = None,
) -> dict[str, Any]:
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

    answers = _billing_answers(db, wo, report)
    labor_hours = _resolve_labor_hours(answers)
    labor_amount = (labor_hours * hourly).quantize(Decimal("0.01"))

    line_payloads: list[dict[str, Any]] = []
    if labor_hours > 0:
        line_payloads.append(
            {
                "line_type": "labor",
                "description": _labor_line_description(wo),
                "quantity": labor_hours,
                "unit_price_sar": hourly,
                "amount_sar": labor_amount,
                "source_ref": {
                    "field": "labor_log",
                    "work_order_id": str(wo.id),
                    "hours_source": "labor_log"
                    if _sum_labor_hours(answers) > 0
                    else "time_elapsed_hours",
                },
            }
        )
    line_payloads.extend(_parts_lines(db, wo.tenant_id, answers, markup))

    if service_fee > 0:
        line_payloads.append(
            {
                "line_type": "fee",
                "description": _service_fee_description(wo),
                "quantity": Decimal("1"),
                "unit_price_sar": service_fee,
                "amount_sar": service_fee,
                "source_ref": {
                    "field": "pricing_profile",
                    "id": str(profile.id),
                    "work_order_source": wo.source.value,
                },
            }
        )

    subtotal = sum(_d(p["amount_sar"]) for p in line_payloads)
    emergency_surcharge = Decimal("0")
    if wo.urgency == Urgency.emergency and emergency_pct > 0:
        sur = (subtotal * emergency_pct / Decimal("100")).quantize(Decimal("0.01"))
        emergency_surcharge = sur
        line_payloads.append(
            {
                "line_type": "surcharge",
                "description": "Emergency surcharge",
                "quantity": Decimal("1"),
                "unit_price_sar": sur,
                "amount_sar": sur,
                "source_ref": {
                    "rule": "emergency_surcharge_percent",
                    "percent": str(emergency_pct),
                },
            }
        )
        subtotal += sur

    subtotal = subtotal.quantize(Decimal("0.01"))
    tax = Decimal("0")
    total = (subtotal + tax).quantize(Decimal("0.01"))

    cur = (currency_override or contract.currency or "SAR").strip().upper()
    if cur not in ALLOWED_INVOICE_CURRENCIES:
        raise ValueError("INVALID_CURRENCY")

    parts_preview = [
        {
            "description": p["description"],
            "quantity": str(p["quantity"]),
            "amount_sar": str(p["amount_sar"]),
        }
        for p in line_payloads
        if p["line_type"] == "parts"
    ]

    summary = _work_summary_from_answers(answers, wo)

    return {
        "contract": contract,
        "currency": cur,
        "labor_hours": labor_hours,
        "labor_rate_sar": hourly,
        "labor_amount_sar": labor_amount,
        "service_fee_sar": service_fee if service_fee > 0 else Decimal("0"),
        "emergency_surcharge_sar": emergency_surcharge,
        "subtotal_sar": subtotal,
        "tax_sar": tax,
        "total_sar": total,
        "line_payloads": line_payloads,
        "parts": parts_preview,
        "work_summary": summary,
    }


def preview_invoice_for_work_order(
    db: Session, wo: WorkOrder, currency_override: Optional[str] = None
) -> dict[str, Any]:
    report = wo.report
    ensure_can_invoice(wo, report)
    existing = db.scalar(select(Invoice).where(Invoice.work_order_id == wo.id))
    if existing:
        raise ValueError("INVOICE_EXISTS")
    return _compute_invoice_lines(db, wo, report, currency_override)


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

    computed = _compute_invoice_lines(db, wo, report, currency_override)
    contract = computed["contract"]
    line_payloads = computed["line_payloads"]
    cur = computed["currency"]

    inv = Invoice(
        tenant_id=wo.tenant_id,
        client_id=wo.client_id,
        work_order_id=wo.id,
        contract_id=contract.id,
        number=next_invoice_number(db, wo.tenant_id),
        status=InvoiceStatus.draft,
        subtotal_sar=computed["subtotal_sar"],
        tax_sar=computed["tax_sar"],
        total_sar=computed["total_sar"],
        currency=cur,
        due_date=date.today(),
        metadata_json={
            "work_order_id": str(wo.id),
            "work_order_title": wo.title or "",
            "notes": "",
        },
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


def extract_invoice_charges(inv: Invoice) -> dict[str, Decimal]:
    """Summarize labor and service fee from invoice line items."""
    labor_hours = Decimal("0")
    labor_rate = Decimal("0")
    labor_amount = Decimal("0")
    service_fee = Decimal("0")
    for li in inv.line_items or []:
        if li.line_type == "labor":
            labor_hours = li.quantity or Decimal("0")
            labor_rate = li.unit_price_sar or Decimal("0")
            labor_amount = li.amount_sar or Decimal("0")
        elif li.line_type == "fee":
            service_fee = li.amount_sar or Decimal("0")
    return {
        "labor_hours": labor_hours,
        "labor_rate_sar": labor_rate,
        "labor_amount_sar": labor_amount,
        "service_fee_sar": service_fee,
    }


def _recompute_invoice_totals(inv: Invoice) -> None:
    subtotal = sum((li.amount_sar or Decimal("0")) for li in inv.line_items or [])
    inv.subtotal_sar = subtotal
    inv.total_sar = subtotal + (inv.tax_sar or Decimal("0"))


def apply_invoice_charge_edits(
    inv: Invoice,
    *,
    labor_hours: Decimal | None = None,
    labor_rate_sar: Decimal | None = None,
    service_fee_sar: Decimal | None = None,
) -> None:
    """Update labor / fee line items from edited charge fields (draft or approved)."""
    if inv.status not in (InvoiceStatus.draft, InvoiceStatus.approved):
        raise ValueError("INVOICE_NOT_EDITABLE")

    labor_li = next((li for li in inv.line_items or [] if li.line_type == "labor"), None)
    fee_li = next((li for li in inv.line_items or [] if li.line_type == "fee"), None)

    if labor_hours is not None or labor_rate_sar is not None:
        hours = labor_hours if labor_hours is not None else (labor_li.quantity if labor_li else Decimal("0"))
        rate = labor_rate_sar if labor_rate_sar is not None else (
            labor_li.unit_price_sar if labor_li else Decimal("0")
        )
        hours = max(Decimal("0"), hours)
        rate = max(Decimal("0"), rate)
        amount = (hours * rate).quantize(Decimal("0.01"))
        if hours > 0 and rate > 0:
            desc = labor_li.description if labor_li else "Labor"
            if labor_li:
                labor_li.quantity = hours
                labor_li.unit_price_sar = rate
                labor_li.amount_sar = amount
            else:
                inv.line_items.append(
                    InvoiceLineItem(
                        invoice_id=inv.id,
                        line_type="labor",
                        description=desc,
                        quantity=hours,
                        unit_price_sar=rate,
                        amount_sar=amount,
                        source_ref={"rule": "manual_charge_edit"},
                    )
                )
        elif labor_li and labor_li in (inv.line_items or []):
            inv.line_items.remove(labor_li)

    if service_fee_sar is not None:
        fee = max(Decimal("0"), service_fee_sar).quantize(Decimal("0.01"))
        if fee > 0:
            desc = fee_li.description if fee_li else "Service fee"
            if fee_li:
                fee_li.quantity = Decimal("1")
                fee_li.unit_price_sar = fee
                fee_li.amount_sar = fee
            else:
                inv.line_items.append(
                    InvoiceLineItem(
                        invoice_id=inv.id,
                        line_type="fee",
                        description=desc,
                        quantity=Decimal("1"),
                        unit_price_sar=fee,
                        amount_sar=fee,
                        source_ref={"rule": "manual_charge_edit"},
                    )
                )
        elif fee_li and fee_li in (inv.line_items or []):
            inv.line_items.remove(fee_li)

    # Recalculate emergency surcharge if present
    surcharge_li = next((li for li in inv.line_items or [] if li.line_type == "surcharge"), None)
    if surcharge_li:
        pct_raw = (surcharge_li.source_ref or {}).get("percent")
        if pct_raw is not None:
            pct = Decimal(str(pct_raw))
            base = sum(
                (li.amount_sar or Decimal("0"))
                for li in inv.line_items or []
                if li.line_type in ("labor", "fee")
            )
            sur = (base * pct / Decimal("100")).quantize(Decimal("0.01"))
            surcharge_li.unit_price_sar = sur
            surcharge_li.amount_sar = sur

    _recompute_invoice_totals(inv)


def recalculate_draft_invoice(db: Session, inv: Invoice) -> Invoice:
    """Replace draft invoice line items with fresh computation from linked WO + report."""
    if inv.status != InvoiceStatus.draft:
        raise ValueError("INVOICE_NOT_DRAFT")
    wo = db.scalars(
        select(WorkOrder)
        .where(WorkOrder.id == inv.work_order_id, WorkOrder.tenant_id == inv.tenant_id)
        .options(
            joinedload(WorkOrder.assignee_user),
            joinedload(WorkOrder.site),
            joinedload(WorkOrder.asset),
            joinedload(WorkOrder.report),
        )
    ).first()
    if not wo or not wo.report:
        raise ValueError("WORK_ORDER_NOT_FOUND")
    ensure_can_invoice(wo, wo.report)
    computed = _compute_invoice_lines(db, wo, wo.report, currency_override=inv.currency)
    for li in list(inv.line_items):
        db.delete(li)
    db.flush()
    inv.subtotal_sar = computed["subtotal_sar"]
    inv.tax_sar = computed["tax_sar"]
    inv.total_sar = computed["total_sar"]
    for p in computed["line_payloads"]:
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
