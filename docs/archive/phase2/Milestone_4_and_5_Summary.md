# Milestones 4 & 5 — Implementation summary

## Milestone 4: New features (F4, F5, F6)

### Backend (FastAPI)

| Area | Details |
|------|---------|
| **P2-F5 Locations** | `Location` model (hierarchical `parent_id` under `site_id`), optional `location_id` on `Asset` and `WorkOrder`. Routes: `GET /locations`, `GET /locations/tree`, `POST/PATCH/DELETE /locations/{id}`. RBAC: super_admin, company_admin, client_admin, site_manager (scoped like sites). |
| **P2-F4 Labor** | `TechnicianProfile`, `LaborEntry`, `TechnicianSchedule` models. Routes under `/labor`: profiles CRUD (admin/manager), entries list/create, schedules list/create/delete. Technicians may log hours only for work orders where they are assignee. |
| **P2-F6 Dashboard** | `GET /dashboard/summary` returns role-aware aggregates: clients/sites/assets counts, open work orders, draft invoices, technician-specific assigned/in-progress counts, completed-this-week, assets at warning/EOL. |

**Migration:** `backend/migrations/versions/9a2b3c4d5e6f_milestone4_locations_labor_dashboard.py` (revises `7aa62ddc0ef8`).

**Apply:**

```powershell
uv run alembic -c backend/alembic.ini upgrade head
```

### Frontend

| Page / component | Details |
|------------------|---------|
| **Dashboard** | Loads `GET /dashboard/summary` and merges with recent work orders list. Invoice card shows **draft count** (not SAR). |
| **Locations** | Site selector + `LocationTree` fed from `GET /locations/tree?site_id=`. |
| **Labor** | Lists profiles (admins), labor entries, and schedules; routes allow manager + technician. |
| **Sidebar / App** | Labor nav visible for manager and technician; `/labor` route updated accordingly. |

### Types / i18n

- `DashboardSummary` in `src/lib/types.ts`.
- New keys: `invoice_drafts`, `no_locations`, `technician_profiles`, `labor_entries`, `role_manager`, etc. (AR + EN).

---

## Milestone 5: QA & validation

### Automated tests

- **76** backend tests passing (including 3 new RBAC checks for dashboard + location create).
- Existing suites: `test_rbac.py`, `test_isolation.py`, `test_asset_lifecycle.py`, `test_tenancy.py`.

### Manual checks (recommended)

1. **RBAC:** Confirm technician cannot call `GET /locations/tree` (403). Confirm site manager only sees own sites’ locations.
2. **Labor:** Create a labor entry as technician only for assigned WO; admin can create profiles and schedules.
3. **Dashboard:** Compare `/dashboard/summary` with UI cards for each role.
4. **Lifecycle E2E:** Complete repairs until replacement WO (existing asset lifecycle tests).
5. **Tenant isolation:** UUID guessing (covered by `test_isolation.py`).

### Regression

After pulling these changes, run:

```powershell
uv run pytest backend/tests/ -q
npm run build
```

---

## Files touched (reference)

- `backend/app/models.py` — new tables + `location_id` on assets/work orders  
- `backend/app/schemas.py` — location, labor, dashboard DTOs; `WorkOrder`/`Asset` optional `location_id`  
- `backend/app/api/routes/locations.py`, `labor.py`, `dashboard.py`  
- `backend/app/main.py` — router registration  
- `backend/app/api/routes/work_orders.py`, `assets.py` — location validation on create  
- `backend/migrations/versions/9a2b3c4d5e6f_*.py`  
- `src/pages/DashboardPage.tsx`, `LocationsPage.tsx`, `LaborPage.tsx`  
- `src/components/LocationTree.tsx`  
- `src/App.tsx`, `Sidebar.tsx`, `i18n/index.ts`, `lib/types.ts`  
- `backend/tests/test_rbac.py` — dashboard + location smoke tests  
