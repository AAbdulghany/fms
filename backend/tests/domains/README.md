# Backend tests by domain

Pytest modules mirror product domains under `backend/tests/domains/`.

| Folder | Tests |
|--------|-------|
| `auth/` | Login identifier resolution |
| `security/` | RBAC, isolation, tenancy |
| `platform/` | `test_app_env`, `test_migration_chain`, `test_demo_environment`, … |
| `users/` | User CRUD |
| `clients/` | Provisioning, `test_provision_acceptance` |
| `assets/` | `test_assets_module`, lifecycle, `test_schedule_anchor` |
| `work_orders/` | Request flow, report-in-progress, `test_work_orders_acceptance` |
| `reports/` | PDF, schema sync, context merge |
| `billing/` | `test_invoices_acceptance`, computation, billing setup |
| `notifications/` | Notification CRUD |
| `core/` | Cross-cutting API errors |

Shared: `backend/tests/api_helpers.py`, fixtures in `backend/conftest.py`.

Use `assert_api_error()` for NT-131 bilingual error responses.

Naming: domain-first filenames (not `test_wave4_*`). Wave traceability is in ticket docs.
