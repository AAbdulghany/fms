# Backend domains

Feature-oriented API packages (routers). Canonical implementations live here; `api/routes/*.py` re-exports for compatibility.

| Domain | Modules |
|--------|---------|
| `auth/` | `router.py` |
| `users/` | `router.py` |
| `clients/` | `router.py`, `sites.py`, `locations.py` |
| `assets/` | `router.py` |
| `work_orders/` | `router.py` |
| `reports/` | `router.py`, `templates.py` |
| `billing/` | `invoices.py`, `billing_actions.py`, `catalog.py`, `labor.py` |
| `notifications/` | `router.py` |
| `dashboard/` | `router.py` |
| `platform/` | `router.py`, `tenants.py` |

Business logic remains in `app/services/` (colocate under domains in a future pass).
