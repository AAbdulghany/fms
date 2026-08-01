# Wave 3 UAT Observations — Maintenance Company Admin

**Captured:** 2026-06-17  
**Tester persona:** Maintenance company admin (`company_admin` — user referred to as *maintenance_admin*)  
**Build tested:** `feature/phase-3-restructure/wave3` (local dev + Docker `fms`)  
**Purpose:** Product feedback for future waves, tickets, and knowledge-hub reference.  
**Status:** ✅ All 18 observations closed in Wave 3 (2026-06-22).  
**Wave closure record:** [WAVE3_OBSERVATIONS.md](../../phase3-restructure/WAVE3_OBSERVATIONS.md)

---

## How to use this doc


| Column       | Meaning                                       |
| ------------ | --------------------------------------------- |
| **ID**       | Stable reference for tickets (`OBS-`*)        |
| **Current**  | What the app does today (verified in code)    |
| **Expected** | What the tester wants                         |
| **Gap**      | Implementation delta                          |
| **Priority** | Suggested triage: P1 must, P2 should, P3 nice |


Link new GitHub issues as: `[Feature] OBS-DASH-02 — Dashboard assets summary card`.

---

## Summary matrix


| ID          | Area        | Title                                                        | Priority | Status                                           |
| ----------- | ----------- | ------------------------------------------------------------ | -------- | ------------------------------------------------ |
| OBS-DASH-01 | Dashboard   | “Users” stat shows technician count, not user count          | P2       | Fixed — card labeled **Technicians**             |
| OBS-DASH-02 | Dashboard   | Add assets summary (parity with work orders)                 | P1       | Fixed — assets card + EOL subtitle               |
| OBS-DASH-03 | Dashboard   | “Create work order” should open modal, not redirect          | P1       | Fixed — `?open=create`                           |
| OBS-DASH-04 | Dashboard   | “Add company” should open modal, not redirect                | P1       | Fixed — `?create=1`                              |
| OBS-COMP-01 | Companies   | Add-company flow must include required site + geo fields     | P1       | Fixed — provision + modal                        |
| OBS-COMP-02 | Companies   | Decouple “add site” from “create site manager”               | P1       | Fixed — `SiteProvisionModal` add-only mode       |
| OBS-AST-01  | Assets      | Register-asset modal missing full asset information fields   | P1       | Fixed — installed_on, max_age_years, age preview |
| OBS-AST-02  | Assets      | Schedule → calendar + auto WO (due date, 1-week lead)        | P1       | Fixed — T-7 lead in `run_due_schedules`          |
| OBS-AST-03  | Assets      | List/detail must show asset **name** and **type** clearly    | P2       | Fixed — name + category columns                  |
| OBS-AST-04  | Assets      | Fix asset lifecycle timeline UI                              | P2       | Fixed — timeline spacing/RTL                     |
| OBS-AST-05  | Assets      | Calendar panel shows active WOs, not upcoming scheduled      | P1       | Fixed — scheduled section + open WOs             |
| OBS-AST-06  | Assets      | Maintenance history = completed WO summary per asset         | P1       | Fixed — completed/verified/closed tab            |
| OBS-AST-07  | Assets      | Work orders tab must be asset-scoped only                    | P2       | Fixed — asset filter + create with asset_id      |
| OBS-AST-08  | Assets      | Visibility into report templates (read-only browse)          | P2       | Fixed — `/report-templates` page                 |
| OBS-WO-01   | Work orders | Mandatory linked asset on create/request (all urgency types) | P1       | Fixed — backend + asset picker UI                |
| OBS-USR-01  | Users       | Tenant staff must not see SW/platform users in list          | P1       | Fixed — list_users filter                        |


---

## 1. Dashboard

**Relevant code:** `src/pages/DashboardPage.tsx`, `backend/app/api/routes/dashboard.py`

### OBS-DASH-01 — What does “Users” refer to?

**Observation:** The fourth stats card is labeled **Users** but the value comes from `technicians_count` in `/dashboard/summary`, not total users.

**Current behavior:**

```117:121:src/pages/DashboardPage.tsx
          <StatsCard
            label={t("users")}
            value={stats.technicians_count ?? "—"}
            onClick={() => navigate("/users")}
          />
```

Backend counts users with role `technician` only (`dashboard.py`).

**Expected:** Label and metric should match user intent — either rename to **Technicians** or show a meaningful user count (engineers + site managers + technicians, excluding platform staff).

**Gap:** Copy vs metric mismatch; no assets card despite `assets_count` being available in summary API.

**Priority:** P2

---

### OBS-DASH-02 — Assets summary like work orders

**Observation:** Dashboard emphasizes companies, active WOs, invoice drafts, and users — but not **assets** (count, overdue maintenance, EOL, etc.).

**Current behavior:** `DashboardSummaryOut` includes `assets_count` and `assets_at_eol` but the UI does not surface an assets stats card for tenant staff.

**Expected:** At least one assets summary card (total assets, due this week, at EOL) with drill-down to `/assets`, similar to work-order stats.

**Gap:** Frontend dashboard layout; optional backend aggregates for “due this week” if not already exposed.

**Priority:** P1

---

### OBS-DASH-03 — “Create work order” opens modal (not redirect)

**Observation:** Quick action **+ Create Work Order** navigates to `/work-orders` instead of opening the create modal inline.

**Current behavior:**

```249:254:src/pages/DashboardPage.tsx
              <button
                onClick={() => navigate("/work-orders")}
                ...
                + {t("create_work_order")}
```

Client/site roles already use modal pattern: `navigate("/work-orders?open=request&view=my_requests")` for **Request work order**.

**Expected:**


| Role                                               | Button label       | Action                                                             |
| -------------------------------------------------- | ------------------ | ------------------------------------------------------------------ |
| `client_admin`, `site_manager`                     | Request work order | Open request modal (already correct)                               |
| `company_admin`, `company_engineer`, `super_admin` | Create work order  | Open **create** modal (`?open=create`) — **no full-page redirect** |


Apply same pattern everywhere a “Create work order” button appears for staff (Dashboard, Asset detail, Company detail, Site detail).

**Gap:** Replace `navigate("/work-orders")` with query-param modal open; ensure `WorkOrdersPage` handles `open=create`.

**Priority:** P1

---

### OBS-DASH-04 — “Add company” opens modal (not redirect)

**Observation:** **+ Add company** navigates to `/companies` instead of opening `CompanyCreateModal`.

**Current behavior:**

```255:260:src/pages/DashboardPage.tsx
              <button
                onClick={() => navigate("/companies")}
                ...
                + {t("add_company")}
```

`CompaniesPage` already hosts `CompanyCreateModal` — same pattern as assets (`?register=1`).

**Expected:** Dashboard button opens add-company popup directly (`navigate("/companies?create=1")` or shared modal state).

**Gap:** Dashboard quick action + optional deep-link on Companies page.

**Priority:** P1

---

## 2. Companies

**Relevant code:** `src/components/CompanyCreateModal.tsx`, `src/components/SiteProvisionModal.tsx`, `backend/app/api/routes/clients.py`, `sites.py`

### OBS-COMP-01 — Add company: required site, timezone, country, city-as-location

**Observation:** Creating a company only collects legal name, manager name, and activity type. No **initial site** is created with geographic context.

**Current behavior:** `POST /clients/provision` provisions client + client admin user only. Site fields exist on **Add site** (`SiteProvisionModal`: timezone, city, country) but not on company create.

**Expected on Add company popup:**


| Field                | Rule                                                                                  |
| -------------------- | ------------------------------------------------------------------------------------- |
| Site / location name | **Required** — represents the city or primary site label                              |
| City                 | Required (site location = city)                                                       |
| Country              | Required parameter on client/site address                                             |
| Timezone             | Auto-detect from browser/`Intl.DateTimeFormat().resolvedOptions().timeZone`, editable |


**Gap:** Extend provision API + `CompanyCreateModal`; align with `Site.address_json` / `Site.timezone` model.

**Priority:** P1

---

### OBS-COMP-02 — Separate “add site” from “assign site manager”

**Observation:** Adding a site via `SiteProvisionModal` always creates a **site manager user** in the same step. Tester wants site creation and manager assignment decoupled.

**Current behavior:** `POST /sites/provision` creates site + site_manager user atomically.

**Expected:**

1. **Add site** button — site record only (name, city, country, timezone).
2. **Assign site manager** — separate action; pick existing user or invite new; bind to a specific site.

**Gap:** New API endpoints or flags on provision; UI split on `CompanyDetailPage` / site list.

**Priority:** P1

---

## 3. Assets

**Relevant code:** `src/components/AssetRegisterModal.tsx`, `src/pages/AssetsPage.tsx`, `src/pages/AssetDetailPage.tsx`, `src/components/MaintenanceCalendar.tsx`, `src/components/AssetWorkOrderPanel.tsx`, `backend/app/services/maintenance_schedules.py`

### OBS-AST-01 — Register asset: full information in popup

**Observation:** Register flow should expose structured fields like the detail view:


| Field             | Example              |
| ----------------- | -------------------- |
| Asset ID / label  | AC2                  |
| Type              | AC2                  |
| Category          | general              |
| Installation date | (date picker)        |
| Expected lifespan | 5 years              |
| Current age       | computed (read-only) |


**Current behavior:** Modal has name, category, model, serial, schedule toggle — no installation date, lifespan, or live age preview in the form.

**Expected:** Register popup mirrors **Asset Information** section on detail page; age computed from installation date before save.

**Gap:** Form fields + `AssetCreate` payload (`installed_on`, `max_age_years`).

**Priority:** P1

---

### OBS-AST-02 — Maintenance schedule → calendar + automatic work order

**Observation:** When register asset + enable maintenance schedule:

1. Entry must appear on **maintenance calendar**.
2. **One week before** the due date, system should create a preventive work order automatically.
3. On the **due date**, WO should exist / be actionable (tester: “create the work order automatically on the specific date”).

**Current behavior:**

- Schedule creates `MaintenanceSchedule` with `next_due_at` (`create_schedule`).
- `run_due_schedules()` creates preventive WOs when `next_due_at <= now` (no 1-week lead).
- Calendar reads schedules, not future WOs.

**Expected:**

```
Schedule created → visible on calendar at due date(s)
T-7 days        → auto-create preventive WO (status created/assigned)
Due date        → WO ready for technician
```

**Gap:** Lead-time parameter (7 days); background job cadence; calendar may need to show **scheduled** events vs **open** WOs distinctly.

**Priority:** P1  
**Related:** Wave 3 NT-117–119; preventive job in `maintenance_schedules.py`

---

### OBS-AST-03 — Show asset name and type on Assets page

**Observation:** Table emphasizes label/category but not clearly **name** and **type** as distinct columns.

**Current behavior:** `AssetsPage` maps `type` and `category` from API; display uses `asset_id` (label) prominently.

**Expected:** Columns or header: **Asset name**, **Type**, **Category** (name ≠ type when they differ).

**Gap:** Table columns + `AssetOut` mapping in list view.

**Priority:** P2

---

### OBS-AST-04 — Fix asset lifecycle timeline UI

**Observation:** Lifecycle timeline component needs visual/UX fix on asset detail.

**Current behavior:** `AssetLifecycleTimeline` on `AssetDetailPage` details tab.

**Expected:** Tester to provide screenshot in follow-up; document as UX debt until design spec attached.

**Gap:** Frontend polish — layout, markers, RTL, mobile.

**Priority:** P2

---

### OBS-AST-05 — Calendar click shows upcoming work, not only active WOs

**Observation:** Selecting an asset on the maintenance calendar opens `AssetWorkOrderPanel`, which filters to **open/in-progress** statuses only — not **upcoming scheduled** maintenance.

**Current behavior:**

```8:14:src/components/AssetWorkOrderPanel.tsx
const OPEN_STATUSES = new Set([
  "requested", "created", "assigned", "in_progress", "on_hold",
]);
```

**Expected:** Panel shows **next scheduled maintenance** (from schedule `next_due_at`) plus linked open WOs; distinguish “scheduled” vs “active”.

**Gap:** Panel data model; optional API `GET /assets/{id}/maintenance-upcoming`.

**Priority:** P1

---

### OBS-AST-06 — Maintenance history = completed work orders summary

**Observation:** **Maintenance** tab should summarize **completed** work orders for the asset, not generic WO list.

**Current behavior:** `AssetDetailPage` maintenance tab filters WOs by category preventive/corrective but includes all statuses.

**Expected:** Maintenance history = completed/verified/closed WOs with date, engineer, hours summary (table or timeline).

**Gap:** Tab query filter + empty state copy.

**Priority:** P1

---

### OBS-AST-07 — Work orders tab: asset-scoped only

**Observation:** Work orders tab must show only WOs for **this asset**.

**Current behavior:** Already fetches `/work-orders?asset_id={id}` — likely OK unless UI shows unrelated rows or missing filter on create-from-detail.

**Expected:** Confirm no cross-asset leakage; create-WO from asset pre-fills `asset_id`.

**Gap:** Verify + fix create-WO from asset detail (OBS-DASH-03 pattern).

**Priority:** P2

---

### OBS-AST-08 — View report templates

**Observation:** Tester needs to **see** report templates (for maintenance schedule selection and understanding inspection forms).

**Current behavior:** Templates loaded inside register modal only (`GET /report-templates`); no standalone browse page.

**Expected:** Read-only list (Settings or Assets sub-nav): template name, code, linked maintenance types; platform admin can manage, tenant admin can view.

**Gap:** New page or modal catalog; RBAC for template CRUD vs read.

**Priority:** P2

---

## 4. Work orders

**Relevant code:** `src/pages/WorkOrdersPage.tsx`, `backend/app/api/routes/work_orders.py`

### OBS-WO-01 — Mandatory asset on every work order

**Observation:** Creating or requesting a work order must include the **asset** under maintenance. Applies to urgent, normal, and preventive types. No WO without a linked asset.

**Current behavior:** Asset may be optional on create depending on form validation and API schema.

**Expected:**


| Field      | Rule                                             |
| ---------- | ------------------------------------------------ |
| `asset_id` | **Required** on create and request               |
| Urgency    | urgent / normal / preventive — all require asset |
| UI         | Asset picker with site/client context            |


**Gap:** Frontend validation + backend `WorkOrderCreate` constraint + migration if legacy null `asset_id` rows exist.

**Priority:** P1  
**Wave candidate:** Wave 4 or hotfix ticket

---

## 5. Users

**Relevant code:** `src/pages/UsersPage.tsx`, `backend/app/api/routes/users.py`, `backend/app/rbac.py`

### OBS-USR-01 — User list scope for maintenance company staff

**Observation:** For any user **except** `super_user` and `sw_dev`, the Users page must **not** list SW company / platform staff. Only users belonging to the maintenance tenant’s operational roles:

- Maintenance company: `company_admin`, `company_engineer`
- Clients: `client_admin`
- Sites: `site_manager`
- Field: `technician`, `manager`

**Current behavior:**

```92:96:backend/app/api/routes/users.py
    users = db.scalars(
        select(User)
        .where(User.tenant_id == current.tenant_id)
        ...
```

Returns **all** tenant users including `super_user`, `sw_dev` if seeded in same tenant, and does not hide platform admins by flag.

**Expected:**


| Viewer                              | Sees                                                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------ |
| `super_user`, `sw_dev`              | Full tenant user list (platform ops)                                                 |
| `company_admin`, `company_engineer` | Operational users only; exclude `is_platform_admin`, exclude `super_user` / `sw_dev` |
| `client_admin`                      | Users scoped to own client (future)                                                  |


**Gap:** Backend filter in `list_users`; optional frontend guard; align with RBAC doc.

**Priority:** P1  
**Security note:** Prevents client admins seeing platform credentials metadata.

---

## Role glossary (tester language → system)


| Tester term       | System role     | Notes                            |
| ----------------- | --------------- | -------------------------------- |
| maintenance_admin | `company_admin` | Maintenance company tenant admin |
| SW developers     | `sw_dev`        | Platform staff                   |
| super user        | `super_user`    | Platform super admin             |
| Client            | `client_admin`  | End-client company admin         |


---

## Suggested wave / ticket grouping

> **Update 2026-06-22:** All items below were implemented in **Wave 3** (not Wave 4). See [WAVE3_OBSERVATIONS.md](../../phase3-restructure/WAVE3_OBSERVATIONS.md) for closure evidence.


| Bucket                     | OBS IDs                               | Milestone (actual)        |
| -------------------------- | ------------------------------------- | ------------------------- |
| **Wave 3 — Dashboard**     | OBS-DASH-03, OBS-DASH-04, OBS-DASH-01 | ✅ Wave 3 sign-off         |
| **Wave 3 — Companies**     | OBS-COMP-01, OBS-COMP-02              | ✅ Wave 3 sign-off         |
| **Wave 3 — Assets depth**  | OBS-AST-01–08, OBS-AST-02             | ✅ Wave 3 sign-off         |
| **Wave 3 — WO governance** | OBS-WO-01                             | ✅ Wave 3 sign-off         |
| **Wave 3 — RBAC**          | OBS-USR-01                            | ✅ Wave 3 sign-off         |


---

## Code index (quick navigation)


| Topic                | Primary files                                                        |
| -------------------- | -------------------------------------------------------------------- |
| Dashboard stats      | `src/pages/DashboardPage.tsx`, `backend/app/api/routes/dashboard.py` |
| Company create       | `src/components/CompanyCreateModal.tsx`                              |
| Site provision       | `src/components/SiteProvisionModal.tsx`                              |
| Asset register       | `src/components/AssetRegisterModal.tsx`                              |
| Asset detail tabs    | `src/pages/AssetDetailPage.tsx`                                      |
| Maintenance calendar | `src/components/MaintenanceCalendar.tsx`, `AssetWorkOrderPanel.tsx`  |
| Schedule → WO job    | `backend/app/services/maintenance_schedules.py`                      |
| Work order create    | `src/pages/WorkOrdersPage.tsx`                                       |
| User list API        | `backend/app/api/routes/users.py`                                    |


---

## Changelog


| Date       | Author                  | Change                                                  |
| ---------- | ----------------------- | ------------------------------------------------------- |
| 2026-06-17 | UAT (maintenance_admin) | Initial observations captured                           |
| 2026-06-17 | Agent                   | Analyzed against codebase; structured for knowledge hub |
| 2026-06-22 | Tech Lead               | All 18 closed — [WAVE3_OBSERVATIONS.md](../../phase3-restructure/WAVE3_OBSERVATIONS.md) |

---

**Next step:** ~~File GitHub issues per `OBS-*` ID~~ — closed in Wave 3. Use `OBS-*` IDs as stable references in future regressions only.