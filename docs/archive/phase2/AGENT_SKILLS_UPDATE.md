# Agent Skills Update — Phase 2

**Date:** April 17, 2026  
**Status:** Complete

---

## Summary

All agent skill files in `.claude/skills/` have been updated with comprehensive Phase 2 context, tasks, and detailed guidance. Each skill now includes:

1. Phase 2-specific tasks and priorities
2. References to detailed prompts in `docs/phase2/prompt_*.md`
3. Known issues from Phase 1 to fix
4. Role access matrix and navigation flows
5. Multi-tenant security and RBAC enforcement guidance
6. i18n/RTL requirements
7. Testing priorities and critical areas

---

## Updated Skill Files

### 1. `.claude/skills/pm.md` — Project Manager

**New content:**
- Phase 2 work items (P2-Fix, P2-F1 through P2-F6)
- Role access matrix (6 roles with corrected access levels)
- Navigation flow specifications per role
- Execution sequence (Fix → F1 → F2 → F3 → F4 → F5 → F6 → QA → Notifications)
- Key constraints (auto-assignment, asset lifecycle automation, tags not separate menu)
- Sub-agent coordination guidance
- Dependency tracking (backend models before frontend pages)

**Key additions:**
- References to `docs/phase2/Phase2_Master_Plan.md` and agent prompts
- RBAC and tenant isolation as critical review areas
- Asset lifecycle automation testing priority

---

### 2. `.claude/skills/senior-backend.md` — Backend Engineer

**New content:**
- Phase 2 backend tasks (26+ tasks across Fix Phase and 6 features)
- Multi-tenant architecture guidance (tenant_context, row-level isolation)
- New models: TechnicianProfile, LaborEntry, TechnicianSchedule, Location
- New routes: `/labor`, `/locations`, `/dashboard`
- Asset lifecycle service: `check_lifecycle()`, `trigger_replacement()`
- RBAC enforcement rules per role
- Known bugs to fix (metadata_json, Invoice import, database.py listener)

**Key additions:**
- Tenant isolation on EVERY query (critical security requirement)
- `require_roles()` decorator usage for all endpoints
- Asset lifecycle auto-creates replacement WO when limits reached
- Tags validation (preventive, corrective, protective only)
- Alembic migration generation for all model changes

---

### 3. `.claude/skills/senior-frontend.md` — Frontend Engineer

**New content:**
- Phase 2 frontend tasks (31+ tasks across Fix Phase and 6 features)
- Navigation restructure: flat routes → nested routes with sidebar
- 10+ new pages (Companies, Sites, Employees, Assets, Locations, Labor, Welcome)
- New components: Sidebar, FilterBar, AssetLifecycleTimeline, TagSelector, LocationTree
- Role-specific navigation structures (4 different sidebar layouts)
- Auto-assignment in work order creation from site context
- Broken references to fix in WorkOrderDetailPage.tsx

**Key additions:**
- RTL-first design approach (Arabic primary, use Tailwind logical properties)
- All text must use `t()` from react-i18next (no hardcoded strings)
- Breadcrumb navigation showing Company > Site > WO hierarchy
- Mobile-responsive sidebar (collapses to hamburger)
- Loading/error states for every async operation
- Chart library for role-specific dashboards (P2-F6)

---

### 4. `.claude/skills/senior-qa.md` — QA Engineer

**New content:**
- Phase 2 test priorities (10 test areas with criticality levels)
- RBAC matrix tests (CRITICAL) — test EVERY endpoint with all 6 roles
- Navigation flow tests (CRITICAL) — verify role-specific sidebar and breadcrumbs
- Asset lifecycle tests (HIGH) — verify auto-replacement WO creation
- Tenant isolation tests — cross-tenant access must be impossible
- Test strategy for filters, tags, labor, locations, dashboards
- Regression tests for existing functionality

**Key additions:**
- Prioritization: RBAC > Navigation > Asset Lifecycle > Filters > Tags > Labor > Location > Dashboard > i18n
- No flaky tests — use explicit waits, not sleep()
- Edge cases for asset lifecycle (no limits, one limit, already replaced)
- i18n/RTL testing for all new pages
- Test data cleanup (no interference between tests)

---

### 5. `.claude/skills/senior-uiux.md` — UI/UX Designer (NEW)

**New content:**
- Information architecture per role (4 distinct sidebar structures)
- Key screen specifications (10 major components/screens)
- Design system additions (sidebar colors, lifecycle badges, tag colors, chart palette)
- Empty states and error states (7 scenarios)
- Component specs: Sidebar, FilterBar, AssetLifecycleTimeline, LocationTree, DashboardCard

**Key additions:**
- Arabic-first design approach (design RTL first, then verify LTR)
- Sidebar: 240px desktop, 60px icon-only tablet, full overlay mobile
- Hierarchical navigation: breadcrumbs for Company > Site > WO
- WCAG 2.1 AA compliance (contrast, touch targets)
- Data density appropriate for facility management (data-heavy screens)
- Design tokens extension (never replace existing tokens)

---

## References

All skill files now reference:
- **Master Plan:** `docs/phase2/Phase2_Master_Plan.md`
- **Detailed Prompts:** `docs/phase2/prompt_pm.md`, `prompt_backend.md`, `prompt_frontend.md`, `prompt_uiux.md`, `prompt_qa.md`

---

## Usage

When invoking an agent for Phase 2 work, the agent will now have:
1. Full context of Phase 2 scope and priorities
2. Specific tasks to execute
3. Known issues to address
4. Role access matrix and navigation flows
5. Testing priorities and critical areas
6. Design specifications and UI patterns

Agents can be invoked using the skill names:
- `@pm` — Project Manager coordination
- `@senior-backend` — Backend development
- `@senior-frontend` — Frontend development
- `@senior-uiux` — UI/UX design
- `@senior-qa` — Quality assurance and testing

---

## Next Steps

1. Start with **Fix Phase** (PM coordinates Backend and Frontend agents)
2. Proceed sequentially through features F1-F6
3. QA validates after each feature
4. Full regression after P2-F6
5. Notification testing after all features complete
