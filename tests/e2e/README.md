# E2E tests (Playwright)

Wave-scoped end-to-end tests for Phase 3 restructure.

**Run guide:** [docs/guides/testing.md](../docs/guides/testing.md)  
**Strategy:** [TEST_STRATEGY.md](../docs/phase3-restructure/TEST_STRATEGY.md) (four tiers: acceptance · regression · E2E · full matrix)


| Wave | Spec file                   | Plan doc                                                | Scenarios                   |
| ---- | --------------------------- | ------------------------------------------------------- | --------------------------- |
| 3    | `domains/assets/wave3-assets.spec.ts` | [WAVE3_E2E.md](../docs/phase3-restructure/WAVE3_E2E.md) | AST-01–06 |
| 4    | `domains/golden-path/wave4-golden-path.spec.ts` | [WAVE4_E2E.md](../docs/phase3-restructure/WAVE4_E2E.md) | GP-03–GP-12 (GP-02 skipped) |
| 4    | `domains/invoices/wave4-invoices.spec.ts` | ↑ | INV-01–06 (NT-127) |
| 4    | `domains/work-orders/wave4-workflows.spec.ts` | ↑ | WO-03, WO-04 (stretch) |
| 4    | `domains/errors/wave4-errors.spec.ts` | ↑ | ERR spot-checks (NT-131) |


```powershell
# Local run (demo stack must be up)
$env:E2E_BASE_URL="http://localhost:9081"
# Demo passwords: {role} prefix + suffix (matches pitch seed; default suffix below)
$env:E2E_DEMO_PASSWORD_SUFFIX="123"
npx playwright test tests/e2e/
```

**Regression** (not here): `pytest -q` + `npm run build` in CI.