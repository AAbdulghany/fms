# Automation Plan #1 — PM series until aging + next-action WO chain

**Status:** implemented (core) · auto-assign deferred  
**Owner:** Ops / CMMS  
**Depends on:** `MaintenanceSchedule`, `Asset.max_age_years` + `installed_on`, preventive `WorkOrder`

## Intent

When an asset is registered (or an asset type applies PM) with a frequency of **monthly / quarterly / semi-annual / yearly**:

1. **Calendar** shows every projected due date from the schedule cadence **until the asset’s aging EOL** (`installed_on + max_age_years`).
2. Exactly **one open preventive work order** exists as the **next action**.
3. When that WO is **completed**, the schedule advances and the **next** preventive WO is created automatically — until the next due would fall after EOL (schedule deactivates).

## Frequencies

| UI / store key | Interval |
|----------------|----------|
| `monthly` | 30 days |
| `quarterly` | 90 days |
| `semi_annual` | 182 days |
| `yearly` (`annually` alias) | 365 days |

Day deltas match the existing engine (not calendar-month anchors).

## Behaviour

| Trigger | Action |
|---------|--------|
| `create_schedule` (asset register / apply-PM) | Persist schedule + **seed** next-action WO (if site present) |
| Preventive WO → `completed` | Advance `next_due_at`; if still ≤ EOL → create next WO; else `is_active=false` |
| Cron `run_due_schedules` | Backfill missing open next-action WOs inside the 7-day lead window |
| `GET …/maintenance-calendar` | Expand all dues in the requested **year** capped by EOL |

## Aging cutoff

- EOL date = `expected_eol_date(asset)` from `installed_on` + `max_age_years`.
- If aging is unset, calendar still projects within the viewed year (capped at 500 occurrences per schedule).
- Past-EOL next dues deactivate the schedule instead of opening another WO.

## Deferred — Automation Plan #1b (auto-assign)

**Not implemented yet.** Needs location + workload data before shipping:

| Datum | Why |
|-------|-----|
| Technician / engineer **site or geo** (lat/lng or site affinity) | “Nearest person in location” |
| Open WO **urgency** + assignee load | “Fewer urgent tasks” |
| Role eligibility for PM vs CM | Avoid assigning wrong skill pool |
| Tenant policy: nearest vs least-loaded vs hybrid | Explicit rule, not hard-coded |

Until then, next-action WOs stay `status=created` with **no assignee**.

## Automation data (ready for later triggers)

On `create_schedule` / after a PM WO finishes, `MaintenanceSchedule.ai_meta_json` is refreshed with:

| Field | Meaning |
|-------|---------|
| `plan` | `pm_series_v1` |
| `automation_ready` | `true` — safe for notifiers |
| `dummy_reminders` | always `false` — no fake reminder rows |
| `next_due_at` / `days_until_next` | live next occurrence |
| `eol_at` / `days_until_eol` | aging cutoff |
| `projected_occurrence_count` | dues from anchor through EOL |
| `next_action_wo_id` | the single open preventive WO (if any) |

Read-side helper for future cron/notify workers: `list_pm_automation_candidates` in `backend/app/services/pm_automation_queue.py`.

## Code map

| Piece | Path |
|-------|------|
| Series + next action | `backend/app/services/maintenance_schedules.py` |
| Automation queue (read) | `backend/app/services/pm_automation_queue.py` |
| Calendar expansion | `backend/app/services/maintenance_calendar.py` |
| Complete hook | `backend/app/services/asset_lifecycle.py` → `on_preventive_work_order_finished` |
| Cron backfill | `backend/scripts/run_maintenance_job.py` |

## Out of scope

- Meter-based / condition-based PM  
- Auto-assign (#1b)  
- Changing day-delta math to calendar months/quarters  
- E-invoice / billing from PM WOs  
