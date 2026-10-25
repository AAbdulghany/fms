# Program A — Asset + billing core

**Customer promise:** Vertical templates, QR tags, parts on bill + VAT, downtime fields.  
**Window:** S1–S6 (~12 weeks, 2 engineers).  
**Status:** A1 + A2 **shipped**; A3–A4 **implemented on branch** (see [PROGRAM_A_COMPLETION_REPORT.md](./PROGRAM_A_COMPLETION_REPORT.md)); A5 next.

## Slices

### A1. Verticals + AssetType catalog — DONE

- Seeded Verticals; tenant AssetType library from platform templates.
- Register: pick type / create-if-missing; apply defaults (criticality, max age, PM).
- Issues #28–#30 · PR #31.

### A2. Printable QR — DONE

- Opaque `AssetTag.token`; public `/a/{token}`; PDF sticker Designs A/C; anon report + rate limit.
- Issues #32–#34 · PR #35 · [AgDR-A2](../engineering/AgDR-A2-qr-public-url.md).

### A3–A4. Inventory lite + billing — ACTIVE

See [A3_A4_PARTS_VAT.md](./A3_A4_PARTS_VAT.md).

- **v1 inventory:** parts catalog UI + `WorkOrderPart` (qty used) → invoice lines. Stock ledger (`StockMovement`) = **A3b** only if on-hand qty is required.
- **VAT:** `TaxProfile` per tenant (rate, inclusive/exclusive, rounding); snapshot on invoice issue; stop `tax = 0` hardcode in [`billing.py`](../../backend/app/services/billing.py).
- Admin UI for PricingProfile / Contract (API exists in `domains/billing/catalog.py`; UI missing).

### A5. Data foundation for later AI — IN PROGRESS (#39–#41)

- Downtime start/end on WO; failure/symptom codes catalog; `GET /assets/{id}/work-order-history`.
- Migration `b9c0d1e2f3a4`; WO detail diagnostics panel; asset maintenance history columns.

### Roles (light in A)

- Display naming aligned: Platform Super Admin; Tenant Company Admin / Engineer / Technician; Client Admin / Site Manager.
- No permission rewrite in A (`require_permission` in B foundations).

## Baseline (pre-A3)

| Need | Today |
|------|-------|
| Parts | `Part` catalog + report `parts_used` → invoice lines — **no stock, thin UI** |
| VAT | `tax_sar` hardcoded `0` in `_compute_invoice_lines` |
| Pricing / Contract | API present; **admin UI missing** |
