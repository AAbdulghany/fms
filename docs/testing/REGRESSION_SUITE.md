# Regression suite — every push / merge to `main`

Maps to catalog IDs in [FULL_SCENARIO_CATALOG.md](./FULL_SCENARIO_CATALOG.md).

## Gate (what CI runs)

| Bucket | Command / path | When |
|--------|----------------|------|
| **API** | `pytest -q` in `backend/` | PR + push to `main` / `dev` / `feature/**` ([ci.yml](../../.github/workflows/ci.yml)) |
| **FE** | `npm run check:imports` + `npm run build` | Same |
| **E2E smoke** | `npx playwright test tests/e2e/regression` on pilot stack | Push to `main` + manual dispatch ([playwright-e2e-pilot.yml](../../.github/workflows/playwright-e2e-pilot.yml)) |

Full Playwright tree (`tests/e2e/domains/**`) is **not** the main gate. Run via workflow_dispatch `suite=full` or locally.

## E2E REG smoke (multi-user)

| Spec | Catalog IDs | Actors |
|------|-------------|--------|
| `tests/e2e/regression/personas.spec.ts` | SC-AUTH-01/02/03, SC-TEN-01/02 | P-ADMIN, P-TECH |
| `tests/e2e/regression/assets-calendar.spec.ts` | SC-AST-01/02 | P-ADMIN |
| `tests/e2e/regression/invoices-smoke.spec.ts` | SC-INV-01 | P-ADMIN |
| `tests/e2e/regression/client-scope.spec.ts` | SC-CLIENT-VIEW (partial) | P-CLIENT |

## Explicitly out of REG

- Full SC-GP-HOSP (invoice generate end-to-end)
- Platform CRUD (SC-PLATFORM)
- Every ERR catalog code
- Import matrices, Lighthouse, multi-browser
- Skipped placeholder specs (removed)

## Local commands

```powershell
# API + FE (same as CI)
uv run pytest backend/tests/ -q
npm run check:imports
npm run build

# E2E REG (pilot up)
$env:E2E_BASE_URL="http://localhost:9081"
$env:E2E_DEMO_PASSWORD_SUFFIX="123"
npx playwright test tests/e2e/regression

# Full E2E (optional)
npx playwright test tests/e2e/domains
```
