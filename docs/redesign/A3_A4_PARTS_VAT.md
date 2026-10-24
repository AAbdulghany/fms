# A3–A4 — Parts catalog + WO consumption + TaxProfile VAT

**Program:** A · **Sprints:** S4–S5  
**Branch:** `feature/a3-a4-parts-vat`  
**Status:** Build in progress (Agile docs + BE VAT/parts + FE shells)  
**Tickets:** [#36](https://github.com/AAbdulghany/fms/issues/36) BE · [#37](https://github.com/AAbdulghany/fms/issues/37) FE · [#38](https://github.com/AAbdulghany/fms/issues/38) QA

## Problem

Invoices still compute `tax = 0`. Parts exist as a catalog and via report `parts_used`, but there is no first-class WO parts line UX, and Pricing/Contract admin UI is missing. Customers cannot see qty × price × VAT on the bill.

## Goals (MVP)

1. **Parts catalog UI** (CRUD) for company admins — wraps existing `/parts-catalog` API.
2. **WorkOrderPart** (or equivalent) — qty used on a WO, linked to catalog Part; feeds invoice line generation.
3. **TaxProfile** per tenant — rate %, inclusive vs exclusive, rounding mode; **snapshot** onto invoice at issue.
4. Replace hardcoded tax in `backend/app/services/billing.py`.
5. **PricingProfile + Contract admin UI** (API already exists).
6. Full unit/API + Playwright acceptance scenarios for QA review.

## Non-goals

- Stock ledger / `StockMovement` (A3b)
- ZATCA / ETA e-invoice
- Multi-currency FX conversion
- Changing `_sar` column names this sprint (document only)

## Artifacts

| Artifact | Path |
|----------|------|
| PRD | [`docs/product/PRD_A3_A4_PARTS_VAT.md`](../product/PRD_A3_A4_PARTS_VAT.md) |
| UX flows | [`docs/product/UX_A3_A4_PARTS_VAT_FLOWS.md`](../product/UX_A3_A4_PARTS_VAT_FLOWS.md) |
| Tech design | [`docs/engineering/designs/A3_A4_PARTS_VAT_TECH_DESIGN.md`](../engineering/designs/A3_A4_PARTS_VAT_TECH_DESIGN.md) |
| AgDR TaxProfile | [`docs/engineering/AgDR-A3-tax-profile.md`](../engineering/AgDR-A3-tax-profile.md) |
| Sprint cycle + tests | [`docs/engineering/cycles/A3_A4_SPRINT_CYCLE.md`](../engineering/cycles/A3_A4_SPRINT_CYCLE.md) |

## Baseline code

- Models: `Part`, `PricingProfile`, `Contract`, `Invoice`, `InvoiceLineItem` — `backend/app/models/billing.py`
- Catalog API: `backend/app/domains/billing/catalog.py`
- Invoice compute: `backend/app/services/billing.py` (`tax = Decimal("0")`)
- Report field: `parts_used` in standard inspection schema
