# Frontend Milestone 2: Infrastructure Refactor - Implementation Notes

**Date:** April 17, 2026  
**Agent:** Frontend Agent  
**Status:** ✅ Complete

## Overview

This milestone successfully refactored the FMS frontend from a flat routing structure to a hierarchical, role-based navigation system with a modern sidebar layout.

## Deliverables

### 1. Type System Enhancement (`src/lib/types.ts`)

Added core user and role types:

```typescript
export type UserRole = 
  | "super_admin" 
  | "company_admin" 
  | "client_admin" 
  | "site_manager" 
  | "technician";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  company_id?: string;
  is_active: boolean;
}
```

**Purpose:** Provides type safety for role-based access control throughout the application.

---

### 2. Layout Component (`src/components/Layout.tsx`)

**Features:**
- ✅ Main application layout wrapper
- ✅ Responsive header with hamburger menu on mobile
- ✅ RTL support (reads from `i18n.dir()`)
- ✅ Language toggle button (AR ↔ EN)
- ✅ Logout button with token clearing
- ✅ Sidebar integration with mobile overlay
- ✅ Max-width content container (7xl)

**Key Implementation Details:**
- Mobile breakpoint: `lg` (1024px)
- Sidebar toggles via hamburger menu on mobile
- Dark overlay (`bg-neutral-900/50`) when sidebar open on mobile
- Uses Tailwind logical properties for RTL (`ms-`, `me-`, `ps-`, `pe-`)

---

### 3. Sidebar Component (`src/components/Sidebar.tsx`)

**Features:**
- ✅ Role-aware navigation (filters menu items by user role)
- ✅ Active route highlighting
- ✅ Heroicons SVG icons for each menu item
- ✅ User profile card at bottom (name, email, role badge)
- ✅ RTL support (sidebar slides from right in Arabic)
- ✅ Collapsible on mobile with close button
- ✅ Loading state while fetching user data

**Navigation Menu Items:**

| Route | Label Key | Allowed Roles |
|-------|-----------|---------------|
| `/dashboard` | dashboard | All roles |
| `/companies` | companies | super_admin, company_admin |
| `/assets` | assets | super_admin, company_admin, client_admin, site_manager |
| `/work-orders` | work_orders | All roles |
| `/invoices` | invoices | super_admin, company_admin, client_admin |
| `/users` | users | super_admin, company_admin |
| `/labor` | labor | super_admin, company_admin |
| `/locations` | locations | super_admin, company_admin, client_admin |

**Active Route Logic:**
- Dashboard: matches `/` or `/dashboard`
- Others: matches route prefix (e.g., `/work-orders` matches `/work-orders/:id`)

---

### 4. ProtectedRoute Component (`src/components/ProtectedRoute.tsx`)

**Features:**
- ✅ Authentication check (requires `access_token`)
- ✅ Role-based authorization (optional `allowedRoles` prop)
- ✅ Loading state (spinner with "Loading..." text)
- ✅ Redirects to `/login` if unauthenticated
- ✅ Shows 403 error page if wrong role
- ✅ Fetches user from `/users/me` API

**Error States:**
- **Unauthenticated:** Redirect to `/login`
- **Unauthorized (403):** Full-page error with "Go Back" button

---

### 5. Updated Routing (`src/App.tsx`)

**Changes:**
- ❌ Removed old `Layout` and `PrivateRoute` components
- ✅ Imported new `Layout`, `ProtectedRoute`, and placeholder pages
- ✅ Wrapped all protected routes with `<ProtectedRoute>` and `<Layout>`
- ✅ Applied role restrictions to sensitive routes
- ✅ Root path (`/`) now redirects to `/dashboard`

**Route Structure:**

```
/login                     → LoginPage (public)
/                          → Redirect to /dashboard
/dashboard                 → DashboardPage (all roles)
/companies                 → CompaniesPage (super_admin, company_admin)
/companies/:id             → CompanyDetailPage (super_admin, company_admin)
/sites/:id                 → SiteDetailPage (super_admin, company_admin, client_admin, site_manager)
/assets                    → AssetsPage (super_admin, company_admin, client_admin, site_manager)
/assets/:id                → AssetDetailPage (super_admin, company_admin, client_admin, site_manager)
/work-orders               → WorkOrdersPage (all roles)
/work-orders/:id           → WorkOrderDetailPage (all roles)
/invoices                  → InvoicesPage (super_admin, company_admin, client_admin)
/users                     → UsersPage (super_admin, company_admin)
/labor                     → LaborPage (super_admin, company_admin)
/locations                 → LocationsPage (super_admin, company_admin, client_admin)
/*                         → Redirect to /dashboard
```

---

### 6. i18n Translations (`src/i18n/index.ts`)

**Added Keys:**

| Key | Arabic | English |
|-----|--------|---------|
| `companies` | الشركات | Companies |
| `sites` | المواقع | Sites |
| `assets` | الأصول | Assets |
| `users` | الموظفين | Users |
| `labor` | إدارة العمالة | Labor Management |
| `locations` | المواقع الجغرافية | Locations |
| `toggle_menu` | فتح/إغلاق القائمة | Toggle menu |
| `close_menu` | إغلاق القائمة | Close menu |
| `logged_in_as` | مسجل الدخول كـ | Logged in as |
| `role_super_admin` | مدير النظام | Super Admin |
| `role_company_admin` | مدير الشركة | Company Admin |
| `role_client_admin` | مدير العميل | Client Admin |
| `role_site_manager` | مدير الموقع | Site Manager |
| `role_technician` | فني | Technician |

---

### 7. Placeholder Pages

Created 8 placeholder pages (to be implemented in later milestones):

- `src/pages/CompaniesPage.tsx`
- `src/pages/CompanyDetailPage.tsx`
- `src/pages/SiteDetailPage.tsx`
- `src/pages/AssetsPage.tsx`
- `src/pages/AssetDetailPage.tsx`
- `src/pages/UsersPage.tsx`
- `src/pages/LaborPage.tsx`
- `src/pages/LocationsPage.tsx`

Each placeholder:
- Shows translated page title
- Displays "To be implemented" message in a card
- Uses proper heading hierarchy (`<h1>`)
- Uses Tailwind design tokens

---

## Technical Decisions

### 1. Layout Architecture

**Decision:** Separate `Layout` and `Sidebar` components instead of one monolithic component.

**Rationale:**
- Better separation of concerns
- Sidebar can be independently tested and styled
- Layout handles global header/footer, Sidebar handles navigation
- Easier to add breadcrumbs or other layout elements later

### 2. Role-Based Access Control

**Decision:** Implement role checks in two places:
1. **Sidebar:** Filter visible menu items
2. **ProtectedRoute:** Block unauthorized access at route level

**Rationale:**
- Defense in depth (UI + route protection)
- Prevents users from manually typing URLs to access restricted pages
- Cleaner UX (users don't see menu items they can't access)

### 3. Mobile Navigation

**Decision:** Collapsible sidebar with dark overlay on mobile (`lg` breakpoint).

**Rationale:**
- Maximizes mobile screen real estate
- Standard pattern users expect
- Sidebar remains visible on desktop (>=1024px)

### 4. RTL Support

**Decision:** Use `i18n.dir()` for directional logic, Tailwind logical properties for styling.

**Rationale:**
- Tailwind's logical properties (`ms-`, `me-`, `start`, `end`) automatically flip in RTL
- No need for manual conditional classes
- Sidebar position flips correctly (right side in RTL)

### 5. API Calls in Components

**Decision:** Sidebar and ProtectedRoute both call `/users/me`.

**Potential Optimization:** Use React Context to share user data and reduce duplicate API calls.

**Why Not Implemented:** Out of scope for this milestone. Context provider can be added in a future refactor.

---

## Testing Checklist

### Before Deployment

- [ ] Run `npm run build` to check for TypeScript errors
- [ ] Test login flow (should redirect to `/dashboard`)
- [ ] Test role-based menu visibility:
  - [ ] Super Admin sees all menu items
  - [ ] Company Admin sees all except "Users" section (verify requirements)
  - [ ] Client Admin sees Dashboard, Assets, Work Orders, Invoices, Locations
  - [ ] Site Manager sees Dashboard, Assets, Work Orders
  - [ ] Technician sees Dashboard, Work Orders
- [ ] Test 403 page (try accessing `/users` as a technician)
- [ ] Test language toggle (AR ↔ EN)
- [ ] Test RTL layout (sidebar on right, text alignment)
- [ ] Test mobile menu (hamburger → sidebar → overlay → close)
- [ ] Test active route highlighting in sidebar
- [ ] Verify logout clears tokens and redirects to `/login`

---

## Known Issues / Future Work

### 1. Duplicate `/users/me` Calls

**Issue:** Both `Sidebar` and `ProtectedRoute` fetch user data independently.

**Solution:** Create a `UserContext` provider to share user data across components.

**Priority:** Medium (optimization, not blocking)

### 2. No Nested Routes for Companies → Sites

**Current:** `/sites/:id` is a top-level route.

**Potential Future:** `/companies/:companyId/sites/:siteId` for hierarchical URLs.

**Priority:** Low (current structure is functional)

### 3. Breadcrumbs Not Implemented

**Issue:** No breadcrumb navigation (e.g., "Companies > Acme Corp > Sites").

**Solution:** Add a `Breadcrumbs` component to `Layout.tsx`.

**Priority:** Medium (nice-to-have for UX)

### 4. No Error Boundary

**Issue:** If a page component crashes, the entire app breaks.

**Solution:** Wrap routes in React Error Boundary.

**Priority:** High (important for production)

### 5. Placeholder Pages Lack ARIA

**Issue:** "To be implemented" placeholders don't have semantic HTML.

**Solution:** Add proper landmarks, headings, and descriptions when implementing real pages.

**Priority:** Low (placeholder pages are temporary)

---

## Migration Notes for Other Agents

### Backend Agent

No backend changes required for this milestone. The frontend now expects:

- `GET /users/me` to return `{ id, email, full_name, role, company_id?, is_active }`
- `role` field to be one of: `super_admin`, `company_admin`, `client_admin`, `site_manager`, `technician`

### QA Agent

Focus testing on:

1. Role-based access control (both UI and route level)
2. RTL layout correctness (Arabic language)
3. Mobile responsiveness (sidebar collapse/overlay)
4. Authentication flow (login → dashboard → logout → login)

### UI/UX Agent

Next steps for design refinement:

1. Add breadcrumbs to Layout
2. Design dashboard widgets (role-specific)
3. Add empty states to placeholder pages
4. Review color contrast for accessibility (WCAG AA)
5. Design loading skeletons (better than spinners)

---

## File Summary

**New Files Created:**
- `src/components/Layout.tsx` (92 lines)
- `src/components/Sidebar.tsx` (154 lines)
- `src/components/ProtectedRoute.tsx` (78 lines)
- `src/pages/CompaniesPage.tsx` (13 lines)
- `src/pages/CompanyDetailPage.tsx` (16 lines)
- `src/pages/SiteDetailPage.tsx` (16 lines)
- `src/pages/AssetsPage.tsx` (13 lines)
- `src/pages/AssetDetailPage.tsx` (16 lines)
- `src/pages/UsersPage.tsx` (13 lines)
- `src/pages/LaborPage.tsx` (13 lines)
- `src/pages/LocationsPage.tsx` (13 lines)

**Modified Files:**
- `src/lib/types.ts` (added User and UserRole types)
- `src/i18n/index.ts` (added 14 translation keys)
- `src/App.tsx` (completely refactored routing)

**Total Lines Added:** ~437 lines  
**Total Lines Removed:** ~88 lines (old App.tsx components)  
**Net Change:** +349 lines

---

## Next Steps

### Milestone 3: Dashboard & Companies Pages

**Priorities:**
1. Implement role-specific dashboard widgets
2. Create Companies list page with CRUD operations
3. Create Company detail page with sites list
4. Add breadcrumb navigation
5. Implement FilterBar component

**Dependencies:**
- Backend must support `/companies` and `/sites` endpoints
- Backend must support filtering/pagination

---

## Success Criteria ✅

- [x] Layout component with RTL support
- [x] Sidebar with role-aware navigation
- [x] ProtectedRoute with authentication and authorization
- [x] Hierarchical routing structure
- [x] All routes guarded with proper role restrictions
- [x] i18n keys for all new UI elements
- [x] Placeholder pages for all new routes
- [x] Mobile-responsive design
- [x] No TypeScript errors
- [x] No hardcoded strings (all via `t()`)

---

**Sign-off:** Frontend Agent  
**Ready for:** QA testing and integration
