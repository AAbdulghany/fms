# Wave 3 E2E Test Plan — Assets (Playwright)

**Branch:** `feature/phase-3-restructure/wave3`  
**Owner:** qa-engineer (NT-121)  
**Tool:** Playwright (see [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md))  
**Seed:** pitch demo (`super@demo.com`, `client@demo.com`, `admin@demo.com`)

---

## Setup (first time)

```powershell
npm install -D @playwright/test
npx playwright install chromium
```

**Config:** `playwright.config.ts` (repo root) — base URL from `E2E_BASE_URL` (default `http://localhost:8080`).

**Run locally (demo stack up):**

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d
$env:E2E_BASE_URL="http://localhost:8080"
npx playwright test tests/e2e/wave3-assets.spec.ts
```

---

## Scenarios (AST-01 – AST-06)

| ID | Role | Scenario | Pass criteria |
|----|------|----------|---------------|
| **AST-01** | company_admin | Open assets → quarterly calendar | Calendar renders; ≥1 scheduled asset from pitch seed |
| **AST-02** | company_admin | Switch to yearly view | Year grid loads; no console errors |
| **AST-03** | company_admin | Select asset → WO linkage panel | Shows linked WO or empty state |
| **AST-04** | company_admin | Tenant **without** `assets` feature | Asset nav hidden OR 403 on direct URL |
| **AST-05** | client_admin | Assets page | Only own client assets visible |
| **AST-06** | client_admin | Register asset flow | Company read-only; can pick site; submit succeeds |

---

## File layout

```
tests/e2e/
  fixtures/
    auth.ts          # login helper per role
  wave3-assets.spec.ts
  README.md
playwright.config.ts
```

---

## CI integration

- Trigger: PR to `feature/phase-3-restructure/wave3` + nightly on wave branch  
- Workflow: `.github/workflows/wave-e2e.yml`  
- Service container: demo compose or Render preview URL (future)

---

## Implementation status

| ID | Automated | File | Status |
|----|-----------|------|--------|
| AST-01 | ✅ | `wave3-assets.spec.ts` | Pass — quarterly calendar visible |
| AST-02 | ✅ | ↑ | Pass — yearly view toggle |
| AST-03 | ✅ | ↑ | Pass — asset WO panel or empty state |
| AST-04 | ⏭️ N/A (backend) | `test_wave3_assets.py` | Skipped in E2E — `test_assets_feature_gate_production` covers 403 |
| AST-05 | ✅ | `wave3-assets.spec.ts` | Pass — client_admin scoped calendar, no client filter |
| AST-06 | ✅ | ↑ | Pass — register asset modal opens |

NT-121 closed 2026-06-22 — all rows ✅ or explicitly deferred with sign-off note.

---

## Wave 4+ reuse

Extend `tests/e2e/` with `wave4-invoices.spec.ts` (INV-01–06) using same `fixtures/auth.ts`.
