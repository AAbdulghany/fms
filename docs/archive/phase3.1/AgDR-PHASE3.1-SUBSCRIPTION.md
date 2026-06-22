# AgDR: Phase 3.1 Subscription (Manual)

**Status:** Approved for Build  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Context

Billing is managed offline. FMS must enforce tenant access based on manually configured subscription state.

## Decision

Store subscription in `Tenant.settings_json`:

```json
{
  "subscription": {
    "plan": "trial | starter | pro | enterprise",
    "status": "active | trial | suspended | expired",
    "valid_until": "2026-12-31",
    "max_sites": 10,
    "max_users": 25,
    "features": ["assets", "invoices", "csv_import"]
  }
}
```

## Enforcement

- Dependency `ensure_active_subscription` on authenticated routes (except auth + super_admin tenant mgmt).
- Block with `403 SUBSCRIPTION_SUSPENDED` and human-readable message.
- Feature flags: e.g. CSV import requires `pro` or `enterprise` + `csv_import` feature.

## Super-admin UI

- `GET/PATCH /tenants/{id}/subscription` (super_admin only)
- Simple panel: plan, status, valid_until, limits, feature toggles

## Operator workflow

1. Client pays offline → set `valid_until` + `status=active`
2. Trial expires → `suspended` → API blocked
3. Upgrade → flip `plan` + features manually

## Out of scope

- Stripe / payment gateway (Phase 4)
- Self-serve signup
