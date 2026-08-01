# FMS Phase 2 — Master Plan & Agent Prompts

**Date:** April 17, 2026
**Phase:** 2 — Screen Fixes + Feature Expansion
**Version:** 1.0

---

## Current State Analysis

The MVP has the following **screen/navigation problems** observed:

1. **No company selection screen** after Super User login — goes straight to a generic dashboard
2. **No hierarchical navigation**: Company -> Sites -> Work Orders
3. **Work Order creation** does not auto-assign company/site from context
4. **No employee creation** screen for Super Admin
5. **Role-based page access** is only partially enforced (Invoices link gated, but no pages for Clients, Sites, Assets, Users)
6. **Missing pages entirely**: Clients list, Sites list, Assets list, Users/Employees management
7. **Dashboard** is generic — no role-specific customization
8. Several **broken references** in `WorkOrderDetailPage.tsx` (undefined `parts`, `approveReport`)

### Existing Backend Routes That Have NO Frontend Pages

- `GET/POST /clients` — no ClientsPage
- `GET/POST /sites` — no SitesPage
- `GET/POST /assets` — no AssetsPage
- `GET /users/me` — no user management page
- `GET/POST /parts-catalog` — no parts catalog page
- `GET/POST /pricing-profiles` — no pricing page
- `GET/POST /contracts` — no contracts page

### Known Backend Bugs

- `notifications.py` references `user.metadata_json` — User model has no such field
- `billing_actions.py` missing `Invoice` import
- `database.py` `do_orm_execute` listener body is `pass` — tenant filtering not enforced
- `WorkOrderDetailPage.tsx` references undefined `parts` / `approveReport`

---

## Phase 2 Scope

### P2-Fix: Screen Layout & Navigation Fixes

**Goal**: Restructure the app so each role sees the correct navigation flow.

**Super User / Company Admin flow after login:**
1. Welcome page with current tasks + dashboard stats
2. Sidebar: Companies/Clients, Employees, Work Orders, Invoices, Settings
3. Click Company -> see Sites -> click Site -> see Work Orders for that site
4. Can create new Company/Client
5. Can create employees (Company Admin, Technician) — Super User only

**Technician flow:**
1. Welcome page with assigned work orders
2. Sidebar: My Work Orders
3. Can view WO detail, change status (at certain levels), create/upload reports

**Client Manager flow:**
1. Welcome page with dashboard stats for their company
2. Sidebar: Sites, Work Orders, Billing/Invoices, Assets
3. Can see sites for their company, create work orders, approve billing, manage assets

**Site Manager flow:**
1. Welcome page with site-specific dashboard
2. Sidebar: Work Orders, Assets (scoped to their site only)
3. Full authority within their site

**Auto-assignment rule**: When creating a work order within a site context, `client_id` and `site_id` are auto-populated from the navigation context.

### Role Access Matrix (Corrected)

| Role | Access |
|------|--------|
| Super User | Everything + create employees (company admins, technicians) |
| Company Admin | Everything except creating employees; same page access as super user |
| Technician | View assigned WOs, change status at certain levels, create/upload reports |
| Client Manager | Sites for their company, create WOs, approve billing, asset management |
| Site Manager | Only their site, but full authority within it |

### Navigation Flow (Corrected)

- **Super User/Company Admin**: Login -> Welcome Page -> Companies list (sidebar) -> click Company -> Sites -> click Site -> Work Orders -> click WO -> Detail (receipt if applicable)
- **Technician**: Login -> Welcome Page (assigned WOs) -> WO Detail -> Report
- **Client Manager**: Login -> Welcome Page -> Sites -> WOs / Billing / Assets
- **Site Manager**: Login -> Welcome Page -> WOs / Assets (site-scoped)

---

### P2-F1: Filters View (Client Admin and above)

Add filtering/search capabilities to work order lists, invoices, and other list views:
- Status filter, date range, urgency, assignee, client, site
- Visible only for `client_admin`, `company_admin`, `super_admin`

### P2-F2: Asset Lifecycle Management

Track asset lifecycle with rules:
- Max repair count per asset (e.g., 3 repairs)
- Max age (e.g., 5 years from `installed_on`)
- When limit is reached: **auto-create a replacement work order**
- UI to view asset lifecycle timeline, maintenance history, remaining life

### P2-F3: Maintenance Tagging (Preventive/Protective)

- Add tags to work orders: `preventive`, `corrective`, `protective`
- Tags are filterable and visible on WO list
- No separate menu — tags on existing Work Orders

### P2-F4: Man Labor Management

- Track technician assignments, hours logged, hourly rates
- Availability/scheduling calendar
- Overtime tracking
- Performance metrics (WOs completed, avg time)
- Cost tracking per technician per work order

### P2-F5: Location Management

- Hierarchical locations: Region -> Building -> Floor -> Zone -> Room
- Map integration (optional Phase 3)
- Location-based asset grouping
- Location-based work order filtering
- QR code scanning for location identification

### P2-F6: Customized Dashboards + Welcome Pages

Role-specific dashboards:
- **Super User**: All companies overview, total WOs, revenue, SLA compliance, technician workload
- **Company Admin**: Same as Super User but scoped to their tenant
- **Client Admin**: Sites overview, open WOs per site, billing summary, asset health
- **Site Manager**: Site-specific WOs, asset status, upcoming maintenance

Welcome page per user:
- Current tasks assigned
- Pending approvals (if applicable)
- Key stats (open WOs, overdue, SLA warnings)
- Quick actions

---

## Agent Architecture

### Sub-Agents

| Agent | Skill File | Prompt File |
|-------|-----------|-------------|
| PM (Orchestrator) | `.claude/skills/pm.md` | `docs/phase2/prompt_pm.md` |
| Backend | `.claude/skills/senior-backend.md` | `docs/phase2/prompt_backend.md` |
| Frontend | `.claude/skills/senior-frontend.md` | `docs/phase2/prompt_frontend.md` |
| UI/UX (NEW) | `.claude/skills/senior-uiux.md` | `docs/phase2/prompt_uiux.md` |
| QA | `.claude/skills/senior-qa.md` | `docs/phase2/prompt_qa.md` |

### Execution Sequence

```
Fix Phase
  1. Fix broken references (frontend)
  2. Fix backend bugs (notifications, billing_actions, database)
  3. Restructure navigation/layout (sidebar, role-based nav)
  4. Add missing pages (Companies, Sites, Employees)
      |
      v
P2-F1: Filters
  Backend filter params -> Frontend FilterBar component
      |
      v
P2-F2: Asset Lifecycle
  Backend models + service -> Frontend lifecycle views
      |
      v
P2-F3: Maintenance Tags
  Backend tags field -> Frontend tag components
      |
      v
P2-F4: Man Labor
  Backend models + routes -> Frontend labor pages
      |
      v
P2-F5: Locations
  Backend location model + routes -> Frontend location tree
      |
      v
P2-F6: Dashboards
  Backend dashboard endpoint -> Frontend role-specific dashboards
      |
      v
QA Full Regression
      |
      v
Notification Testing
```

### Key Dependencies

- **Backend must complete** model changes and migrations before Frontend can consume new APIs
- **UI/UX agent** should produce specs first for each feature, then Frontend implements
- **QA** runs after each feature completion, full regression after P2-F6
- **Notifications** tested only after all features are complete
- **Filters (F1)** should be done early since it's used across many pages
- **Asset Lifecycle (F2)** depends on having Assets page working (from Fix Phase)
