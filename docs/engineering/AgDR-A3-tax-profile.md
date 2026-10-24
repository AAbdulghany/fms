# AgDR-A3 — TaxProfile for invoice VAT

**Status:** Accepted  
**Date:** 2026-10-24  
**Program:** A3–A4  
**Tickets:** #36–#38

## Decision

Each tenant has one or more **TaxProfile** rows. Invoice generation loads the **default** profile (or the single active profile) and computes VAT as follows:

| Mode | Formula |
|------|---------|
| Exclusive (`tax_inclusive=false`) | `tax = round(subtotal × rate/100)`; `total = subtotal + tax` |
| Inclusive (`tax_inclusive=true`) | `tax = round(subtotal − subtotal/(1+rate/100))`; display subtotal stays pre-split line sum; total = line subtotal (tax embedded) — **MVP: treat inclusive as tax extracted from subtotal, total unchanged** |

- `rate_percent`: Numeric(6,3), e.g. `15.000`
- `rounding`: `HALF_UP` (default) using `decimal.ROUND_HALF_UP` to 2 places
- On **draft create**, store snapshot under `invoice.metadata_json["tax_profile"]`:
  `{id, name, rate_percent, tax_inclusive, rounding}`
- Issued invoices **never** recompute tax from the live profile

**Default seed:** 15% exclusive, HALF_UP, name `Standard VAT` (KSA-friendly).

## Out of scope

- ZATCA / ETA e-invoice payloads
- Per-line tax codes / multi-rate mixed invoices
- Multi-country profiles beyond rate field (future: `country_code`)

## Alternatives rejected

| Option | Why not |
|--------|---------|
| Hardcode 15% in code | Blocks other GCC/EG rates |
| Live profile on every read | Historical invoices drift when admin edits rate |
| Tax on PricingProfile | Mixes commercial rates with fiscal policy |

## Consequences

- New tables `tax_profiles`, `work_order_parts`
- `billing._compute_invoice_lines` replaces `tax = 0`
- Admin UI for TaxProfile; FE must not imply e-invoice compliance
