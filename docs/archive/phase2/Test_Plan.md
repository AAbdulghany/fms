# Phase 2 Comprehensive Test Plan

**Date:** April 17, 2026  
**QA Agent:** Senior QA Engineer  
**Phase:** Phase 2 - Screen Fixes + Feature Expansion  
**Version:** 1.0

---

## Executive Summary

This document defines the comprehensive test strategy for FMS Phase 2, covering security (RBAC, tenant isolation), functional testing (asset lifecycle, work orders, filters), integration testing, performance testing, and localization.

**Test Pyramid:**
- Unit Tests: 60% (pytest for backend, Vitest for frontend)
- Integration Tests: 30% (API + DB, Frontend + API mocks)
- E2E Tests: 10% (Playwright critical paths)

**Priority Levels:**
- **CRITICAL**: RBAC, Tenant Isolation, Asset Lifecycle Automation
- **HIGH**: Navigation Flows, Work Order Lifecycle, Filters
- **MEDIUM**: Labor Management, Location Management, Dashboards, i18n

---

## 1. Security Testing (CRITICAL)

### 1.1 RBAC Matrix Testing

Test **every endpoint** with **all 6 roles** to verify correct access control.

#### Roles:
1. `super_admin` - Full access to everything
2. `company_admin` - Everything except creating employees
3. `client_admin` - Client-scoped access
4. `site_manager` - Site-scoped access
5. `technician` - View only assigned work orders
6. `manager` - Limited management access

#### RBAC Test Matrix

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| **Users/Employees** |
| GET /users | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| POST /users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| PATCH /users/{id} | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| DELETE /users/{id} | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Clients/Companies** |
| GET /clients | ✅ | ✅ | ✅(own) | ❌ | ❌ | ✅(own) |
| POST /clients | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| PATCH /clients/{id} | ✅ | ✅ | ✅(own) | ❌ | ❌ | ❌ |
| **Sites** |
| GET /sites | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| POST /sites | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| PATCH /sites/{id} | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| **Assets** |
| GET /assets | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| POST /assets | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| PATCH /assets/{id} | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| GET /assets/{id}/lifecycle | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| POST /assets/{id}/reset-lifecycle | ✅ | ✅ | ✅(own) | ❌ | ❌ | ❌ |
| **Work Orders** |
| GET /work-orders | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| POST /work-orders | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| PATCH /work-orders/{id} | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| POST /work-orders/{id}/status | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| **Reports** |
| GET /reports | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| POST /reports | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| POST /reports/{id}/submit | ✅ | ✅ | ✅(own) | ✅(own) | ✅(assigned) | ✅(own) |
| POST /reports/{id}/approve | ✅ | ✅ | ✅(own) | ✅(own) | ❌ | ✅(own) |
| **Invoices** |
| GET /invoices | ✅ | ✅ | ✅(own) | ❌ | ❌ | ✅(own) |
| POST /invoices | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| POST /invoices/{id}/approve | ✅ | ✅ | ✅(own) | ❌ | ❌ | ❌ |
| **Billing Actions** |
| GET /billing-actions | ✅ | ✅ | ✅(own) | ❌ | ❌ | ✅(own) |
| POST /billing-actions/{id}/approve | ✅ | ✅ | ✅(own) | ❌ | ❌ | ❌ |

#### Test Cases per Endpoint

For each endpoint in the matrix:

**TC-RBAC-{endpoint}-{role}**: Test {endpoint} with {role} credentials
- **Given**: User logged in with {role}
- **When**: Request {endpoint} with valid data
- **Then**: 
  - If ✅: Returns 200/201 with correct data
  - If ❌: Returns 403 Forbidden
  - If ✅(own): Returns 200 only for user's tenant/client/site data
  - If ✅(assigned): Returns 200 only for assigned work orders

**Example Test Implementation:**

```python
# backend/tests/test_rbac.py

def test_get_users_super_admin(db_session, super_admin_token):
    """TC-RBAC-GET-users-super_admin"""
    response = client.get("/users", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert response.status_code == 200

def test_get_users_technician(db_session, technician_token):
    """TC-RBAC-GET-users-technician"""
    response = client.get("/users", headers={"Authorization": f"Bearer {technician_token}"})
    assert response.status_code == 403
```

### 1.2 Tenant Isolation Testing

**CRITICAL**: Verify users cannot access data from other tenants.

#### Test Scenarios:

**TS-TENANT-001: Cross-Tenant Data Access Attempt**
- **Given**: Two tenants (Tenant A, Tenant B) with data
- **When**: User from Tenant A requests Tenant B's resource by UUID
- **Then**: Returns 404 Not Found (not 403, to avoid UUID guessing)

**TS-TENANT-002: List Endpoints Respect Tenant**
- **Given**: Tenant A has 5 work orders, Tenant B has 3 work orders
- **When**: User from Tenant A requests GET /work-orders
- **Then**: Returns only 5 work orders (Tenant A's)

**TS-TENANT-003: Filter Bypassing Attempt**
- **Given**: User from Tenant A
- **When**: User filters by Tenant B's client_id
- **Then**: Returns empty list (not 403)

**TS-TENANT-004: Nested Resource Access**
- **Given**: Tenant A has Asset X with WO Y, Tenant B has Asset Z
- **When**: Tenant B user requests GET /assets/{X}/work-orders
- **Then**: Returns 404 Not Found

**TS-TENANT-005: Create with Foreign Tenant IDs**
- **Given**: Tenant A user
- **When**: POST /work-orders with Tenant B's site_id
- **Then**: Returns 400 Bad Request or 404 (site not found)

#### Test Implementation:

```python
# backend/tests/test_tenancy.py

def test_cross_tenant_work_order_access(db_session):
    """TS-TENANT-001"""
    tenant_a = create_tenant("Tenant A")
    tenant_b = create_tenant("Tenant B")
    
    wo_a = create_work_order(tenant_a.id)
    user_b = create_user(tenant_b.id, role="company_admin")
    
    token_b = login(user_b)
    response = client.get(f"/work-orders/{wo_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    
    assert response.status_code == 404  # Not 403, to avoid UUID enumeration

def test_list_work_orders_tenant_isolation(db_session):
    """TS-TENANT-002"""
    tenant_a = create_tenant("Tenant A")
    tenant_b = create_tenant("Tenant B")
    
    create_work_orders(tenant_a.id, count=5)
    create_work_orders(tenant_b.id, count=3)
    
    user_a = create_user(tenant_a.id, role="company_admin")
    token_a = login(user_a)
    
    response = client.get("/work-orders", headers={"Authorization": f"Bearer {token_a}"})
    
    assert response.status_code == 200
    assert len(response.json()) == 5
```

### 1.3 UUID Guessing Attack Prevention

**Goal**: Prevent attackers from enumerating resources by guessing UUIDs.

#### Test Scenarios:

**TS-UUID-001: Invalid UUID Returns 404**
- **When**: Request resource with random valid UUID
- **Then**: Returns 404 Not Found (not 403)

**TS-UUID-002: Cross-Tenant UUID Returns 404**
- **When**: Request resource UUID from another tenant
- **Then**: Returns 404 Not Found (not 403, to avoid confirming UUID exists)

**TS-UUID-003: Unauthorized Resource Returns 404**
- **When**: Technician requests work order not assigned to them
- **Then**: Returns 404 Not Found (not 403)

### 1.4 SQL Injection Testing

**Goal**: Verify all query parameters are properly sanitized.

#### Test Scenarios:

**TS-SQL-001: Search Parameter SQL Injection**
- **When**: GET /work-orders?search='; DROP TABLE users; --
- **Then**: Returns empty list or filtered results, no SQL error

**TS-SQL-002: Filter Parameter Injection**
- **When**: GET /work-orders?status=' OR '1'='1
- **Then**: Returns 400 Bad Request (invalid enum value)

**TS-SQL-003: UUID Parameter Injection**
- **When**: GET /work-orders/{id}' OR '1'='1
- **Then**: Returns 400 Bad Request (invalid UUID format)

### 1.5 XSS Prevention Testing

**Goal**: Verify user input is sanitized before rendering.

#### Test Scenarios:

**TS-XSS-001: Work Order Title Script Injection**
- **Given**: Create work order with title `<script>alert('XSS')</script>`
- **When**: View work order in frontend
- **Then**: Title is rendered as plain text, script does not execute

**TS-XSS-002: Report Description HTML Injection**
- **Given**: Submit report with description `<img src=x onerror=alert('XSS')>`
- **When**: View report
- **Then**: HTML is escaped, no script execution

**TS-XSS-003: Asset Name Injection**
- **Given**: Create asset with name `<a href="javascript:alert('XSS')">Click</a>`
- **When**: View asset list
- **Then**: Name is rendered as plain text

---

## 2. Functional Testing

### 2.1 Asset Lifecycle Management (P2-F2)

**Feature**: Automatic tracking of asset repair count and age, auto-creating replacement work orders.

#### Test Scenarios:

**TS-LIFECYCLE-001: Repair Count Triggers Replacement**
- **Given**: Asset with max_repair_count=3, current_repair_count=2
- **When**: Complete a work order for this asset
- **Then**: 
  - current_repair_count increments to 3
  - lifecycle_status changes to 'end_of_life'
  - Replacement work order is auto-created with category='replacement'

**TS-LIFECYCLE-002: Age Triggers End of Life**
- **Given**: Asset installed 6 years ago with max_age_years=5
- **When**: Call check_lifecycle() or view asset
- **Then**: 
  - lifecycle_status changes to 'end_of_life'
  - Replacement work order is auto-created

**TS-LIFECYCLE-003: Warning at 80% of Repair Limit**
- **Given**: Asset with max_repair_count=5, current_repair_count=4 (80%)
- **When**: Check lifecycle
- **Then**: lifecycle_status changes to 'warning'

**TS-LIFECYCLE-004: Warning at 80% of Age Limit**
- **Given**: Asset installed 4 years ago with max_age_years=5 (80%)
- **When**: Check lifecycle
- **Then**: lifecycle_status changes to 'warning'

**TS-LIFECYCLE-005: No Double Replacement WO**
- **Given**: Asset at end_of_life with existing replacement WO
- **When**: Trigger replacement again
- **Then**: No new work order created, returns existing one

**TS-LIFECYCLE-006: Replacement WO Not Counted**
- **Given**: Asset with replacement work order
- **When**: Complete the replacement work order
- **Then**: current_repair_count does not increment (skip category='replacement')

**TS-LIFECYCLE-007: Reset Lifecycle**
- **Given**: Asset with lifecycle_status='end_of_life'
- **When**: POST /assets/{id}/reset-lifecycle
- **Then**: 
  - lifecycle_status changes to 'replaced'
  - current_repair_count resets to 0

**TS-LIFECYCLE-008: No Limits Set**
- **Given**: Asset with max_repair_count=null, max_age_years=null
- **When**: Complete work order
- **Then**: lifecycle_status remains 'active', no replacement WO created

**TS-LIFECYCLE-009: Lifecycle Timeline API**
- **Given**: Asset with repair/age data
- **When**: GET /assets/{id}/lifecycle
- **Then**: Returns timeline with current/max values, percentages, warnings

**TS-LIFECYCLE-010: Edge Case - Same Day Age Limit**
- **Given**: Asset installed exactly 5 years ago with max_age_years=5
- **When**: Check lifecycle
- **Then**: lifecycle_status changes to 'end_of_life'

#### Implementation Status:
- ✅ Backend service: `backend/app/services/asset_lifecycle.py`
- ✅ Basic tests: `backend/tests/test_asset_lifecycle.py` (3 tests exist)
- ❌ Missing: Edge case tests (TS-LIFECYCLE-005 through TS-LIFECYCLE-010)
- ❌ Missing: API endpoint tests

### 2.2 Work Order Lifecycle Testing

**Feature**: Status transitions, assignment, completion workflow.

#### Test Scenarios:

**TS-WO-001: Create Work Order**
- **Given**: Super admin or company admin
- **When**: POST /work-orders with valid data
- **Then**: Work order created with status='created'

**TS-WO-002: Assign Work Order**
- **Given**: Work order with status='created'
- **When**: PATCH /work-orders/{id} with assignee_user_id
- **Then**: status changes to 'assigned'

**TS-WO-003: Start Work Order**
- **Given**: Assigned work order
- **When**: Technician updates status to 'in_progress'
- **Then**: status changes to 'in_progress'

**TS-WO-004: Complete Work Order**
- **Given**: Work order in progress
- **When**: Technician updates status to 'completed'
- **Then**: 
  - status changes to 'completed'
  - If asset has limits, check_lifecycle() is triggered

**TS-WO-005: Invalid Status Transition**
- **Given**: Work order with status='created'
- **When**: Technician tries to update status to 'completed' (skip 'assigned')
- **Then**: Returns 400 Bad Request (invalid transition)

**TS-WO-006: Auto-Assignment from Context**
- **Given**: Super admin viewing Site X
- **When**: Create work order in Site X context
- **Then**: client_id and site_id are auto-populated from Site X

### 2.3 Filter Functionality Testing (P2-F1)

**Feature**: Filter work orders, invoices, assets by various criteria.

#### Test Scenarios:

**TS-FILTER-001: Status Filter**
- **Given**: 5 work orders (2 created, 3 completed)
- **When**: GET /work-orders?status=completed
- **Then**: Returns only 3 completed work orders

**TS-FILTER-002: Date Range Filter**
- **Given**: Work orders from Jan, Feb, Mar
- **When**: GET /work-orders?date_from=2026-02-01&date_to=2026-02-28
- **Then**: Returns only February work orders

**TS-FILTER-003: Multiple Filters Combined**
- **When**: GET /work-orders?status=in_progress&urgency=urgent&site_id={site_id}
- **Then**: Returns work orders matching all conditions

**TS-FILTER-004: Search Filter (Case Insensitive)**
- **Given**: Work orders with titles "AC Repair", "ac maintenance", "Plumbing"
- **When**: GET /work-orders?search=AC
- **Then**: Returns 2 work orders (case-insensitive match)

**TS-FILTER-005: Empty Filter Results**
- **When**: GET /work-orders?status=cancelled
- **Then**: Returns empty list [] (not error)

**TS-FILTER-006: Filter Respects Tenant Isolation**
- **Given**: Tenant A has work orders matching filter
- **When**: Tenant B user applies same filter
- **Then**: Returns empty list (Tenant B has no matching WOs)

**TS-FILTER-007: Filter Respects Role (Technician)**
- **Given**: Technician assigned to WO-1, WO-2 exists but not assigned
- **When**: Technician requests GET /work-orders (any filter)
- **Then**: Returns only WO-1 (assigned work orders)

**TS-FILTER-008: Invalid Filter Parameter**
- **When**: GET /work-orders?status=invalid_status
- **Then**: Returns 400 Bad Request

#### Implementation Status:
- ✅ Backend: Filter parameters added to work_orders.py, invoices.py, assets.py
- ✅ Frontend: FilterBar.tsx component created
- ✅ Integration: WorkOrdersPage.tsx uses FilterBar
- ❌ Missing: Tests for all filter scenarios

### 2.4 Maintenance Tagging (P2-F3)

**Feature**: Tag work orders as preventive, corrective, or protective.

#### Test Scenarios:

**TS-TAG-001: Create Work Order with Tags**
- **When**: POST /work-orders with tags=['preventive', 'corrective']
- **Then**: Work order created with tags

**TS-TAG-002: Filter by Tag**
- **When**: GET /work-orders?tags=preventive
- **Then**: Returns only work orders with 'preventive' tag

**TS-TAG-003: Invalid Tag Validation**
- **When**: POST /work-orders with tags=['invalid_tag']
- **Then**: Returns 400 Bad Request

**TS-TAG-004: Update Tags**
- **When**: PATCH /work-orders/{id} with tags=['protective']
- **Then**: Tags updated successfully

**TS-TAG-005: Tag Display in UI**
- **When**: View work order list
- **Then**: Tags displayed as badges with correct colors

#### Implementation Status:
- ❌ Not yet implemented (scheduled after P2-F2)

### 2.5 Report Approval Workflow

**Feature**: Technician submits report, manager approves.

#### Test Scenarios:

**TS-REPORT-001: Create Draft Report**
- **Given**: Technician assigned to work order
- **When**: POST /reports with status='draft'
- **Then**: Report created, work order report_id updated

**TS-REPORT-002: Submit Report**
- **Given**: Draft report
- **When**: POST /reports/{id}/submit
- **Then**: status changes to 'submitted'

**TS-REPORT-003: Approve Report**
- **Given**: Submitted report
- **When**: Manager calls POST /reports/{id}/approve
- **Then**: status changes to 'approved'

**TS-REPORT-004: Reject Report**
- **Given**: Submitted report
- **When**: Manager calls POST /reports/{id}/reject with reason
- **Then**: status changes to 'rejected', reason stored

**TS-REPORT-005: Technician Cannot Approve Own Report**
- **Given**: Technician submits report
- **When**: Same technician calls POST /reports/{id}/approve
- **Then**: Returns 403 Forbidden

### 2.6 Invoice Generation

**Feature**: Generate invoice from approved report or billing actions.

#### Test Scenarios:

**TS-INVOICE-001: Generate from Approved Report**
- **Given**: Work order with approved report
- **When**: POST /invoices with work_order_id
- **Then**: Invoice created with line items from report answers

**TS-INVOICE-002: Invoice Status Workflow**
- **Given**: Draft invoice
- **When**: POST /invoices/{id}/approve
- **Then**: status changes to 'approved'

**TS-INVOICE-003: Filter Invoices**
- **When**: GET /invoices?status=paid&client_id={client_id}
- **Then**: Returns filtered invoices

---

## 3. Integration Testing

### 3.1 End-to-End Work Order Lifecycle

**Test Flow**: Create asset → complete repairs → trigger replacement → complete replacement

**TS-E2E-WO-001: Full Asset Lifecycle with Replacement**
1. **Setup**: Create tenant, client, site, asset with max_repair_count=2
2. **Step 1**: Create work order WO-1 for asset
3. **Step 2**: Assign WO-1 to technician
4. **Step 3**: Technician completes WO-1 (repair count = 1)
5. **Step 4**: Create work order WO-2 for same asset
6. **Step 5**: Complete WO-2 (repair count = 2, status = end_of_life)
7. **Verify**: Replacement work order WO-3 auto-created
8. **Step 6**: Complete WO-3
9. **Verify**: Repair count not incremented (WO-3 is replacement)
10. **Step 7**: Reset lifecycle
11. **Verify**: Asset status = 'replaced', repair count = 0

**Expected Assertions:**
- After step 3: asset.current_repair_count == 1
- After step 5: asset.current_repair_count == 2, asset.lifecycle_status == 'end_of_life'
- After step 5: WO-3 exists with category='replacement'
- After step 8: asset.current_repair_count == 2 (no increment)
- After step 10: asset.lifecycle_status == 'replaced', asset.current_repair_count == 0

### 3.2 Asset Replacement Work Order Auto-Creation

**TS-E2E-ASSET-001: Repair Count Triggers Replacement**
- See TS-LIFECYCLE-001 + verify replacement WO has correct fields

**TS-E2E-ASSET-002: Age Triggers Replacement**
- See TS-LIFECYCLE-002 + verify replacement WO references age limit

### 3.3 Multi-Tenant Data Isolation

**TS-E2E-TENANT-001: Two Tenants Cannot See Each Other's Data**
1. Create Tenant A with 3 work orders
2. Create Tenant B with 2 work orders
3. User A requests GET /work-orders → returns 3
4. User B requests GET /work-orders → returns 2
5. User A requests GET /work-orders/{tenant_b_wo_id} → returns 404

### 3.4 Role-Based Navigation Flows

**TS-E2E-NAV-001: Super Admin Navigation**
1. Login as super_admin
2. Navigate to Welcome Page → sees current tasks + stats
3. Click "Companies" → sees ClientsPage with company list
4. Click company → sees SitesPage for that company
5. Click site → sees WorkOrdersPage filtered by site
6. Click work order → sees WorkOrderDetailPage
7. Verify breadcrumbs: Companies > Company X > Sites > Site Y > Work Orders > WO-123

**TS-E2E-NAV-002: Technician Navigation**
1. Login as technician
2. Navigate to Welcome Page → sees assigned work orders
3. Sidebar shows only "My Work Orders"
4. Click work order → sees WorkOrderDetailPage
5. Can update status, create report
6. Cannot see Companies, Sites, Invoices

**TS-E2E-NAV-003: Client Manager Navigation**
1. Login as client_admin
2. Navigate to Welcome Page → sees company dashboard
3. Sidebar shows: Sites, Work Orders, Billing, Assets
4. Can see only their company's sites
5. Can create work orders within their sites
6. Can approve billing actions

**TS-E2E-NAV-004: Site Manager Navigation**
1. Login as site_manager
2. Navigate to Welcome Page → sees site dashboard
3. Sidebar shows: Work Orders, Assets (scoped to their site)
4. Cannot see other sites
5. Can create work orders, manage assets within their site

---

## 4. Performance Testing

### 4.1 List Endpoints with Large Datasets

**Goal**: Ensure list endpoints perform well with 1000+ records.

**TS-PERF-001: Work Orders List with 1000 Records**
- **Given**: 1000 work orders in database
- **When**: GET /work-orders
- **Then**: Response time < 2 seconds

**TS-PERF-002: Filter Query Performance**
- **Given**: 1000 work orders
- **When**: GET /work-orders?status=in_progress&urgency=urgent&date_from=2026-01-01
- **Then**: Response time < 2 seconds

**TS-PERF-003: Assets List with 500 Assets**
- **Given**: 500 assets across 10 sites
- **When**: GET /assets?site_id={site_id}
- **Then**: Response time < 1 second

**TS-PERF-004: Pagination Performance**
- **Given**: 1000 work orders
- **When**: GET /work-orders?skip=0&limit=50
- **Then**: Response time < 500ms

### 4.2 Concurrent User Sessions

**Goal**: Verify system handles multiple users simultaneously.

**TS-PERF-005: 10 Concurrent Users Creating Work Orders**
- **Given**: 10 users logged in
- **When**: All create work order simultaneously
- **Then**: All requests succeed, no race conditions

**TS-PERF-006: Concurrent Asset Lifecycle Checks**
- **Given**: 5 users completing work orders on same asset
- **When**: All complete work orders at same time
- **Then**: Repair count increments correctly, no double replacement WO

### 4.3 Database Query Optimization

**TS-PERF-007: N+1 Query Prevention**
- **When**: GET /work-orders (list with 100 records)
- **Then**: Uses eager loading, max 5 queries (not 100+)

**TS-PERF-008: Tenant Filter Performance**
- **Given**: 10,000 work orders across 10 tenants
- **When**: GET /work-orders (1000 per tenant)
- **Then**: Query uses tenant_id index, response < 2 seconds

---

## 5. Localization (L10n/i18n) Testing

### 5.1 Arabic (RTL) Rendering

**Goal**: Verify all pages render correctly in Arabic with right-to-left layout.

**TS-I18N-001: Work Orders Page RTL**
- **Given**: User locale is 'ar'
- **When**: Navigate to WorkOrdersPage
- **Then**: 
  - Page layout is RTL (sidebar on right)
  - Text aligned right
  - Date formatting uses Arabic numerals

**TS-I18N-002: Forms RTL**
- **Given**: Locale is 'ar'
- **When**: Open Create Work Order form
- **Then**: 
  - Labels aligned right
  - Input fields RTL
  - Buttons positioned correctly

**TS-I18N-003: No Hardcoded Strings**
- **When**: Search codebase for hardcoded English text
- **Then**: All UI text uses t() function

### 5.2 English (LTR) Rendering

**TS-I18N-004: Work Orders Page LTR**
- **Given**: User locale is 'en'
- **When**: Navigate to WorkOrdersPage
- **Then**: Page layout is LTR (sidebar on left)

### 5.3 Date/Time Formatting

**TS-I18N-005: Date Format Per Locale**
- **Given**: Work order opened_at = 2026-04-17
- **When**: View in Arabic locale
- **Then**: Displayed as "١٧ أبريل ٢٠٢٦"
- **When**: View in English locale
- **Then**: Displayed as "April 17, 2026"

### 5.4 Number Formatting

**TS-I18N-006: Currency Formatting**
- **Given**: Invoice amount = 1500.50 SAR
- **When**: View in Arabic locale
- **Then**: Displayed as "١٬٥٠٠٫٥٠ ر.س"
- **When**: View in English locale
- **Then**: Displayed as "SAR 1,500.50"

---

## 6. Test Coverage Gaps (Current State)

### 6.1 Existing Tests Analysis

**File**: `backend/tests/test_asset_lifecycle.py`

**Tests Implemented (3 tests):**
1. ✅ `test_lifecycle_repair_count_triggers_replacement` - Basic repair count test
2. ✅ `test_lifecycle_age_triggers_end_of_life` - Basic age test
3. ✅ `test_lifecycle_warning_at_80_percent` - Warning status test
4. ✅ `test_get_lifecycle_timeline` - Timeline API test

**Missing Tests:**
- ❌ No double replacement WO test
- ❌ Replacement WO not counted in repair count
- ❌ Reset lifecycle test
- ❌ Edge cases (no limits set, null values)
- ❌ API endpoint tests (GET /assets/{id}/lifecycle)
- ❌ Integration test with work order completion

**File**: `backend/conftest.py`

**Fixtures Implemented:**
- ✅ `db_session` - In-memory SQLite database
- ✅ `sample_tenant` - Test tenant
- ✅ `sample_client` - Test client
- ✅ `sample_site` - Test site
- ✅ `sample_user` - Test user with super_admin role

**Missing Fixtures:**
- ❌ Users with different roles (company_admin, technician, client_admin, site_manager, manager)
- ❌ Authentication tokens per role
- ❌ Multiple tenants for isolation tests
- ❌ Work orders, assets, reports fixtures

### 6.2 Coverage Gaps by Feature

| Feature | Unit Tests | Integration Tests | E2E Tests | Coverage % |
|---------|-----------|-------------------|-----------|------------|
| Asset Lifecycle | 30% | 0% | 0% | 30% |
| Work Orders | 0% | 0% | 0% | 0% |
| Filters | 0% | 0% | 0% | 0% |
| RBAC | 0% | 0% | 0% | 0% |
| Tenant Isolation | 0% | 0% | 0% | 0% |
| Reports | 0% | 0% | 0% | 0% |
| Invoices | 0% | 0% | 0% | 0% |
| User Management | 0% | 0% | 0% | 0% |
| **Overall** | **5%** | **0%** | **0%** | **5%** |

### 6.3 Priority Test Creation Order

1. **CRITICAL - Week 1**:
   - RBAC matrix tests (30 test cases)
   - Tenant isolation tests (10 test cases)
   - Asset lifecycle edge cases (10 test cases)

2. **HIGH - Week 2**:
   - Work order lifecycle tests (15 test cases)
   - Filter functionality tests (15 test cases)
   - Report approval workflow (10 test cases)

3. **MEDIUM - Week 3**:
   - Navigation flow E2E tests (8 test cases)
   - Invoice generation tests (10 test cases)
   - Performance tests (5 test cases)

4. **LOW - Week 4**:
   - i18n/RTL tests (10 test cases)
   - User management tests (10 test cases)
   - Edge case tests (10 test cases)

---

## 7. Test Environments

### 7.1 Unit Test Environment

**Backend:**
- In-memory SQLite database
- Pytest fixtures
- No external dependencies

**Frontend:**
- Vitest with React Testing Library
- Mock API responses
- JSDOM environment

### 7.2 Integration Test Environment

**Backend:**
- PostgreSQL test database (Docker container)
- Alembic migrations applied
- Test data seeded

**Frontend:**
- Mock API server (MSW - Mock Service Worker)
- React Testing Library with API calls

### 7.3 E2E Test Environment

**Setup:**
- Full backend server running (uvicorn)
- Frontend dev server (Vite)
- Playwright browser automation
- PostgreSQL test database

**Browser Matrix:**
- Chromium (primary)
- Firefox (RTL verification)
- WebKit (Safari compatibility)

---

## 8. CI/CD Pipeline Integration

### 8.1 GitHub Actions Workflow

```yaml
name: FMS Phase 2 Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run pytest
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm ci
      - name: Run Vitest
        run: npm run test:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  e2e-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run migrations
        run: |
          cd backend
          alembic upgrade head
      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
      - name: Install frontend dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run Playwright tests
        run: npx playwright test
```

### 8.2 Coverage Requirements

**Minimum Coverage Thresholds:**
- Backend: 80%
- Frontend: 70%
- E2E: Critical paths only

**Coverage Reports:**
- Codecov integration
- PR comments with coverage diff
- Block merge if coverage drops > 5%

---

## 9. Test Execution Schedule

### 9.1 Development Phase

**Daily:**
- Run unit tests on changed files
- Run linter (flake8, ESLint)

**Pre-Commit:**
- Run unit tests for changed modules
- Run TypeScript type check

**Pre-Push:**
- Run all unit tests
- Run integration tests

### 9.2 Feature Completion Phase

**After P2-F2 (Asset Lifecycle):**
- Run asset lifecycle test suite
- Run integration tests
- Manual smoke test

**After P2-F3 (Maintenance Tags):**
- Run tag test suite
- Run filter tests with tags

**After P2-F4, P2-F5, P2-F6:**
- Run feature-specific test suite
- Run regression tests

### 9.3 Phase 2 Completion

**Before Production:**
- Run full test suite (unit + integration + E2E)
- Run performance tests
- Run security tests (RBAC, tenant isolation)
- Manual exploratory testing (4 hours)
- UAT with stakeholders

---

## 10. Bug Tracking & Reporting

### 10.1 Bug Report Template

```markdown
## Bug Report

**ID**: BUG-{number}
**Severity**: Critical / High / Medium / Low
**Priority**: P0 / P1 / P2 / P3
**Found By**: {name}
**Date**: {date}
**Affected Feature**: {feature}

### Environment
- OS: 
- Browser: 
- User Role: 

### Steps to Reproduce
1. 
2. 
3. 

### Expected Behavior


### Actual Behavior


### Screenshots/Logs


### Related Test Case
TC-{test_id}
```

### 10.2 Severity Definitions

- **Critical**: System crash, data loss, security vulnerability
- **High**: Feature broken, major functionality unusable
- **Medium**: Feature works but with issues, workaround exists
- **Low**: Minor UI issue, typo, cosmetic

---

## 11. Appendix

### 11.1 Test Data Seeding Script

See: `backend/app/test_seed.py` (if exists)

### 11.2 Useful Commands

**Backend Tests:**
```bash
# Run all tests
cd backend && pytest

# Run specific test file
pytest tests/test_asset_lifecycle.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_asset_lifecycle.py::test_lifecycle_repair_count_triggers_replacement -v

# Run tests matching pattern
pytest -k "lifecycle" -v
```

**Frontend Tests:**
```bash
# Run all tests
npm run test

# Run with coverage
npm run test:coverage

# Run specific test file
npm run test -- WorkOrderDetailPage.test.tsx

# Watch mode
npm run test:watch
```

**Database Management:**
```bash
# Create migration
cd backend
export PYTHONPATH=.
alembic revision --autogenerate -m "Migration message"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 11.3 Key Metrics

**Test Execution Time:**
- Unit tests: < 30 seconds
- Integration tests: < 2 minutes
- E2E tests: < 10 minutes
- Full suite: < 15 minutes

**Success Criteria:**
- All tests pass
- Coverage > 80% backend, > 70% frontend
- No critical or high severity bugs
- All RBAC tests pass
- All tenant isolation tests pass

---

**End of Test Plan**
