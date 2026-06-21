# E2E tests (Playwright)

Wave-scoped end-to-end tests for Phase 3 restructure.

| Wave | Spec file | Plan doc |
|------|-----------|----------|
| 3 | `wave3-assets.spec.ts` | [WAVE3_E2E.md](../docs/phase3-restructure/WAVE3_E2E.md) |
| 4 | `wave4-invoices.spec.ts` | TBD |

**Status:** Wave 3 specs pending NT-121.

```powershell
# Local run (demo stack must be up)
$env:E2E_BASE_URL="http://localhost:8080"
npx playwright test tests/e2e/wave3-assets.spec.ts
```
