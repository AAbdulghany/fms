# UX — A3–A4 Parts & VAT flows

**Date:** 2026-10-24 · **i18n:** AR default + EN · **Layout:** existing Orbit shell

## F-PART-01 — Parts catalog (admin)

1. Nav → **Billing / Parts** (`/billing/parts`)
2. List SKU, name, unit cost (SAR)
3. Create / edit modal; delete only if unused on open WOs (v1: soft-hide optional — MVP allow delete with confirm)
4. Empty state: “No parts yet — add your first SKU”

## F-TAX-01 — Tax profile (admin)

1. Nav → **Billing / Tax** (`/billing/tax`)
2. Show default profile: rate %, inclusive toggle, rounding (HALF_UP)
3. Save; toast success; note: “Changes apply to **new** invoices only”

## F-PRICE-01 — Pricing & contracts (admin)

1. `/billing/pricing` — list/create PricingProfiles
2. `/billing/contracts` — list/create Contracts (client + profile + currency)
3. Mirror field names from existing API schemas

## F-WO-01 — Attach parts on work order

1. WO detail → **Parts used** section
2. Search/select catalog part → qty → Add
3. List shows name, SKU, qty, unit cost
4. Remove row before invoice generated

## F-INV-01 — Invoice tax visibility

1. Invoice detail / preview: Subtotal · Tax (rate %) · Total
2. If snapshot present, show “VAT {rate}% ({inclusive|exclusive})”
3. PDF already shows Tax line — keep consistent amounts
