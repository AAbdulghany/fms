# AgDR: Phase 3 Multi-Tenant Architecture & Environments

**Status:** Approved for Build (Wave 0 — 2026-06-06)  
**Author:** Hisham (Tech Lead) / Tariq (Architecture)  
**Date:** 2026-06-06  
**PRD:** [PRD_PHASE3_MULTI_TENANT.md](PRD_PHASE3_MULTI_TENANT.md)  
**ERD:** [ERD_WAVE0.md](ERD_WAVE0.md)

---

## Context

NexTask FMS serves three distinct actor classes. Phase 3.1 delivered a minimal subscription gate and tenant-scoped RBAC. The customer requests a formal platform hierarchy, package-based feature flags, environment segregation (demo/dev/prod), and invoice/asset modules aligned to subscription tiers.

## Decision

### 1. Tenancy model — shared database, row-level isolation (retain)

Continue **single PostgreSQL database per environment** with `tenant_id` on all tenant-owned rows. Add explicit **platform tables** for packages and global config.

| Layer | Scope key | Visibility |
|-------|-----------|------------|
| Platform | `is_platform_admin` / SW staff | Cross-tenant read/write for ops only |
| Maintenance company (tenant) | `tenant_id` | All tenant staff data |
| End client | `tenant_id` + `client_id` (+ site scope) | Client profile, assets, WOs only |

**Rejected:** DB-per-tenant (operational cost too high for micro-SaaS stage).  
**Rejected:** Schema-per-tenant (migration complexity without current scale need).

### 2. Role hierarchy mapping

| Customer tier | FMS roles | Capabilities |
|---------------|-----------|--------------|
| SW Company Staff | `super_admin` + `is_platform_admin=true` | Package CRUD, tenant license, demo reset, feature matrix, all env bypass in non-prod |
| Maintenance Company | `company_admin`, `manager`, `technician`, `site_manager` (tenant staff) | Tenant-scoped ops; package limits enforced |
| End Client | `client_admin`, `site_manager` (client-bound) | Own `client_id` only |

Rename in UX (not DB enum yet): "Super Admin" → "Platform Admin" where customer-facing.

### 3. Subscription & feature flags

New tables (platform-owned):

```
subscription_packages (id, code, name, features_json, limits_json, is_active)
tenant_subscriptions (tenant_id, package_id, status, valid_until, overrides_json)
```

- **SW Company exclusively** assigns `package_id` and `valid_until` per tenant.
- `features_json` keys: `assets`, `csv_import`, `invoices`, `advanced_scheduling`, `ai_maintenance` (placeholder), etc.
- **License expired / suspended:** middleware blocks **all** authenticated API + returns login-block payload; read-only mode rejected per customer ("complete freeze").
- **Development:** `APP_ENV=development` bypasses feature gates and license freeze (platform staff only can still mutate packages).

### 4. AI maintenance placeholder

Add nullable `ai_maintenance_plan_json` on `MaintenanceSchedule` and feature flag `ai_maintenance` (disabled for all packages until Phase N). No ML pipeline in this phase.

### 5. Invoice data contract

Mandatory PDF + API fields (validation at generate):

- Responsible engineer (assignee display name)
- Hours logged, hourly rate, currency
- Maintenance company legal name (tenant)
- Client legal name
- SW company copyright watermark (from `platform_settings.branding`)

### 6. Environment strategy

| Environment | Database | Purpose | Data lifecycle |
|-------------|----------|---------|----------------|
| **Demo** | `fms_demo` (separate URL) | Sales pitches | Reset nightly or on-demand via platform script |
| **Dev** | `fms_dev` | Engineering | Persistent; synthetic data OK |
| **Prod** | `fms_prod` | Paying tenants | Migrations only; no seed overwrite |

Implementation:

- `DATABASE_URL` per env (12-factor).
- `APP_ENV=demo|development|production`.
- Demo: pre-seeded tenants (1 maintenance co + 2 end clients + sample assets/WOs/invoices).
- Platform endpoint `POST /platform/demo/reset` (platform admin only, demo env only).

### 7. Migration from Phase 3.1

- Migrate `Tenant.settings_json.subscription` → `tenant_subscriptions` row linked to default package.
- Keep `settings_json` for tenant branding only.
- Backward-compatible read for one release cycle.

## NFRs

- Tenant isolation: 100% of tenant queries include `tenant_id` filter (existing pattern).
- Package check: p95 < 5ms (cached package resolution per request).
- Demo reset: < 60s full re-seed.

## Risks

| Risk | Mitigation |
|------|------------|
| Freeze locks out admins mid-demo | Demo env bypasses freeze; prod uses grace banner 7d before hard freeze (configurable) |
| Feature flag drift | Single `subscription_packages` source of truth; no per-tenant ad-hoc flags except `overrides_json` audit-logged |

## Open question (Abdullah)

See PRD §12 — package model: fixed tiers vs à-la-carte feature matrix.

## Wave 0 ERD

The concrete schema for the platform/subscription tables introduced in §3 (subscription
& feature flags) and §5 (invoice branding) is specified in
[ERD_WAVE0.md](ERD_WAVE0.md). It defines `subscription_packages`,
`tenant_subscriptions` (UNIQUE `tenant_id`), and `platform_settings`, plus their
relationship to the existing `tenants` table. NT-102 builds the migration against that
ERD; NT-103 migrates `settings_json.subscription` into `tenant_subscriptions`.

## Sign-off

| Gate | Role | Name | Date | Decision |
|------|------|------|------|----------|
| Wave 0 architecture (NT-101) | Solution Architect | Tariq | 2026-06-06 | ✅ Approved for Build |
