# NexTask Wave 4 — Mega Prompt (Post Phase 1/2 Verification)

**Use this document as the single source of truth for agents.** Do not re-interpret requirements from chat; implement against task IDs below.

**Branch:** `feature/phase-3-restructure/wave3`  
**Tech Lead verification:** 2026-06-20  
**Prior docs:** [01_wave3_uat_observations.md](./01_wave3_uat_observations.md), [02_post_uat_implementation.md](./02_post_uat_implementation.md)

---

## System role

You are the NexTask (FMS) engineering team:

| Agent | Responsibility |
|-------|----------------|
| **Team Leader** | Orchestrate tasks, verify acceptance criteria, update this doc |
| **Architect** | WO state machine, schedule anchor rules, schema decisions |
| **Backend Engineer** | API, FSM, seeds, aggregations |
| **Frontend Engineer** | UI for transitions, reports, asset detail, filters |
| **QA** | Smoke tests per task ID |

---

## Architect decisions (binding)

### A1 — Maintenance first `next_due_at`

When `last_maintenance_date` is **null**:

1. If `installed_on` is set → **first due = `installed_on + interval`** (not `today + interval`).
2. If that date is **in the past** → leave it in the past so **Overdue** filters and T-7 job fire; do **not** skip to `today + interval`.
3. If both `last_maintenance_date` and `installed_on` are null → `today + interval`.

**Example:** Install 2026-05-13, monthly, today 2026-06-20 → `next_due_at = 2026-06-13` (overdue), **not** 2026-07-20.

### A2 — WO completion vs report (fix chicken-and-egg)

| Step | Status | Who | UI |
|------|--------|-----|-----|
| 1 | `in_progress` | Technician | **Report editor unlocked** |
| 2 | Save + Submit report | Technician | Report modal; labor/man-hours required |
| 3 | `completed` | Technician | Blocked until report `submitted` or `approved` |
| 4 | `verified` | Admin / company_engineer | Approve report if not already |
| 5 | Invoice | Admin | Existing generate-invoice flow |

Report section must be visible from **`in_progress`** (and `on_hold`), not only after `completed`.

### A3 — Status transition payloads (UI required)

| API error | When | UI location |
|-----------|------|-------------|
| `ASSIGNEE_REQUIRED` | → `assigned` | Assign user dropdown **before** Apply; or combined modal |
| `HOLD_REASON_REQUIRED` | → `on_hold` | Modal with required textarea `hold_reason` |
| `REPORT_REQUIRED` | → `completed` | Inline banner + link to report modal |
| `CANCELLATION_REASON_REQUIRED` | → `cancelled` | Modal with `cancellation_reason` |

PATCH body must include payload fields, not `{ status }` alone.

### A4 — Asset retire status

Backend uses `lifecycle_status = replaced`. Frontend must treat **`replaced` as retired** (badge, hide retire button).

### A5 — Clean environment

| Profile | Seed module | Data |
|---------|-------------|------|
| Dev | `app.seed` | Users only |
| Demo/pitch | `app.pitch_seed` | Users only (align with dev — **no default company/WO**) |

Reset DB or re-seed after changing seed modules.

---

## Task registry

### Phase 1 — Low priority / core (verify + close)

| ID | Priority | Title | Acceptance criteria | Owner | Status |
|----|----------|-------|---------------------|-------|--------|
| **NT-P1-01** | P1 | Companies count excludes archived | Archive company → dashboard `clients_count` decreases on refresh; API filters `Client.status == active` | BE + FE | **Done** — visibility refetch |
| **NT-P1-02** | P1 | Remove technicians summary | No technicians card on dashboard; `technicians_count` removed from API/types | FE + BE | **Done** |
| **NT-P1-03** | P1 | Clean seed (no demo company/WO) | Fresh DB: only seeded users; empty companies/assets/WO | BE | **Done** — `seed.py` + `pitch_seed.py` users-only |

### Phase 2 — Assets

| ID | Priority | Title | Acceptance criteria | Owner | Status |
|----|----------|-------|---------------------|-------|--------|
| **NT-P2-A01** | P1 | Register asset — extended fields | Modal + POST: floor, room, smart_labels, serial, criticality, warranty_until, last_maintenance_date (N/A if new) | FE + BE | **Done** |
| **NT-P2-A02** | P1 | Schedule anchor from install date | May install + monthly → first due June (not July); see A1 | BE | **Done** — `test_wave4_schedule_anchor.py` |
| **NT-P2-A03** | P1 | Edit asset | Edit button opens modal; PATCH works; fields persist on detail | FE | **Done** |
| **NT-P2-A04** | P1 | Retire asset | Retire → `replaced`; history preserved; button hidden after retire | FE + BE | **Done** |
| **NT-P2-A05** | P2 | Asset page maintenance filters | All / Overdue / Due this week return correct sets | BE + FE | **Done** |

### Phase 2 — Work orders

| ID | Priority | Title | Acceptance criteria | Owner | Status |
|----|----------|-------|---------------------|-------|--------|
| **NT-P2-W01** | P1 | Report workflow before complete | Report editable at `in_progress`; submit → then allow `completed` | FE + BE | **Done** |
| **NT-P2-W02** | P1 | Transition modals (hold/cancel/assignee) | hold_reason, cancellation_reason, assignee validation in UI | FE | **Done** |
| **NT-P2-W03** | P2 | WO lifecycle RBAC doc + UI hints | Status dropdown shows only legal next states; role hints | FE + Architect | **PARTIAL** — FSM backend only |
| **NT-P2-W04** | P2 | Invoice from verified report | completed → verified → generate invoice with man-hours | FE | Existing; verify after W01 |

### Phase 2 — Users

| ID | Priority | Title | Acceptance criteria | Owner | Status |
|----|----------|-------|---------------------|-------|--------|
| **NT-P2-U01** | P1 | Role filter scoped to actor | company_admin does not see super_admin filter; company_engineer filter works | FE | **Done** |
| **NT-P2-U02** | P1 | Seed role hierarchy | seed.py + pitch_seed.py include all test roles per A5 table | BE | **Done** |

---

## WO state machine (reference — do not drift)

```
requested → created | declined
created → assigned (assignee required) | cancelled
assigned → in_progress | on_hold (hold_reason) | cancelled
in_progress → on_hold (hold_reason) | completed (report submitted) | cancelled
on_hold → in_progress | cancelled
completed → verified | cancelled
verified → closed | cancelled
closed | cancelled → (terminal, immutable)
```

**Roles:** Technician = assignee only on own WOs for in_progress/on_hold/completed. Admin/company_admin/company_engineer/site_manager = assign, verify, cancel.

---

## Sub-agent assignment (Wave 4 sprint)

| Sprint lane | Tasks | Agent type |
|-------------|-------|------------|
| **Lane A — Schedule + seed** | NT-P2-A02, NT-P1-03, NT-P2-U02 | backend-engineer |
| **Lane B — WO report + transitions** | NT-P2-W01, NT-P2-W02, NT-P2-W03 | frontend-engineer + backend-engineer |
| **Lane C — Asset detail + filters** | NT-P2-A01, NT-P2-A03, NT-P2-A04, NT-P2-A05 | frontend-engineer |
| **Lane D — Dashboard + users** | NT-P1-01, NT-P1-02, NT-P2-U01 | frontend-engineer |
| **Lane E — QA + docs** | All IDs checklist | qa-engineer + tech-lead |

---

## Verification commands

```powershell
# Backend
cd backend
python -m pytest -q

# Frontend
npm run build

# Fresh dev seed (after DB reset)
python -m app.seed

# Dev stack
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d db migrate
cd backend && python -m uvicorn app.main:app --reload --port 8000
npm run dev   # or npm run build && npm run preview
```

**Important:** `npm run preview` serves **old** `dist/` until you run `npm run build` again.

---

## Tech Lead gap summary (2026-06-20)

| User observation | Verdict |
|------------------|---------|
| Companies count unchanged after archive | Likely stale dashboard session or need refetch; backend filter is correct |
| Technicians still shown | Stale preview build OR not rebuilt |
| Initial company/WO still present | **`pitch_seed.py`** or old database — not `seed.py` alone |
| Asset detail missing new fields | **Frontend mapping gap** on AssetDetailPage |
| May install → July due | **Schedule bug** — wrong anchor (A1) |
| Edit asset not working | Modal exists; verify PATCH + detail refresh |
| WO `REPORT_REQUIRED` / no report UI | **Critical** — report locked until completed |
| `HOLD_REASON_REQUIRED` | **No UI** for hold_reason on transition |
| company_engineer filter | Static filter list + possible missing seed user |

---

## Copy-paste agent prompt (minimal context)

```
Implement NexTask Wave 4 tasks from docs/knowledge-hub/product/03_wave4_mega_prompt.md.
Your assigned IDs: [NT-P2-A02, ...]
Follow Architect decisions A1–A5 exactly.
Run pytest + npm run build. Update task Status column when done.
Do not commit unless asked.
```
