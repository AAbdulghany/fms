# Wave 4 E2E Test Plan — Invoices + Golden Path

**Branch:** `feature/phase-3-restructure/wave4`  
**Owner:** qa-engineer (NT-127, NT-132)  
**Strategy:** [TEST_STRATEGY.md](TEST_STRATEGY.md) · **Full matrix:** [WAVE4_FULL_TEST_MATRIX.md](WAVE4_FULL_TEST_MATRIX.md)  
**Tool:** Playwright (see [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md))

---

## Test suites (proposed — confirm with product)

| Suite | File | Scenarios | Tier | Purpose |
|-------|------|-----------|------|---------|
| **A — Golden path** | `wave4-golden-path.spec.ts` | GP-01–GP-12 | E2E | Happy path: company → site → asset → WO → report → invoice |
| **B — Invoice module** | `wave4-invoices.spec.ts` | INV-01–INV-06 | E2E | Invoice-specific edges (feature gate, edit, send) |
| **C — WO transitions** | `wave4-workflows.spec.ts` | WO-03, WO-04 | E2E | Modals: hold reason, assignee, cancel |
| **D — Error UX** | `wave4-errors.spec.ts` | ERR spot-checks | E2E | UI shows friendly text, not raw codes |

**Regression** (not Playwright): full pytest + build — see CI.  
**Acceptance** (not Playwright): per-ticket pytest in matrix.  
**Full matrix:** all rows in `WAVE4_FULL_TEST_MATRIX.md`.

---

## Suite A — Golden path (GP-03 – GP-12)

**Navigation model (locked):** E2E starts at **GP-03**. GP-02 (create company UI) is **skipped** — company is pre-created via API fixture (`POST /clients`, 0 sites) before the first UI step.

| ID | Role | Route / UI | Step | Pass criteria |
|----|------|------------|------|---------------|
| **GP-01** | company_admin | `/login` → `/dashboard` | Login | Dashboard loads |
| **GP-02** | — | — | **Skipped (N/A)** | Company from API setup, not UI |
| **GP-03** | company_admin | `/companies/:id` → Sites tab → **+ Add site** (`add-only`) | Add first site | Site row visible on company detail |
| **GP-04** | company_admin | `/assets` → Register asset modal | Pick company + site; monthly schedule | Asset appears on calendar |
| **GP-05** | company_admin | `/work-orders` → **+ Create work order** | Select company, site, asset | WO in list, status `created` |
| **GP-06** | company_admin | `/work-orders/:id` | Assign technician → status `assigned` | Assignee set |
| **GP-07** | technician | `/work-orders/:id` | Start → `in_progress` | Report section unlocked |
| **GP-08** | technician | `/work-orders/:id` → report modal | Submit report + labor hours | Report `submitted` |
| **GP-09** | company_admin | `/work-orders/:id` | Complete → verify (approve report) | WO `verified` |
| **GP-10** | company_admin | `/invoices` or WO → preview modal | Invoice preview | Hours, rate, currency shown |
| **GP-11** | company_admin | Generate invoice | Confirm generate | Invoice on `/invoices` |
| **GP-12** | company_admin | Invoice detail / list | Download PDF | PDF 200; no raw error codes in UI |

**Estimated runtime:** ~3–5 min (serial; GP-02 not in browser).

### Golden path flow (GP-03+)

```
[API setup]         POST /clients → company with 0 sites
    ↓
/companies/:id      GP-03  Sites tab → + Add site (add-only)
    ↓
/assets             GP-04  Register asset
    ↓
/work-orders        GP-05  Create WO
    ↓
/work-orders/:id    GP-06  Assign technician
    ↓
…                   GP-07–GP-12  report → invoice
```

### GP-02 status

GP-02 UI (company-only create modal) was reverted. Production **Add company** uses full provision (`POST /clients/provision`). E2E does not test that path; GP-03 is the first UI assertion.


---

## Suite B — Invoice module (INV-01 – INV-06)

| ID | Role | Scenario | Pass criteria |
|----|------|----------|---------------|
| **INV-01** | company_admin | Generate invoice from verified WO | Invoice created; appears on list |
| **INV-02** | company_admin | Invoice detail edit draft fields | billing_email, dates, currency persist |
| **INV-03** | company_admin | Download invoice PDF | PDF returns 200; tenant + platform names |
| **INV-04** | company_admin | Tenant **without** `invoices` feature | Nav hidden OR friendly message on direct URL |
| **INV-05** | company_admin | Invoice preview before generate | Preview shows labor hours + currency |
| **INV-06** | company_admin | Approve / send invoice workflow | Status draft → approved → sent |

---

## Data strategy — **locked (2026-06-22)**

**Decision:** **Hybrid** — GP-03+ via separate page flows; **GP-02 skipped** (company from API fixture). Unique codes per run (`E2E-{timestamp}`).

| Option | Status |
|--------|--------|
| UI-only fresh journey | Rejected — too slow for CI |
| API setup + UI assert | Partial — only if GP-02–06 flake |
| Pitch seed only | Rejected — conflicts with clean-seed policy |
| **Hybrid** | **Selected** |

## Error UX — **locked (2026-06-22)**

**Decision:** **Both** — API returns `{ code, message_en, message_ar }`; FE `resolveApiError()` prefers API messages, falls back to i18n.

## Suites in scope — **locked (2026-06-22)**

All four suites ship in Wave 4: **A** golden path · **B** invoices · **C** WO modals · **D** error UX.

---

## Data strategy (reference)

| Option | Pros | Cons |
|--------|------|------|
| **1 — UI-only fresh journey** | Truest E2E; GP-02–GP-12 from empty tenant | Slow; needs clean DB or unique codes per run |
| **2 — API setup + UI assert** | Fast GP-09–GP-12; Playwright APIRequest for GP-02–08 | Less “pure” E2E |
| **3 — Pitch seed + extend** | Fastest; reuses demo users | Conflicts with A5 clean-seed policy |
| **4 — Hybrid (recommended)** | GP-01 login + GP-02–06 via UI; parallel worker isolation with timestamp suffix on company code | Moderate complexity |

Default recommendation: **Option 4** until you choose otherwise.

---

## Setup

```powershell
npm install -D @playwright/test
npx playwright install chromium

docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d
$env:E2E_BASE_URL="http://localhost:8080"
npx playwright test tests/e2e/wave4-golden-path.spec.ts
```

---

## Implementation status

| ID | Automated | File | Status |
|----|-----------|------|--------|
| GP-03–GP-12 | ⬜ | `wave4-golden-path.spec.ts` | NT-132 (GP-02 skipped) |
| INV-01–INV-06 | ⬜ | `wave4-invoices.spec.ts` | NT-127 |
| WO-03, WO-04 | ⬜ | `wave4-workflows.spec.ts` | NT-127 stretch |
| ERR spot-checks | ⬜ | `wave4-errors.spec.ts` | NT-131 |

NT-127 / NT-132 close when suites A+B are ✅ or explicitly deferred in sign-off.
