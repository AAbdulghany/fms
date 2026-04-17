# Phase 2 Completion Plan: Stability & Feature Expansion

## Context
Phase 2 began with critical fixes and partial feature implementation (Filters, Asset Lifecycle, Tags). While backend logic for these exists, the frontend is missing most pages, the routing is flat (not hierarchical), database migrations are not applied, and there are zero automated tests for RBAC or tenant isolation. This plan transforms the "proof-of-concept" state into a production-ready foundation.

## Implementation Approach

### Milestone 1: Database & Testing Foundation
**Goal**: Establish a reliable schema and security baseline.
- **Migrations**: Generate and apply Alembic migrations for all `models.py` changes (User metadata, Asset lifecycle, WorkOrder tags).
- **RBAC Matrix Tests**: Create `backend/tests/test_rbac.py` to verify all 6 roles across all endpoints.
- **Tenant Isolation Tests**: Create `backend/tests/test_isolation.py` to ensure cross-tenant data access is blocked.
- **Lifecycle Automation Tests**: Verify `active` $\rightarrow$ `warning` $\rightarrow$ `replaced` transitions and auto-WO creation.

### Milestone 2: Frontend Infrastructure ("The Big Refactor")
**Goal**: Move from flat routing to a role-aware, hierarchical shell.
- **Layout & Sidebar**: Create `src/components/Layout.tsx` and `src/components/Sidebar.tsx` with RTL support.
- **Nested Routing**: Refactor `src/App.tsx` to implement:
  - `/dashboard` (Welcome/Widgets)
  - `/companies` $\rightarrow$ `/companies/:id` $\rightarrow$ `/sites` $\rightarrow$ `/sites/:id` $\rightarrow$ `/locations`
  - `/assets` $\rightarrow$ `/assets/:id`
  - `/work-orders` $\rightarrow$ `/work-orders/:id`
  - `/labor` (New)

### Milestone 3: Feature Completion (Pages & Components)
**Goal**: Build the UI for existing backend capabilities.
- **Administrative Pages**: `CompaniesPage`, `CompanyDetailPage`, `SitesPage`, `SiteDetailPage`, `EmployeesPage`.
- **Asset/Location UI**: `AssetsPage`, `AssetDetailPage` with `AssetLifecycleTimeline`.
- **Utility Components**: `TagSelector` (for WO forms) and `WelcomePage` (role-specific).

### Milestone 4: New Feature Implementation (F4, F5, F6)
**Goal**: Implement the remaining business domains.
- **P2-F5 (Locations)**: 
  - Backend: Hierarchical `Location` model + `routes/locations.py`.
  - Frontend: `LocationTree` component and `LocationsPage`.
- **P2-F4 (Man Labor)**: 
  - Backend: `TechnicianProfile`, `LaborEntry`, `TechnicianSchedule` models + `routes/labor.py`.
  - Frontend: `LaborPage`, `LaborEntryForm`, and `TechnicianScheduleView`.
- **P2-F6 (Dashboards)**: 
  - Backend: `routes/dashboard.py` for role-specific aggregations.
  - Frontend: Dashboard widgets integrated into `WelcomePage`.

### Milestone 5: QA & Final Validation
**Goal**: Full regression and security audit.
- **RBAC Audit**: Systematic check of all new endpoints (`/labor`, `/locations`, `/dashboard`) against roles.
- **E2E Lifecycle Test**: Validate the full "Asset End-of-Life $\rightarrow$ Replacement WO" flow.
- **Tenant Leak Test**: Verify UUID-guessing attacks are blocked.

## Critical Files

### Backend
- `backend/app/models.py`: Schema extensions.
- `backend/app/api/routes/labor.py` (New)
- `backend/app/api/routes/locations.py` (New)
- `backend/app/api/routes/dashboard.py` (New)
- `backend/tests/`: New RBAC and Isolation test suites.

### Frontend
- `src/App.tsx`: Routing overhaul.
- `src/components/Layout.tsx` & `src/components/Sidebar.tsx` (New)
- `src/pages/WelcomePage.tsx`, `src/pages/AssetsPage.tsx`, `src/pages/EmployeesPage.tsx` (New)

## Verification Plan
1. **Schema**: `alembic current` matches `models.py`.
2. **Security**: All tests in `backend/tests/test_rbac.py` and `test_isolation.py` pass.
3. **Navigation**: Verify a "Technician" cannot see "Companies" and a "Super User" can navigate `Company > Site > Location`.
4. **Lifecycle**: Trigger a "replacement" WO by completing the max number of repairs on an asset.
5. **L10n**: Verify all new pages and components render correctly in Arabic (RTL).
