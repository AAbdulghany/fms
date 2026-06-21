# Sprint Backlog — NT Tickets (Parallel Execution)

**Epic:** Phase 3 Multi-Tenant Restructure  
**PRD:** [PRD_PHASE3_MULTI_TENANT.md](PRD_PHASE3_MULTI_TENANT.md)  
**AgDR:** [AgDR-PHASE3-TENANT-ARCHITECTURE.md](AgDR-PHASE3-TENANT-ARCHITECTURE.md)

> **Branch format (Wave 3+):** `feature/phase-3-restructure/wave{N}/NT-XXX-short-description`  
> **Wave integration branch:** `feature/phase-3-restructure/wave{N}`  
> **Governance:** [WAVE_GOVERNANCE.md](WAVE_GOVERNANCE.md) · **CI:** [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md)  
> PR title: `feat(NT-XXX): description`

---

## Wave 0 — Architecture & migration (sequential gate) ✅ CLOSED

See [WAVE0_SIGNOFF.md](WAVE0_SIGNOFF.md).


| ID         | Title                 | Owner agent        | Status | GitHub |
| ---------- | --------------------- | ------------------ | ------ | ------ |
| **NT-101** | AgDR sign-off + ERD   | solution-architect | ✅ Done | #3     |
| **NT-102** | DB migration tables   | backend-engineer   | ✅ Done | #4     |
| **NT-103** | Migrate settings_json | backend-engineer   | ✅ Done | #6     |
| **NT-104** | APP_ENV matrix        | platform-engineer  | ✅ Done | #5     |


---

## Wave 1 — Platform & licensing (parallel after NT-102) ✅ CLOSED

See [WAVE1_WAVE2_SIGNOFF.md](WAVE1_WAVE2_SIGNOFF.md).


| ID         | Title                                                              | Owner agent       | Status | GitHub |
| ---------- | ------------------------------------------------------------------ | ----------------- | ------ | ------ |
| **NT-105** | Platform API: CRUD subscription_packages (SW only)                 | backend-engineer  | ✅ Done | #7     |
| **NT-106** | Platform API: assign package + valid_until to tenant               | backend-engineer  | ✅ Done | #8     |
| **NT-107** | License freeze middleware (full block) + dev bypass                | backend-engineer  | ✅ Done | #10    |
| **NT-108** | Feature gate dependency (per-route + per-feature)                  | backend-engineer  | ✅ Done | #12    |
| **NT-109** | Platform admin UI: package manager                                 | frontend-engineer | ✅ Done | #14    |
| **NT-110** | Platform admin UI: tenant license panel (replace SubscriptionPage) | frontend-engineer | ✅ Done | #16    |
| **NT-111** | Subscription + freeze tests                                        | qa-engineer       | ✅ Done | #9     |


---

## Wave 2 — Demo environment (parallel with Wave 1) ✅ CLOSED


| ID         | Title                                                          | Owner agent       | Status | GitHub |
| ---------- | -------------------------------------------------------------- | ----------------- | ------ | ------ |
| **NT-112** | Demo database compose profile (fms_demo URL)                   | platform-engineer | ✅ Done | #11    |
| **NT-113** | Pitch seed script (1 tenant, 2 clients, assets, WOs, invoices) | backend-engineer  | ✅ Done | #13    |
| **NT-114** | POST /platform/demo/reset (demo env only)                      | backend-engineer  | ✅ Done | #15    |
| **NT-115** | DEMO_DEPLOY.md update + Railway demo instance guide            | platform-engineer | ✅ Done | #17    |


---

## Wave 3 — Assets module ✅ CLOSED

**Branch:** `feature/phase-3-restructure/wave3`  
**Tracker:** [WAVE3_TICKETS.md](WAVE3_TICKETS.md) · **Sign-off:** [WAVE3_SIGNOFF.md](WAVE3_SIGNOFF.md) · **E2E:** [WAVE3_E2E.md](WAVE3_E2E.md) · **UAT:** [WAVE3_OBSERVATIONS.md](WAVE3_OBSERVATIONS.md)


| ID         | Title                                                 | Owner agent                          | Status | GitHub |
| ---------- | ----------------------------------------------------- | ------------------------------------ | ------ | ------ |
| **NT-116** | AI maintenance schema placeholder + feature flag stub | backend-engineer                     | ✅ Done | —      |
| **NT-117** | Asset dashboard: quarterly maintenance calendar view  | frontend-engineer                    | ✅ Done | —      |
| **NT-118** | Asset dashboard: yearly maintenance calendar view     | frontend-engineer                    | ✅ Done | —      |
| **NT-119** | Asset ↔ WO linkage panel on dashboard                 | frontend-engineer                    | ✅ Done | —      |
| **NT-120** | Enforce `assets` feature gate on asset routes + UI    | backend-engineer + frontend-engineer | ✅ Done | —      |
| **NT-121** | Asset module QA (AST-01–AST-06)                       | qa-engineer                          | ✅ Done | —      |

**UAT observations (18):** All P1/P2 items from maintenance-admin UAT absorbed into Wave 3 — see [WAVE3_OBSERVATIONS.md](WAVE3_OBSERVATIONS.md).


---

## Wave 4 — Invoices & workflows 🟡 IN REVIEW

**Branch:** `feature/phase-3-restructure/wave4` · [WAVE4_TICKETS.md](WAVE4_TICKETS.md) · **E2E:** [WAVE4_E2E.md](WAVE4_E2E.md)


| ID         | Title                                                       | Owner agent                          | Status | Notes |
| ---------- | ----------------------------------------------------------- | ------------------------------------ | ------ | ----- |
| **NT-122** | WO workflow simplification: progress + hourly billing paths | backend-engineer + frontend-engineer | ✅ Done | FSM + report-before-complete |
| **NT-123** | Invoice validation: mandatory fields at generate            | backend-engineer                     | ✅ Done | billing_setup + computation tests |
| **NT-124** | PDF: engineer, hours, rate, currency, both company names    | backend-engineer                     | ✅ Done | branded invoice + maintenance report |
| **NT-125** | PDF: SW company copyright watermark (platform_settings)     | backend-engineer                     | ✅ Done | `pdf_brand` / platform copyright |
| **NT-126** | Enforce `invoices` feature gate                             | backend-engineer + frontend-engineer | ✅ Done | API + `FeatureRoute` + sidebar |
| **NT-127** | Invoice module QA (INV-01–INV-06)                           | qa-engineer                          | 🟡 Partial | 25 backend tests; Playwright deferred |


---

## Wave 5 — Role hardening & sign-off (blocked on Wave 4)

**Branch:** `feature/phase-3-restructure/wave5` · [WAVE5_TICKETS.md](WAVE5_TICKETS.md)  
**Note:** RBAC core (super_user, sw_dev, company_engineer) landed early on `feature/phase3` — NT-128 scope reduced; reconcile in Wave 5.


| ID         | Title                                                     | Owner agent             | Depends                | Est |
| ---------- | --------------------------------------------------------- | ----------------------- | ---------------------- | --- |
| **NT-128** | RBAC matrix update: 3-tier boundaries documented + tested | tech-lead + qa-engineer | NT-107                 | M   |
| **NT-129** | Security review: isolation + platform routes              | security-reviewer       | NT-108, NT-128         | M   |
| **NT-130** | Phase 3 restructure sign-off doc                          | qa-engineer             | NT-111, NT-121, NT-127 | S   |


---

## Parallel execution map

```
NT-101 → NT-102 → NT-103 ─┬→ NT-105..NT-111 (licensing)
                          ├→ NT-112..NT-115 (demo)
                          └→ NT-116..NT-121 (assets) ∥ NT-122..NT-127 (invoices)
                                      └→ NT-128..NT-130 (hardening)
```

**Suggested parallel lanes after NT-102:**


| Lane          | Agent                  | Tickets                        |
| ------------- | ---------------------- | ------------------------------ |
| A Platform BE | backend-engineer       | NT-105, NT-106, NT-107, NT-108 |
| B Platform FE | frontend-engineer      | NT-109, NT-110                 |
| C Demo/Infra  | platform-engineer      | NT-112, NT-115                 |
| D Assets      | frontend-engineer + BE | NT-117–NT-120                  |
| E Invoices    | backend-engineer + FE  | NT-122–NT-126                  |


---

## PR workflow (Tariq / pr-manager)

- **Ticket PR** → target `feature/phase-3-restructure/wave{N}` (one PR per ticket or tight pair)
- **Wave merge PR** → target `dev` after [WAVE{N}_SIGNOFF.md](WAVE3_SIGNOFF.md) complete
- Required sections: Summary, Test plan, AgDR link if schema change
- 2-review gate: code-reviewer (Rex) + human (Abdullah)
- CI must pass: `.github/workflows/ci.yml` (+ `wave-e2e.yml` when E2E exists)

