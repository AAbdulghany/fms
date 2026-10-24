# A3–A4 — Parts + VAT technical design

**Status:** Build  
**AgDR:** [AgDR-A3-tax-profile.md](../AgDR-A3-tax-profile.md)  
**Date:** 2026-10-24

## 1. Models

### `tax_profiles`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | FK tenants | |
| name | String(255) | |
| rate_percent | Numeric(6,3) | |
| tax_inclusive | Bool | default false |
| rounding | String(16) | `HALF_UP` |
| is_default | Bool | one default per tenant (service-enforced) |

### `work_order_parts`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | FK | |
| work_order_id | FK work_orders | |
| part_id | FK parts_catalog | |
| quantity | Numeric(14,4) | |
| unit_cost_sar | Numeric(12,2) | snapshot at attach time |

## 2. Services

- `services/tax_profiles.py` — ensure_default, get_default, apply_tax(subtotal, profile) → (tax, total, snapshot)
- `services/work_order_parts.py` — list/add/remove; tenant checks
- `billing._parts_lines` — **prefer** WorkOrderPart rows; else fall back to report `parts_used`
- `billing._compute_invoice_lines` — call `apply_tax`; merge snapshot into return + invoice metadata

## 3. API

| Method | Path | Auth |
|--------|------|------|
| GET/POST | `/tax-profiles` | company_admin write |
| PATCH | `/tax-profiles/{id}` | company_admin |
| GET/POST | `/work-orders/{id}/parts` | tech+ admin |
| DELETE | `/work-orders/{id}/parts/{line_id}` | tech+ admin |
| Existing | `/parts-catalog`, `/pricing-profiles`, `/contracts` | unchanged |

## 4. Frontend

| Route | Page |
|-------|------|
| `/billing/parts` | PartsCatalogPage |
| `/billing/tax` | TaxProfilePage |
| `/billing/pricing` | PricingProfilesPage |
| `/billing/contracts` | ContractsPage |
| WO detail | PartsUsedPanel |
| Invoice detail | tax row + snapshot label |

## 5. Migration

Alembic `e6f7a8b9c0d1` revises `d5e6f7a8b9c0`. Expand-only.
