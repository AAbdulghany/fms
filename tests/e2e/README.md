# E2E tests (Playwright)

**Scenarios (multi-user):** [docs/testing/FULL_SCENARIO_CATALOG.md](../../docs/testing/FULL_SCENARIO_CATALOG.md)  
**Main gate (REG):** [docs/testing/REGRESSION_SUITE.md](../../docs/testing/REGRESSION_SUITE.md)  
**Run guide:** [docs/guides/testing.md](../../docs/guides/testing.md)

| Suite | Path | CI |
|-------|------|-----|
| **Regression smoke** | `tests/e2e/regression/*.spec.ts` | Push to `main` (default) |
| **Domain / full** | `tests/e2e/domains/**` | Manual `suite=full` or local |

```powershell
docker compose -f docker-compose-pilot.yml up -d --build
$env:E2E_BASE_URL="http://localhost:9081"
$env:E2E_DEMO_PASSWORD_SUFFIX="123"

npx playwright test tests/e2e/regression   # REG
npx playwright test tests/e2e/domains      # fuller journeys (e.g. A2 company→QR)
```

Fixtures: `fixtures/auth.ts` — seed users use `{local-part}` + `E2E_DEMO_PASSWORD_SUFFIX`.
