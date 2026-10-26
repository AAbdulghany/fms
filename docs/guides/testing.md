# Testing

How to run automated tests for Orbit (FMS).

**Scenario catalog (multi-user):** [../testing/FULL_SCENARIO_CATALOG.md](../testing/FULL_SCENARIO_CATALOG.md)  
**Main regression gate:** [../testing/REGRESSION_SUITE.md](../testing/REGRESSION_SUITE.md)  
**Strategy:** [TEST_STRATEGY.md](../phase3-restructure/TEST_STRATEGY.md)

---

## Four tiers (summary)

| Tier | Tool | Location | When |
|------|------|----------|------|
| **Acceptance** | Focused pytest | `backend/tests/` | Ticket PR |
| **Regression** | Full pytest + `npm run build` + E2E smoke | CI on PR + push to `main` | Every PR / merge to main |
| **E2E (full)** | Playwright domains | `tests/e2e/domains/` | Manual `suite=full` / local |
| **Full scenarios** | Catalog | `docs/testing/FULL_SCENARIO_CATALOG.md` | UAT / sign-off |

---

## Backend (pytest)

```powershell
uv run pytest backend/tests/ -q
```

CI ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)):

- Runs on **PR** and **push** to `main`, `dev`, `feature/**`
- Python 3.12, `DATABASE_URL=sqlite:///:memory:`
- `pytest -q --tb=line`

---

## Frontend

```powershell
npm run check:imports
npm run build
```

---

## E2E (Playwright)

Config: `playwright.config.ts` → `testDir: ./tests/e2e`.

| Suite | Path | CI default |
|-------|------|------------|
| **Regression smoke** | `tests/e2e/regression/` | Push to `main` |
| **Domain / full** | `tests/e2e/domains/` | `workflow_dispatch` → `suite=full` |

### Which URL

| Stack | `E2E_BASE_URL` |
|-------|----------------|
| Pilot Docker (recommended) | `http://localhost:9081` |
| Local Docker | `http://localhost:9080` |
| Hybrid Vite | `http://localhost:5173` |

### Run REG locally

```powershell
docker compose -f docker-compose-pilot.yml up -d --build
npm ci
npx playwright install chromium
$env:E2E_BASE_URL = "http://localhost:9081"
$env:E2E_DEMO_PASSWORD_SUFFIX = "123"
npx playwright test tests/e2e/regression
```

Fixtures: `tests/e2e/fixtures/auth.ts` — `DEMO_USERS` (admin, tech, client, site, super).

---

## Pre-merge checklist

```powershell
uv run pytest backend/tests/ -q
npm run check:imports
npm run build
# Optional REG E2E with pilot up
npx playwright test tests/e2e/regression
```

---

## Related

- [local-development.md](./local-development.md)
- [pilot-stack.md](./pilot-stack.md)
- [docker-seed-profiles.md](./docker-seed-profiles.md)
- [tests/e2e/README.md](../../tests/e2e/README.md)
