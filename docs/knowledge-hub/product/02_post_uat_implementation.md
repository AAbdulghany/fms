# Post-UAT Implementation — NexTask Phase 1 & 2

**Date:** 2026-06-06  
**Branch:** `feature/phase-3-restructure/wave3`  
**Authors:** Team Leader + Architect agents  
**Status:** Verified 2026-06-20 — partial; see [03_wave4_mega_prompt.md](./03_wave4_mega_prompt.md) for gaps.

---

## Architect & Team Leader Discussion

### Design principles

1. **Soft delete everywhere** — Companies (`status=archived`), assets (`lifecycle_status=replaced`), work orders (status terminal states). Historical maintenance reports and invoices remain queryable.
2. **Metadata-first asset extensions** — Floor, room, smart labels, criticality, and `last_maintenance_date` live in `assets.metadata_json` to avoid a blocking migration; they are exposed as first-class fields on API schemas.
3. **Maintenance anchor date** — First `next_due_at` uses `installed_on + interval` when no `last_maintenance_date` (past dates stay overdue). See Wave 4 doc A1 for correction from earlier `today + interval` spec.
4. **WO state machine** — Existing enum values are retained (`created`, `assigned`, …) to avoid breaking clients. NexTask matrix names map to current statuses; transition rules are enforced in `work_order_fsm.py`.

### NexTask → FMS status mapping

| NexTask state | FMS `WorkOrderStatus` | Notes |
|---------------|----------------------|-------|
| OPEN | `created` | WO approved / direct-created |
| UNASSIGNED | `created` (no assignee) | Same status; assignee null |
| ASSIGNED | `assigned` | Requires `assignee_user_id` |
| IN_PROGRESS | `in_progress` | Technician or admin |
| ON_HOLD | `on_hold` | Requires `hold_reason` |
| RESOLVED | `completed` | Requires submitted maintenance report |
| CLOSED/VERIFIED | `verified` → `closed` | Manager sign-off |
| CANCELED | `cancelled` | Requires `cancellation_reason` via decline flow |

Request flow (`requested` → `created` / `declined`) remains for client/site managers.

### Database / schema changes

| Area | Change |
|------|--------|
| `assets.metadata_json` | Keys: `floor`, `room`, `smart_labels[]`, `criticality`, `last_maintenance_date` (ISO date string) |
| `clients` | Dashboard count filters `status = 'active'` |
| `dashboard` API | Remove `technicians_count`; keep `operational_users_count` optional |
| `maintenance_schedules` | `next_due_at` base = `last_maintenance_date` or `now()` |
| `work_orders` | FSM validation on PATCH; terminal states immutable |
| `seed.py` | Users-only bootstrap (no demo company/WO) |

No new tables. Optional future migration: promote metadata fields to columns if reporting needs indexing.

### WO transition matrix (enforced)

| From | To | Roles | Payload |
|------|-----|-------|---------|
| `created` | `assigned` | admin, company_admin, company_engineer, site_manager | `assignee_user_id` required |
| `assigned` | `in_progress` | assignee technician, admin | — |
| `in_progress` | `on_hold` | assignee, admin | `hold_reason` |
| `on_hold` | `in_progress` | assignee, admin | — |
| `in_progress` | `completed` | assignee | Report `submitted` or `approved` |
| `completed` | `verified` | admin, company_admin, company_engineer | — |
| `verified` | `closed` | admin, company_admin | — |
| `*` (non-terminal) | `cancelled` | admin, company_admin, company_engineer | Reason recommended |

**Re-assignment:** PATCH assignee on `assigned`/`in_progress` with audit entry; optional revert to `created` if assignee cleared.

**Immutability:** PATCH blocked when status ∈ `{closed, cancelled, verified}` except no-op.

---

## Sub-task assignment

| Task | Agent | Files |
|------|-------|-------|
| Dashboard archived count, remove technicians | Backend | `dashboard.py`, `schemas.py` |
| Clean seed | Backend | `seed.py` |
| Asset schema + PATCH + retire + filters | Backend | `schemas.py`, `assets.py`, `maintenance_schedules.py` |
| WO FSM validation | Backend | `work_order_fsm.py`, `work_orders.py` |
| Asset register/edit UI, retire, dashboard | Frontend | `AssetRegisterModal`, `AssetEditModal`, `AssetDetailPage`, `DashboardPage` |
| Users role filter + i18n | Frontend | `UsersPage`, `i18n/index.ts` |
| Architecture doc | Team Leader | This file |

---

## API changes summary

### Dashboard `GET /dashboard/summary`

- `clients_count` — active clients only (`status == active`)
- Removed: `technicians_count`

### Assets

- `POST /assets` — extended body (floor, room, smart_labels, criticality, warranty_until, last_maintenance_date)
- `PATCH /assets/{id}` — update asset fields
- `POST /assets/{id}/retire` — soft retire → `lifecycle_status = replaced`
- `GET /assets?filter=overdue|due_week` — fixed active-schedule logic
- `GET /assets?include_retired=true` — include retired assets

### Work orders

- `PATCH /work-orders/{id}` — FSM + payload validation; `hold_reason` on transition to `on_hold`
- Completion to `completed` requires maintenance report in `submitted` or `approved` status

---

## Seed users (clean environment)

| Email | Role | Password |
|-------|------|----------|
| admin@demo.com | company_admin | admin123 |
| engineer@demo.com | company_engineer | engineer123 |
| tech@demo.com | technician | tech123 |
| clientmgr@demo.com | client_admin | client123 |
| sitemgr@demo.com | site_manager | site123 |

No default company, site, asset, or work order.

---

## Verification checklist

- [ ] Archive company → dashboard companies count decreases
- [ ] Technicians card absent from dashboard
- [ ] Fresh seed → empty companies/assets/WO lists
- [ ] Register asset with past install date + schedule → `next_due` from today
- [ ] Asset filters: overdue / due week return correct rows
- [ ] Edit + retire asset preserves WO history
- [ ] WO cannot move to `assigned` without technician
- [ ] WO cannot move to `completed` without submitted report
- [ ] Users page filters by `company_engineer`

---

## References

- Prior UAT: [01_wave3_uat_observations.md](./01_wave3_uat_observations.md)
- WO request flow AgDR: `docs/phase3/AgDR-PHASE3-WO-REQUEST-FLOW.md`
- RBAC roles: [architecture/RBAC.md](../architecture/RBAC.md)
