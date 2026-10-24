# PRD — A3–A4 Parts catalog + TaxProfile VAT

**Product:** Orbit AM  
**Date:** 2026-10-24  
**Tickets:** [#36](https://github.com/AAbdulghany/fms/issues/36) BE · [#37](https://github.com/AAbdulghany/fms/issues/37) FE · [#38](https://github.com/AAbdulghany/fms/issues/38) QA  
**Program docs:** [docs/redesign/A3_A4_PARTS_VAT.md](../redesign/A3_A4_PARTS_VAT.md)

## Problem

Invoices hardcode `tax = 0`. Parts exist in a catalog and via report `parts_used`, but there is no first-class WO parts UX and no Pricing/Contract/Tax admin UI. Customers cannot see qty × price × VAT on the bill.

## Personas

- **Farida (company admin)** — maintains parts catalog, tax profile, pricing profiles & contracts
- **Ahmed (technician)** — records parts used on a work order
- **Layla (client finance)** — reads invoice PDF with correct VAT

## Stories (MVP)

1. As Farida, I CRUD parts (SKU, name, unit cost) for my tenant.
2. As Farida, I set a default TaxProfile (rate %, inclusive/exclusive, rounding).
3. As Farida, I manage PricingProfiles and Contracts in the UI (API already exists).
4. As Ahmed, I attach catalog parts + qty on a work order (WorkOrderPart).
5. As Farida, when I generate an invoice, tax uses the TaxProfile and a **snapshot** is stored so later profile edits do not change issued totals.
6. As Layla, invoice detail shows subtotal, tax, total, and rate used.

## Acceptance criteria

### BE (#36)
- [ ] `tax_profiles` + `work_order_parts` migrations
- [ ] TaxProfile CRUD; default 15% exclusive on tenant bootstrap
- [ ] Invoice compute uses TaxProfile; matrix tests 0% / 15% excl / inclusive / rounding
- [ ] WorkOrderPart → invoice `parts` lines (report `parts_used` remains fallback)
- [ ] Snapshot in `invoice.metadata_json.tax_profile` at create
- [ ] Tenant isolation tests

### FE (#37)
- [ ] Parts catalog page
- [ ] TaxProfile settings
- [ ] PricingProfile + Contract admin UI
- [ ] WO detail parts section
- [ ] Invoice shows tax breakdown
- [ ] i18n EN/AR

### QA (#38)
- [ ] Scenario pack in sprint cycle reviewed
- [ ] E2E: part → WO → invoice tax > 0 at 15%
- [ ] E2E: profile change does not alter issued snapshot
- [ ] Negative cross-tenant

## Out of scope

- Stock ledger / `StockMovement` (A3b)
- ZATCA / ETA e-invoice
- FX conversion / renaming `*_sar` columns
