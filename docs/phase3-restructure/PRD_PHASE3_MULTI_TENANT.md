# Phase 3 Product Requirements Document — Multi-Tenant Architecture Shift

**Product:** NexTask FMS  
**Version:** 3.2-restructure (draft)  
**Author:** Mariam (Product Manager)  
**Architect:** Tariq (Solution Architect)  
**Date:** 2026-06-06  
**Status:** Pending Abdullah approval

---

## 1. Problem statement

NexTask must scale as a **multi-tenant micro-SaaS** sold by the software company to maintenance companies, who in turn serve end clients owning physical assets. The current system has tenant isolation and a basic subscription gate, but lacks:

- A clear **three-tier actor model** with enforced boundaries
- **SW-controlled subscription packages** with granular feature flags
- **Pitch-ready demo environments** separate from dev/production
- **Invoice and asset modules** aligned to customer billing and dashboard expectations

## 2. Goals & success metrics

| Goal | Metric |
|------|--------|
| Zero cross-tenant data leakage | 0 isolation regressions in QA + security review |
| License enforcement | Expired tenant: 100% API block within 1 request |
| Demo readiness | Sales can reset demo to clean pitch state in < 1 min |
| Invoice compliance | 100% generated invoices include all mandatory fields |
| Asset visibility | Client users see only own assets/WOs in 100% of test cases |

## 3. User personas & limitations

### 3.1 Software Company Staff (Platform)

**Who:** Developers, product ops, super admins (`is_platform_admin`).  
**Can:**

- Define subscription packages and feature matrices
- Assign / renew / suspend tenant licenses
- Reset demo database
- Access all tenants in **non-production** for support
- Enable all features in development environment

**Cannot:**

- Routine daily ops inside a tenant's business data in **production** without audit trail (future: support impersonation AgDR)

### 3.2 Maintenance Companies (Tenants)

**Who:** `company_admin`, `manager`, `technician`, tenant-scoped `site_manager`.  
**Can:**

- Create staff accounts within plan `max_users`
- Onboard end clients and sites
- Register/import assets, run work orders, generate invoices (if package allows)
- See **only their tenant's** data

**Cannot:**

- View other maintenance companies
- Enable features not in their package
- Operate when license expired (complete freeze)

### 3.3 End Clients (Maintenance company's customers)

**Who:** `client_admin`, client-scoped `site_manager`.  
**Can:**

- View own company profile, sites, assets, work orders
- Request work orders, view maintenance schedules on own assets

**Cannot:**

- See other end clients within same tenant
- Access billing configuration, subscription, or staff management
- Import assets or manage packages (unless explicitly granted — out of scope)

## 4. Feature modules

### 4.1 Assets management (core)

**Requirements**

| ID | Requirement | Priority |
|----|-------------|----------|
| AST-01 | Add assets individually with label + schedule | Must (exists — enhance) |
| AST-02 | Bulk import via CSV/template | Must (exists — enhance validation) |
| AST-03 | Dashboard: asset list with **quarterly** and **yearly** maintenance calendar views | Must |
| AST-04 | Link assets to work orders in dashboard | Must |
| AST-05 | `ai_maintenance` feature flag + schema placeholder on schedules | Must (placeholder only) |
| AST-06 | Package gate: `assets` feature required | Must |

**Out of scope:** AI-generated maintenance plans (future phase).

### 4.2 Invoices & workflows

**Requirements**

| ID | Requirement | Priority |
|----|-------------|----------|
| INV-01 | Simplify WO workflow for **progress** and **hourly** billing tracks | Must |
| INV-02 | Generate invoice directly from approved WO / workflow history | Must (exists — align) |
| INV-03 | Mandatory invoice fields: responsible engineer, hours, hourly rate, currency | Must |
| INV-04 | Mandatory: Maintenance Company name, Client name | Must |
| INV-05 | SW Company copyright watermark on every PDF | Must |
| INV-06 | Package gate: `invoices` feature required | Must |

### 4.3 Subscriptions & licensing

**Requirements**

| ID | Requirement | Priority |
|----|-------------|----------|
| SUB-01 | SW defines packages (name, features, limits) | Must |
| SUB-02 | SW assigns package + expiry per tenant | Must |
| SUB-03 | Per-feature enable/disable enforced at API + UI | Must |
| SUB-04 | Expired license = **complete freeze** (no read, no write) | Must |
| SUB-05 | Development: all capabilities open regardless of package | Must |
| SUB-06 | Migrate Phase 3.1 `settings_json.subscription` to new model | Must |

## 5. Non-functional requirements

- **Security:** RBAC + tenant_id on every query; platform routes require `is_platform_admin`
- **Performance:** Dashboard quarterly view < 2s for 500 assets/tenant
- **Availability:** Demo reset does not affect dev/prod
- **Audit:** Package changes and license updates logged

## 6. Dependencies

- Phase 3.1 baseline ([PROGRESS_SNAPSHOT](../phase3.1/PROGRESS_SNAPSHOT_2026-06-06.md))
- AgDR: [AgDR-PHASE3-TENANT-ARCHITECTURE.md](AgDR-PHASE3-TENANT-ARCHITECTURE.md)

## 7. Out of scope

- Payment gateway / Stripe
- AI maintenance recommendations
- Mobile PWA
- Multi-language invoices (Phase 4)

## 8. Acceptance criteria (epic)

- [ ] Three-tier role boundaries demonstrated in QA matrix (platform / tenant / client)
- [ ] Two packages configured; tenant on "Starter" cannot CSV import
- [ ] Expired tenant receives freeze on login and API
- [ ] Demo DB reset produces pitch-ready seed
- [ ] Invoice PDF includes all mandatory fields + watermark
- [ ] Asset dashboard shows quarterly and yearly views
- [ ] 131+ backend tests pass; new isolation/subscription tests added

## 9. Rollout plan

1. Schema + migration (packages, tenant_subscriptions)
2. Platform admin UI (packages, tenant assignment)
3. Feature gates refactor
4. Invoice PDF + workflow alignment
5. Asset dashboard views
6. Demo environment automation

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Breaking 3.1 subscription JSON | Dual-read migration window |
| Parallel agent merge conflicts | Ticket-per-PR; domain-split (platform vs tenant vs FE) |

## 11. Open items

- Grace period before hard freeze (default 0 per customer; confirm)
- Support impersonation for SW staff in prod (defer)

## 12. Clarification for Abdullah

**One question:** Should subscription packages be **fixed tiers** (Starter / Pro / Enterprise with predefined bundles), or **fully custom** per tenant (à-la-carte feature matrix with optional overrides)? The AgDR supports both via `subscription_packages` + `overrides_json`; default proposal is **fixed tiers with rare overrides**.

---

**Approval**

| Role | Name | Date | Decision |
|------|------|------|----------|
| Product owner | Abdullah | | ☐ Approve ☐ Changes |
| Solution Architect | Tariq | | ☐ Approve ☐ Changes |
