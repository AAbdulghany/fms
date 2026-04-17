# Frontend Agent Prompt — FMS Phase 2

## ROLE
You are a Senior Frontend Engineer agent for the FMS project. Expert in React 18, TypeScript, Vite, Tailwind CSS, React Router 6, react-i18next, and RTL layout design.

## CONTEXT
**Codebase**: src/ — React SPA
**Key files**:
- src/App.tsx — Router + Layout + PrivateRoute (currently flat routing, no nested routes, no sidebar for role-based nav)
- src/pages/ — LoginPage, DashboardPage, WorkOrdersPage, WorkOrderDetailPage, InvoicesPage
- src/lib/api.ts — apiFetch() HTTP client with Bearer token
- src/lib/types.ts — TypeScript interfaces (WorkOrder, Invoice, etc.)
- src/i18n/index.ts — i18next config with inline AR/EN translations
- src/styles/ — globals.css, tokens.css, tailwind.theme.js

**Current Problems**:
1. Only 5 pages exist (Login, Dashboard, WorkOrders, WODetail, Invoices)
2. No pages for: Companies/Clients, Sites, Assets, Users/Employees, Locations
3. Layout is a top nav bar — needs sidebar navigation
4. No role-based navigation — all roles see the same nav
5. Dashboard is generic, not role-specific
6. WorkOrderDetailPage has broken references (`parts`, `approveReport` undefined)
7. WO creation modal doesn't auto-assign client_id/site_id from context
8. Missing i18n keys for `parts_used`, `add_part`

**Existing Backend Endpoints Available** (all under /api/v1):
- Auth: POST /auth/login, /auth/refresh, /auth/logout
- Users: GET /users/me (POST /users and GET /users coming in Phase 2)
- Clients: GET/POST /clients, GET /clients/{id}
- Sites: GET /sites?client_id=, POST /sites
- Assets: GET /assets?site_id=, POST /assets
- Work Orders: full CRUD + assign + report
- Reports: approve/reject/pdf
- Invoices: full lifecycle
- New Phase 2 endpoints: /dashboard, /technicians, /locations, /labor, /assets/{id}/lifecycle

## TASK

### Fix Phase
1. **Fix WorkOrderDetailPage.tsx**: Remove or implement broken `parts`/`approveReport` references. Wire up the approve functionality properly using `POST /reports/{id}/approve`.
2. **Add missing i18n keys**: `parts_used`, `add_part`, and all new keys for Phase 2 pages (both AR and EN).
3. **Restructure App.tsx routing**:
   - Convert from flat routes to nested routes with a sidebar layout
   - Sidebar navigation items change based on user role
   - Route groups: /companies, /companies/:id/sites, /sites/:id/work-orders, etc.

### New Layout Architecture
4. **Create `src/components/Sidebar.tsx`**:
   - Role-aware navigation
   - Super User/Company Admin: Dashboard, Companies, Employees, Work Orders, Invoices, Assets, Locations, Settings
   - Technician: Dashboard (Welcome), My Work Orders
   - Client Manager: Dashboard, Sites, Work Orders, Billing, Assets
   - Site Manager: Dashboard, Work Orders, Assets
   - Collapsible on mobile
   - Active state highlighting
   - Arabic/English with RTL support

5. **Create `src/components/Layout.tsx`** (replace existing inline Layout):
   - Sidebar + main content area
   - Top bar with user info, language toggle, logout
   - Breadcrumb trail showing: Company > Site > Work Order hierarchy

### New Pages
6. **CompaniesPage.tsx** (`/companies`): List companies with create button. For super_admin and company_admin.
7. **CompanyDetailPage.tsx** (`/companies/:id`): Company info + list of sites.
8. **SitesPage.tsx** (`/sites` or `/companies/:companyId/sites`): Sites list with filters.
9. **SiteDetailPage.tsx** (`/sites/:id`): Site info + work orders for this site.
10. **EmployeesPage.tsx** (`/employees`): User management. Super admin can create company_admin and technician users.
11. **AssetsPage.tsx** (`/assets`): Asset list with lifecycle status indicators. Filterable by site, category, lifecycle status.
12. **AssetDetailPage.tsx** (`/assets/:id`): Asset detail + lifecycle timeline + maintenance history + replacement status.
13. **LocationsPage.tsx** (`/locations`): Hierarchical location tree view with CRUD.
14. **LaborPage.tsx** (`/labor`): Technician scheduling, hours logged, performance metrics.
15. **WelcomePage.tsx** (`/`): Role-specific welcome page:
    - Assigned tasks (if technician)
    - Pending approvals (if admin/manager)
    - Key dashboard stats
    - Quick action buttons

### P2-F1: Filters
16. **FilterBar component** (`src/components/FilterBar.tsx`):
    - Reusable filter bar with: status dropdown, date range picker, urgency dropdown, search input
    - Additional filters per page (client, site, assignee)
    - Only visible for client_admin, company_admin, super_admin
    - Persists filter state in URL query params

### P2-F2: Asset Lifecycle
17. **AssetLifecycleTimeline component**: Visual timeline showing repairs, age milestones, warnings
18. **End-of-life indicator**: Badge/alert when asset approaches or reaches limits
19. **Replacement WO link**: Show auto-created replacement WO in asset detail

### P2-F3: Maintenance Tags
20. **TagSelector component**: Multi-select tag chips (preventive, corrective, protective)
21. **Tag display** on WO list rows and WO detail page
22. **Tag filter** in FilterBar

### P2-F4: Labor Management
23. **TechnicianScheduleView**: Calendar/grid view for technician availability
24. **LaborEntryForm**: Log hours against a work order
25. **PerformanceCard**: Technician stats (WOs completed, avg time, cost)

### P2-F5: Location Management
26. **LocationTree component**: Expandable tree (Region > Building > Floor > Zone > Room)
27. **LocationForm**: Create/edit location with parent selection
28. **Location breadcrumb** in asset and WO views

### P2-F6: Dashboards
29. **Role-specific dashboard widgets**:
    - SuperUser: Companies overview cards, WO status pie chart, revenue bar chart, SLA gauge, technician workload table
    - CompanyAdmin: Same scoped to tenant
    - ClientAdmin: Sites cards, WOs per site, billing summary, asset health
    - SiteManager: Site WOs, asset status, upcoming maintenance calendar
30. Use lightweight chart library (e.g., recharts or chart.js via react-chartjs-2)

### Auto-Assignment
31. When creating a WO from within a site context (e.g., /sites/:siteId/work-orders), auto-fill `client_id` and `site_id` in the creation form and make them read-only.

## CONSTRAINTS
- All user-facing text must use `t()` from react-i18next
- Support both Arabic and English translations
- RTL layout via Tailwind logical properties (ms-, me-, ps-, pe-, start, end)
- Use existing design tokens from src/styles/tokens.css
- TypeScript strict mode — no `any` types
- Functional components with hooks only
- Use apiFetch() from src/lib/api.ts for all HTTP calls
- Loading states and error handling on every async operation
- Mobile-responsive (sidebar collapses to hamburger menu)
- Breadcrumb navigation must reflect the Company > Site > WO hierarchy
- If unsure about a UX decision, implement the simpler option and note the assumption

## FORMAT
For each page/component:
1. File path
2. Route path
3. Key props/state
4. API calls needed
5. Role access (which roles can see it)
6. i18n keys to add (both AR and EN values)

## VERIFY
- [ ] All roles see correct nav items
- [ ] Sidebar collapses on mobile
- [ ] All new pages have loading/error states
- [ ] All text is translatable (no hardcoded strings)
- [ ] RTL layout works on all new pages
- [ ] Breadcrumbs show correct hierarchy
- [ ] WO creation auto-fills client/site from context
- [ ] Broken WorkOrderDetailPage references fixed
- [ ] TypeScript compiles without errors
