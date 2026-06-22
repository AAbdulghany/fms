# E2E tests by domain

Playwright specs under `tests/e2e/domains/` mirror product areas.

| Folder | Spec |
|--------|------|
| `assets/` | Wave 3 asset scenarios |
| `invoices/` | Wave 4 invoice scenarios |
| `work-orders/` | Wave 4 WO workflow scenarios |
| `golden-path/` | GP-03+ multi-step journey |
| `errors/` | Bilingual API error spot-checks |

Fixtures: `tests/e2e/fixtures/auth.ts`

### Base URL by stack

| Stack | Command | `E2E_BASE_URL` |
|-------|---------|----------------|
| Local full Docker | `docker compose -f docker-compose-local.yml up -d --build` | `http://127.0.0.1:9080` |
| Demo Docker | `docker compose -f docker-compose-demo.yml up -d --build` | `http://127.0.0.1:8081` |
| Hybrid (Vite) | hybrid compose + `npm run dev` + uvicorn | `http://127.0.0.1:5173` |

Run guide: [docs/guides/testing.md](../../docs/guides/testing.md)
