# Testing

How to run automated tests for Orbit (FMS). Authoritative strategy: [TEST_STRATEGY.md](../phase3-restructure/TEST_STRATEGY.md).

---

## Four tiers (summary)

| Tier | Tool | Location | When |
|------|------|----------|------|
| **Acceptance** | Focused pytest | `backend/tests/test_*.py` | Ticket PR |
| **Regression** | Full pytest + `npm run build` | CI | Every PR |
| **E2E** | Playwright | `tests/e2e/*.spec.ts` | Wave branch / nightly |
| **Full matrix** | Traceability tables | `WAVE*_FULL_TEST_MATRIX.md` | Wave sign-off |

---

## Backend (pytest)

From repository root:

```powershell
uv run pytest backend/tests/ -q
```

From `backend/`:

```powershell
cd backend
pytest -q
```

CI (`.github/workflows/ci.yml`):

- Python 3.12, `DATABASE_URL=sqlite:///:memory:`
- `pytest -q --tb=line`

**Current count:** 219+ tests (wave + domain modules).

### Notable test modules

| Module | Covers |
|--------|--------|
| `test_rbac.py`, `test_rbac_roles.py` | Role matrix |
| `test_isolation.py`, `test_tenancy.py` | Multi-tenant isolation |
| `test_wave3_assets.py` | Assets feature gate |
| `test_wave4_invoices.py` | Invoice gate + validation |
| `test_report_pdf_rbac.py` | Report PDF access control |
| `test_api_errors.py` | Bilingual API errors (NT-131) |
| `test_work_order_requests.py` | WO request flow |

Shared fixtures: `backend/conftest.py`, `backend/tests/api_helpers.py`.

---

## Frontend

No unit test suite today. **Regression tier** uses:

```powershell
npm run build
```

(`tsc -b && vite build`)

---

## E2E (Playwright)

Config: `playwright.config.ts` → `testDir: ./tests/e2e`, default base URL `http://localhost:8080`.

### Prerequisites

Demo stack must be running:

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
```

### Run locally

```powershell
npm ci
npx playwright install chromium

$env:E2E_BASE_URL = "http://localhost:8080"
$env:E2E_DEMO_PASSWORD_SUFFIX = "123"
npx playwright test tests/e2e/
```

Single suite:

```powershell
npx playwright test tests/e2e/wave3-assets.spec.ts
```

### E2E specs

| File | Wave | Scenarios |
|------|------|-----------|
| `wave3-assets.spec.ts` | 3 | AST-01–06 |
| `wave4-golden-path.spec.ts` | 4 | GP-03–GP-12 |
| `wave4-invoices.spec.ts` | 4 | INV-01–06 |
| `wave4-workflows.spec.ts` | 4 | WO-03, WO-04 |
| `wave4-errors.spec.ts` | 4 | ERR spot-checks |

Plan docs: `docs/phase3-restructure/WAVE3_E2E.md`, `WAVE4_E2E.md`.

Fixtures: `tests/e2e/fixtures/auth.ts` — demo users compose passwords from `E2E_DEMO_PASSWORD_SUFFIX`.

### CI

`.github/workflows/wave-e2e.yml`:

- Triggers on `feature/phase-3-restructure/wave3|wave4` PRs
- Starts demo compose, waits for `http://localhost:8000/health`
- Runs Wave 3 assets spec against `http://localhost:8080`

---

## Pre-PR checklist

```powershell
# Regression
uv run pytest backend/tests/ -q
npm run build

# Optional E2E (demo stack up)
$env:E2E_BASE_URL="http://localhost:8080"
npx playwright test tests/e2e/wave3-assets.spec.ts
```

---

## Related

- [local-development.md](./local-development.md) — run API/UI for manual testing
- [demo-stack.md](./demo-stack.md) — Docker stack for E2E
- [tests/e2e/README.md](../../tests/e2e/README.md) — spec table
