# Sprint Backlog — NT Tickets (Parallel Execution)

**Epic:** Phase 3 Multi-Tenant Restructure  
**PRD:** [PRD_PHASE3_MULTI_TENANT.md](PRD_PHASE3_MULTI_TENANT.md)  
**AgDR:** [AgDR-PHASE3-TENANT-ARCHITECTURE.md](AgDR-PHASE3-TENANT-ARCHITECTURE.md)

> **Idris (ticket-manager):** File each row as a GitHub Issue after Abdullah approves PRD.  
> Branch format: `feature/NT-XXX-short-description`  
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

## Wave 3 — Assets module (parallel after NT-108)


| ID         | Title                                                 | Owner agent                          | Depends       | Est |
| ---------- | ----------------------------------------------------- | ------------------------------------ | ------------- | --- |
| **NT-116** | AI maintenance schema placeholder + feature flag stub | backend-engineer                     | NT-102        | S   |
| **NT-117** | Asset dashboard: quarterly maintenance calendar view  | frontend-engineer                    | —             | L   |
| **NT-118** | Asset dashboard: yearly maintenance calendar view     | frontend-engineer                    | NT-117        | M   |
| **NT-119** | Asset ↔ WO linkage panel on dashboard                 | frontend-engineer                    | NT-117        | M   |
| **NT-120** | Enforce `assets` feature gate on asset routes + UI    | backend-engineer + frontend-engineer | NT-108        | S   |
| **NT-121** | Asset module QA (AST-01–AST-06)                       | qa-engineer                          | NT-117–NT-120 | M   |


---

## Wave 4 — Invoices & workflows (parallel after NT-108)


| ID         | Title                                                       | Owner agent                          | Depends       | Est |
| ---------- | ----------------------------------------------------------- | ------------------------------------ | ------------- | --- |
| **NT-122** | WO workflow simplification: progress + hourly billing paths | backend-engineer + frontend-engineer | —             | L   |
| **NT-123** | Invoice validation: mandatory fields at generate            | backend-engineer                     | NT-122        | M   |
| **NT-124** | PDF: engineer, hours, rate, currency, both company names    | backend-engineer                     | NT-123        | M   |
| **NT-125** | PDF: SW company copyright watermark (platform_settings)     | backend-engineer                     | NT-124        | S   |
| **NT-126** | Enforce `invoices` feature gate                             | backend-engineer + frontend-engineer | NT-108        | S   |
| **NT-127** | Invoice module QA (INV-01–INV-06)                           | qa-engineer                          | NT-122–NT-126 | M   |


---

## Wave 5 — Role hardening & sign-off


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

- One PR per ticket (or tightly coupled pair with same NT id)
- Required sections: Summary, Test plan, AgDR link if schema change
- 2-review gate: code-reviewer (Rex) + human (Abdullah)

