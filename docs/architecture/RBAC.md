# RBAC — Role-Based Access Control (canonical)

**Product:** Orbit (FMS) · **Applies to:** API (`/api/v1`) + React SPA  
**Tests:** `backend/tests/domains/security/` · **Code:** `backend/app/rbac.py`, `backend/app/api/deps.py`

---

## Role tiers (current model)

### Platform staff (`is_platform_admin=true`)

| Role | Code | Capabilities |
|------|------|--------------|
| Super user | `super_user` | Full platform: tenants, packages, licenses, demo reset, provision maintenance companies |
| SW dev | `sw_dev` | Same as super_user **except** cannot remove/deactivate members |

**UI:** `/platform/maintenance-companies`, `/platform/packages`, `/subscription`

### Maintenance company (tenant)

| Role | Code | Scope |
|------|------|--------|
| Company admin | `company_admin` | Full tenant ops; manage staff (engineers, technicians, client/site admins) |
| Company engineer | `company_engineer` | Same operational access as company_admin; **cannot** add peer engineers or company admins |

### End client (tenant customer's org)

| Role | Code | Scope |
|------|------|--------|
| Client admin | `client_admin` | Own client's sites, assets, locations, scoped WOs/invoices |
| Site manager | `site_manager` | Assigned site(s) via `UserSiteScope` |
| Technician | `technician` | Assigned work orders; report edit/submit |
| Manager | `manager` | Report approval; read-heavy tenant access |

### Legacy

| Role | Notes |
|------|--------|
| `super_admin` | Pre-restructure tenant god-role. Platform staff should use `super_user`. `scripts/migrate_roles.py` maps legacy platform admins. |

---

## Access patterns

| Pattern | Roles | Mechanism |
|---------|-------|-----------|
| Tenant-wide | super_admin, company_admin, company_engineer, manager | Filter by `tenant_id` only |
| Client-scoped | client_admin | Filter by `user.client_id` |
| Site-scoped | site_manager | `UserSiteScope` join |
| Assignee-scoped | technician | `assignee_user_id == user.id` |
| Platform-only | super_user, sw_dev | `is_platform_admin` + route guards |

---

## Feature gates (subscription)

Modules gated by package features (bypassed when `APP_ENV=development|demo`):

| Feature key | Routes / UI |
|-------------|-------------|
| `assets` | `/assets`, asset APIs |
| `invoices` | `/invoices`, invoice APIs |
| `ai_maintenance` | AI scheduling stub (returns 501 when enabled) |

See [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md).

---

## Endpoint summary (high level)

Detailed Phase 2 matrix (historical): [../archive/phase2/RBAC_Matrix.md](../archive/phase2/RBAC_Matrix.md)

| Area | Create | List/read | Approve / sensitive |
|------|--------|-----------|---------------------|
| Users | company_admin+ (role-limited) | company_admin+ | super_user platform |
| Work orders | client_admin, site_manager, company roles | role-filtered list | status FSM by role |
| Reports | technician (draft) | WO access | company_admin, manager approve |
| Invoices | generate from verified WO | client_admin+ scoped | company_admin approve/send |
| Assets | company_admin, site_manager | scoped by client/site | lifecycle reset admin roles |

---

## Migrate existing databases

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg2://fms:fms@localhost:5432/fms_demo"
python -m scripts.migrate_roles
```

Docker demo migrate runs this after seed.

---

## Demo logins

See [../guides/demo-stack.md](../guides/demo-stack.md).

---

## Related

- [RBAC_ROLES.md](../phase3-restructure/RBAC_ROLES.md) — short redirect to this doc
- [knowledge-hub/backend/04_rbac.md](../knowledge-hub/backend/04_rbac.md) — tutorial
- `test_rbac.py` (51+ cases), `test_rbac_roles.py`, `test_isolation.py`
