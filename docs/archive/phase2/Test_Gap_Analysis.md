# Test Coverage Gap Analysis Report

**Date:** April 17, 2026  
**QA Agent:** Senior QA Engineer  
**Version:** 1.0

---

## Executive Summary

This report analyzes the current state of test coverage for FMS Phase 2 and identifies critical gaps that must be addressed before production deployment.

**Current Coverage:**
- Backend Unit Tests: **5%** (4 tests exist)
- Backend Integration Tests: **0%** (no tests exist)
- Frontend Unit Tests: **0%** (no tests exist)
- E2E Tests: **0%** (no tests exist)

**Target Coverage:**
- Backend Unit Tests: **80%**
- Backend Integration Tests: **30%**
- Frontend Unit Tests: **70%**
- E2E Tests: **10%** (critical paths)

**Gap:** 75-80% of required tests are missing.

---

## 1. Current Test Inventory

### 1.1 Existing Backend Tests

**File:** `backend/tests/test_asset_lifecycle.py`

| Test Name | Status | Coverage |
|-----------|--------|----------|
| `test_lifecycle_repair_count_triggers_replacement` | ✅ Passing | Repair count basic flow |
| `test_lifecycle_age_triggers_end_of_life` | ✅ Passing | Age limit basic flow |
| `test_lifecycle_warning_at_80_percent` | ✅ Passing | Warning status at 80% |
| `test_get_lifecycle_timeline` | ✅ Passing | Timeline API response |

**Total:** 4 tests

**Estimated Coverage:**
- `app/services/asset_lifecycle.py`: ~40%
- `app/models.py` (Asset model): ~20%
- `app/api/routes/assets.py`: ~0%

---

### 1.2 Existing Frontend Tests

**Status:** No test files found.

**Expected Files (Not Created):**
- `src/components/FilterBar.test.tsx`
- `src/components/AssetLifecycleBadge.test.tsx`
- `src/components/TagBadge.test.tsx`
- `src/pages/WorkOrdersPage.test.tsx`
- `src/pages/WorkOrderDetailPage.test.tsx`

---

### 1.3 Existing E2E Tests

**Status:** No E2E tests exist.

**Expected Directory:** `tests/e2e/` (not created)

---

### 1.4 Existing Fixtures

**File:** `backend/conftest.py`

**Fixtures Created:**
- ✅ `db_session` - In-memory SQLite database
- ✅ `sample_tenant` - Test tenant
- ✅ `sample_client` - Test client
- ✅ `sample_site` - Test site
- ✅ `sample_user` - Super admin user

**Missing Fixtures:**
- ❌ Users with different roles (company_admin, technician, client_admin, site_manager, manager)
- ❌ Authentication token fixtures per role
- ❌ Multiple tenants for isolation testing
- ❌ Work order fixtures
- ❌ Asset fixtures
- ❌ Report fixtures
- ❌ Invoice fixtures
- ❌ Labor entry fixtures
- ❌ Location fixtures

---

## 2. Gap Analysis by Feature

### 2.1 Asset Lifecycle Management (P2-F2)

**Implementation Status:** ✅ Complete (backend service exists)

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Unit Tests | 15 | 4 | 11 | CRITICAL |
| Integration Tests | 5 | 0 | 5 | HIGH |
| API Endpoint Tests | 5 | 0 | 5 | HIGH |
| E2E Tests | 2 | 0 | 2 | MEDIUM |
| **Total** | **27** | **4** | **23** | - |

**Missing Unit Tests:**
1. ❌ `test_no_double_replacement_wo` - Verify only one replacement WO created
2. ❌ `test_replacement_wo_not_counted` - Replacement WO doesn't increment repair count
3. ❌ `test_reset_lifecycle` - Reset lifecycle to 'replaced' status
4. ❌ `test_no_limits_set` - Asset with no limits stays active
5. ❌ `test_only_repair_limit` - Only repair count limit set
6. ❌ `test_only_age_limit` - Only age limit set
7. ❌ `test_multiple_completion_same_asset` - Multiple WOs on same asset
8. ❌ `test_lifecycle_check_interval` - Don't check on every request
9. ❌ `test_replacement_wo_fields` - Verify replacement WO has correct source, category
10. ❌ `test_edge_case_exact_limit` - Asset exactly at limit (not over)
11. ❌ `test_null_installed_on` - Asset with null installed_on date

**Missing Integration Tests:**
1. ❌ E2E: Create asset → complete repairs → verify replacement WO → complete replacement
2. ❌ Test with database transaction rollback
3. ❌ Test with concurrent work order completions
4. ❌ Test lifecycle check triggered from work order completion webhook
5. ❌ Test replacement WO appears in GET /work-orders list

**Missing API Tests:**
1. ❌ `GET /assets/{id}/lifecycle` returns correct timeline
2. ❌ `POST /assets/{id}/reset-lifecycle` resets status
3. ❌ `GET /assets?lifecycle_status=end_of_life` filters correctly
4. ❌ Lifecycle endpoints respect tenant isolation
5. ❌ Lifecycle endpoints respect RBAC

**Impact:** HIGH - Asset lifecycle is a core Phase 2 feature. Without comprehensive tests, auto-replacement logic could fail silently in production.

---

### 2.2 Work Order Management

**Implementation Status:** ✅ Complete (endpoints exist from MVP)

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Unit Tests | 20 | 0 | 20 | CRITICAL |
| Integration Tests | 10 | 0 | 10 | CRITICAL |
| API Endpoint Tests | 15 | 0 | 15 | CRITICAL |
| E2E Tests | 5 | 0 | 5 | HIGH |
| **Total** | **50** | **0** | **50** | - |

**Missing Critical Tests:**
1. ❌ RBAC: All 6 roles tested on work order endpoints
2. ❌ Tenant isolation: Cross-tenant work order access
3. ❌ Status transitions: Valid/invalid FSM transitions
4. ❌ Assignment: Auto-assignment from context
5. ❌ Filters: All 8 filter parameters tested
6. ❌ Technician scope: Only assigned WOs visible

**Impact:** CRITICAL - Work orders are the core entity. Without RBAC tests, unauthorized users could access/modify work orders.

---

### 2.3 Filter Functionality (P2-F1)

**Implementation Status:** ✅ Complete (backend filters added, FilterBar component created)

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 15 | 0 | 15 | HIGH |
| Frontend Unit Tests | 10 | 0 | 10 | HIGH |
| Integration Tests | 8 | 0 | 8 | MEDIUM |
| **Total** | **33** | **0** | **33** | - |

**Missing Backend Tests:**
1. ❌ Filter by status (single value)
2. ❌ Filter by urgency
3. ❌ Filter by date range (date_from, date_to)
4. ❌ Filter by client_id
5. ❌ Filter by site_id
6. ❌ Filter by assignee_user_id
7. ❌ Search filter (case-insensitive)
8. ❌ Multiple filters combined (AND logic)
9. ❌ Empty filter results
10. ❌ Invalid filter parameters
11. ❌ Filters respect tenant isolation
12. ❌ Filters respect role scope (technician)
13. ❌ Invoice filters (status, client_id, date range)
14. ❌ Asset filters (category, search)
15. ❌ Filter pagination interaction

**Missing Frontend Tests:**
1. ❌ FilterBar renders with correct options
2. ❌ FilterBar updates URL query params
3. ❌ FilterBar clears filters
4. ❌ FilterBar respects role visibility
5. ❌ WorkOrdersPage fetches with filter params
6. ❌ WorkOrdersPage reacts to URL param changes
7. ❌ FilterBar shows selected filter values
8. ❌ FilterBar date range picker works
9. ❌ FilterBar responsive layout on mobile
10. ❌ FilterBar loading state during fetch

**Impact:** MEDIUM - Filters work but lack validation. Users could experience unexpected behavior with edge cases.

---

### 2.4 Maintenance Tagging (P2-F3)

**Implementation Status:** ❌ Not Implemented (scheduled after P2-F2)

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 8 | 0 | 8 | MEDIUM |
| Frontend Unit Tests | 5 | 0 | 5 | MEDIUM |
| **Total** | **13** | **0** | **13** | - |

**Missing Tests:**
- All tests (feature not implemented yet)

**Impact:** LOW - Feature not yet implemented. Tests will be created during implementation.

---

### 2.5 Man Labor Management (P2-F4)

**Implementation Status:** ❌ Not Implemented

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 25 | 0 | 25 | HIGH |
| Frontend Unit Tests | 15 | 0 | 15 | MEDIUM |
| Integration Tests | 10 | 0 | 10 | HIGH |
| **Total** | **50** | **0** | **50** | - |

**Impact:** HIGH - Major feature with complex business logic (overtime calculation, performance metrics). Requires comprehensive test coverage.

---

### 2.6 Location Management (P2-F5)

**Implementation Status:** ❌ Not Implemented

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 20 | 0 | 20 | HIGH |
| Frontend Unit Tests | 12 | 0 | 12 | MEDIUM |
| Integration Tests | 8 | 0 | 8 | MEDIUM |
| **Total** | **40** | **0** | **40** | - |

**Impact:** HIGH - Hierarchical data structure with circular reference prevention. Requires thorough edge case testing.

---

### 2.7 Customized Dashboards (P2-F6)

**Implementation Status:** ❌ Not Implemented

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 15 | 0 | 15 | MEDIUM |
| Frontend Unit Tests | 25 | 0 | 25 | MEDIUM |
| Integration Tests | 10 | 0 | 10 | LOW |
| **Total** | **50** | **0** | **50** | - |

**Impact:** MEDIUM - Primarily UI feature. Backend logic is simple (data aggregation). Focus on data accuracy and role-based visibility.

---

### 2.8 User Management (P2-Fix)

**Implementation Status:** ✅ Complete (endpoints added in Fix Phase)

**Test Coverage:**

| Test Category | Required Tests | Existing Tests | Gap | Priority |
|---------------|---------------|----------------|-----|----------|
| Backend Unit Tests | 15 | 0 | 15 | CRITICAL |
| RBAC Tests | 10 | 0 | 10 | CRITICAL |
| **Total** | **25** | **0** | **25** | - |

**Missing Critical Tests:**
1. ❌ Only super_admin can GET /users
2. ❌ Only super_admin can POST /users
3. ❌ Super_admin can create company_admin, technician
4. ❌ Super_admin cannot create super_admin, client_admin
5. ❌ Email uniqueness within tenant
6. ❌ Tenant isolation on user list
7. ❌ User creation validates email format
8. ❌ User creation requires password
9. ❌ User update respects role restrictions
10. ❌ User deletion (soft delete)

**Impact:** CRITICAL - User management is a security-sensitive feature. Without RBAC tests, privilege escalation is possible.

---

## 3. Critical Security Gaps

### 3.1 RBAC Testing Gap

**Status:** 0 tests exist for RBAC enforcement.

**Required:** 180+ tests (30 endpoints × 6 roles = 180 test cases)

**Gap:** 180 tests

**Risk:** HIGH - Without RBAC tests, users could access unauthorized data or perform unauthorized actions.

**Example Attack Scenarios (Unvalidated):**
1. Technician accesses GET /users and sees all user emails
2. Client admin creates super_admin user via POST /users
3. Site manager accesses other sites' work orders
4. Technician approves invoices
5. Manager deletes assets

**Recommendation:** Create `backend/tests/test_rbac.py` with comprehensive RBAC matrix tests (see Test_Plan.md section 1.1).

---

### 3.2 Tenant Isolation Testing Gap

**Status:** 0 tests exist for tenant isolation.

**Required:** 50+ tests (10 endpoints × 5 scenarios = 50 test cases)

**Gap:** 50 tests

**Risk:** CRITICAL - Without tenant isolation tests, data leaks between tenants are possible.

**Example Attack Scenarios (Unvalidated):**
1. Tenant A user GUESses Tenant B work order UUID and accesses it
2. Tenant A user filters by Tenant B's client_id and sees data
3. Tenant A user creates work order with Tenant B's site_id
4. List endpoints return data from all tenants

**Recommendation:** Create `backend/tests/test_tenancy.py` with cross-tenant access tests (see Test_Plan.md section 1.2).

---

### 3.3 Input Validation Gap

**Status:** 0 tests exist for input validation.

**Required:** 30+ tests (SQL injection, XSS, UUID validation)

**Gap:** 30 tests

**Risk:** MEDIUM - Input validation bugs could lead to SQL injection or XSS attacks.

**Recommendation:** Create security test suite with OWASP Top 10 attack scenarios.

---

## 4. Fixture Gap Analysis

### 4.1 Required Fixtures Not Created

**Purpose:** Fixtures reduce test setup boilerplate and ensure consistent test data.

**Missing Fixtures:**

1. ❌ **`company_admin_user(db_session, sample_tenant)`** - User with company_admin role
2. ❌ **`client_admin_user(db_session, sample_tenant, sample_client)`** - User with client_admin role
3. ❌ **`site_manager_user(db_session, sample_tenant, sample_site)`** - User with site_manager role
4. ❌ **`technician_user(db_session, sample_tenant)`** - User with technician role
5. ❌ **`manager_user(db_session, sample_tenant)`** - User with manager role
6. ❌ **`super_admin_token(super_admin_user)`** - Authentication token for super_admin
7. ❌ **`company_admin_token(company_admin_user)`** - Token for company_admin
8. ❌ **`technician_token(technician_user)`** - Token for technician
9. ❌ **`tenant_b(db_session)`** - Second tenant for isolation tests
10. ❌ **`sample_work_order(db_session, sample_site)`** - Work order fixture
11. ❌ **`sample_asset(db_session, sample_site)`** - Asset fixture
12. ❌ **`sample_report(db_session, sample_work_order)`** - Report fixture
13. ❌ **`sample_invoice(db_session, sample_client)`** - Invoice fixture
14. ❌ **`sample_labor_entry(db_session, sample_work_order)`** - Labor entry fixture
15. ❌ **`sample_location(db_session, sample_site)`** - Location fixture

**Impact:** HIGH - Without these fixtures, writing new tests is slow and error-prone. Each test would need to manually create users, authenticate, and set up data.

**Recommendation:** Expand `backend/conftest.py` with all missing fixtures (see implementation example below).

---

## 5. Frontend Testing Gap

### 5.1 Component Tests (0% Coverage)

**Status:** No component tests exist.

**Required Components to Test:**
1. ❌ `FilterBar.test.tsx` (15 tests)
2. ❌ `AssetLifecycleBadge.test.tsx` (8 tests)
3. ❌ `TagBadge.test.tsx` (5 tests)
4. ❌ `Sidebar.test.tsx` (10 tests) - Role-based visibility
5. ❌ `Breadcrumbs.test.tsx` (5 tests)

**Impact:** MEDIUM - Components work but lack regression protection. Refactoring could break existing functionality.

---

### 5.2 Page Tests (0% Coverage)

**Status:** No page tests exist.

**Required Page Tests:**
1. ❌ `WorkOrdersPage.test.tsx` (20 tests)
2. ❌ `WorkOrderDetailPage.test.tsx` (15 tests)
3. ❌ `AssetsPage.test.tsx` (15 tests)
4. ❌ `DashboardPage.test.tsx` (10 tests)

**Impact:** MEDIUM - Pages work but lack integration tests with API mocks.

---

## 6. E2E Testing Gap

### 6.1 Critical User Journeys (0% Coverage)

**Status:** No E2E tests exist.

**Required E2E Tests:**
1. ❌ Super admin login → Companies → Sites → Work Orders → Detail
2. ❌ Technician login → Assigned WOs → Update status → Submit report
3. ❌ Client admin login → Sites → Create WO → Approve invoice
4. ❌ Asset lifecycle: Create asset → Complete repairs → Verify replacement WO
5. ❌ Report approval: Technician submits → Manager approves → Invoice generated

**Impact:** HIGH - No automated validation of end-to-end workflows. Regressions could go unnoticed.

**Recommendation:** Set up Playwright and create 5 critical E2E tests (see Test_Plan.md section 3).

---

## 7. Test Infrastructure Gaps

### 7.1 Missing Test Configuration

**Files Not Created:**
1. ❌ `backend/pytest.ini` - Pytest configuration
2. ❌ `backend/.coveragerc` - Coverage configuration
3. ❌ `vitest.config.ts` - Frontend test configuration (might exist but not verified)
4. ❌ `playwright.config.ts` - E2E test configuration
5. ❌ `.github/workflows/tests.yml` - CI pipeline for tests

**Impact:** MEDIUM - Tests can run locally, but CI integration is missing.

---

### 7.2 Missing Test Data Management

**Issues:**
1. ❌ No seed data script for test database
2. ❌ No test data cleanup strategy
3. ❌ No test database isolation (tests could interfere with each other)

**Recommendation:**
- Use in-memory SQLite for unit tests (already done in `conftest.py`)
- Use PostgreSQL test database for integration/E2E tests
- Implement database cleanup hooks in pytest

---

## 8. Prioritized Test Implementation Plan

### Phase 1: Critical Security Tests (Week 1)

**Goal:** Prevent security vulnerabilities from reaching production.

**Tasks:**
1. Create `backend/tests/test_rbac.py` with 30 tests (high-priority endpoints)
2. Create `backend/tests/test_tenancy.py` with 10 tests
3. Expand `backend/conftest.py` with role-based user fixtures and token fixtures
4. Run tests in CI pipeline

**Expected Coverage Gain:** 
- Backend: 5% → 25%
- RBAC: 0% → 50%
- Tenant isolation: 0% → 80%

**Deliverables:**
- [ ] 40 new backend tests passing
- [ ] CI pipeline running tests on every push
- [ ] RBAC test report showing role access matrix

---

### Phase 2: Core Feature Tests (Week 2)

**Goal:** Validate core Phase 2 features (asset lifecycle, filters).

**Tasks:**
1. Complete asset lifecycle tests (20 tests)
2. Create filter tests (15 backend tests)
3. Create work order lifecycle tests (15 tests)
4. Create user management tests (15 tests)

**Expected Coverage Gain:**
- Backend: 25% → 50%
- Asset lifecycle: 40% → 90%
- Work orders: 0% → 60%

**Deliverables:**
- [ ] 65 new backend tests passing
- [ ] Asset lifecycle edge cases covered
- [ ] Filter functionality validated

---

### Phase 3: Frontend Tests (Week 3)

**Goal:** Add frontend test coverage for new components and pages.

**Tasks:**
1. Create FilterBar.test.tsx (15 tests)
2. Create WorkOrdersPage.test.tsx (20 tests)
3. Create AssetLifecycleBadge.test.tsx (8 tests)
4. Set up Vitest coverage reporting

**Expected Coverage Gain:**
- Frontend: 0% → 40%

**Deliverables:**
- [ ] 43 new frontend tests passing
- [ ] Frontend coverage report in CI

---

### Phase 4: Integration & E2E Tests (Week 4)

**Goal:** Add integration and E2E tests for critical workflows.

**Tasks:**
1. Set up Playwright
2. Create 5 E2E tests (super admin, technician, client admin flows)
3. Create integration tests for asset lifecycle (5 tests)
4. Create integration tests for work order creation (5 tests)

**Expected Coverage Gain:**
- Backend: 50% → 65%
- E2E: 0% → 80% (critical paths)

**Deliverables:**
- [ ] 5 E2E tests passing
- [ ] 10 integration tests passing
- [ ] E2E test recordings

---

### Phase 5: Remaining Features (Weeks 5-7)

**Goal:** Complete test coverage for P2-F3, P2-F4, P2-F5, P2-F6.

**Tasks:**
1. Labor management tests (30 tests)
2. Location management tests (25 tests)
3. Dashboard tests (20 tests)
4. Maintenance tagging tests (10 tests)

**Expected Coverage Gain:**
- Backend: 65% → 80%+
- Frontend: 40% → 70%+

**Deliverables:**
- [ ] 85 new tests passing
- [ ] All Phase 2 features tested

---

## 9. Risk Assessment

### 9.1 Risk Matrix

| Gap | Likelihood | Impact | Risk Level | Mitigation |
|-----|-----------|--------|------------|------------|
| RBAC bypass | High | Critical | **CRITICAL** | Phase 1 tests |
| Tenant isolation breach | Medium | Critical | **HIGH** | Phase 1 tests |
| Asset lifecycle failure | Medium | High | **MEDIUM** | Phase 2 tests |
| Filter bugs | High | Medium | **MEDIUM** | Phase 2 tests |
| Frontend regressions | Medium | Medium | **MEDIUM** | Phase 3 tests |
| Performance issues | Low | Medium | **LOW** | Performance tests |
| i18n bugs | Medium | Low | **LOW** | Manual testing |

---

### 9.2 Production Readiness Assessment

**Can Phase 2 be deployed to production today?**

❌ **NO** - Critical test gaps exist.

**Blockers:**
1. No RBAC tests (0/180 required)
2. No tenant isolation tests (0/50 required)
3. No user management tests (0/25 required)
4. No E2E tests (0/5 required)

**Minimum Requirements for Production:**
- [x] Asset lifecycle basic tests (4/15 exist)
- [ ] RBAC tests for critical endpoints (0/30 exist)
- [ ] Tenant isolation tests (0/10 exist)
- [ ] User management RBAC tests (0/10 exist)
- [ ] E2E tests for super admin and technician flows (0/2 exist)

**Estimated Time to Production Readiness:** 4 weeks (Phases 1-4 complete)

---

## 10. Recommendations

### 10.1 Immediate Actions (This Week)

1. **Create RBAC Test Suite** (backend/tests/test_rbac.py)
   - Test 10 critical endpoints with all 6 roles
   - Focus on write operations (POST, PATCH, DELETE)

2. **Create Tenant Isolation Test Suite** (backend/tests/test_tenancy.py)
   - Test cross-tenant access on 5 key endpoints
   - Verify list endpoints return only tenant-scoped data

3. **Expand Fixtures** (backend/conftest.py)
   - Add role-based user fixtures
   - Add token fixtures for authentication

4. **Set Up CI Pipeline** (.github/workflows/tests.yml)
   - Run pytest on every push
   - Block merge if tests fail

### 10.2 Short-Term Actions (Next 2 Weeks)

1. **Complete Asset Lifecycle Tests** (backend/tests/test_asset_lifecycle.py)
   - Add 11 missing unit tests
   - Add 5 integration tests

2. **Create Filter Tests** (backend/tests/test_filters.py)
   - Test all filter parameters individually
   - Test filter combinations

3. **Create Work Order Tests** (backend/tests/test_work_orders.py)
   - Test status transitions
   - Test assignment logic

4. **Add Frontend Tests** (src/)
   - FilterBar.test.tsx
   - WorkOrdersPage.test.tsx

### 10.3 Long-Term Actions (Next 4 Weeks)

1. **Set Up E2E Tests** (tests/e2e/)
   - Install Playwright
   - Create 5 critical user journey tests

2. **Add Labor Management Tests**
   - 30 backend tests
   - 15 frontend tests

3. **Add Location Management Tests**
   - 25 backend tests
   - 12 frontend tests

4. **Add Dashboard Tests**
   - 20 backend tests
   - 25 frontend tests

5. **Performance Tests**
   - Load test with 1000+ records
   - Concurrent user test

---

## 11. Appendix A: Sample Fixture Implementation

Here's an example of how to expand `backend/conftest.py` with missing fixtures:

```python
# backend/conftest.py (additions)

import pytest
from app.models import User, UserRole, WorkOrder, Asset
from app.core.security import hash_password
from uuid import uuid4

# ===== Role-based User Fixtures =====

@pytest.fixture
def company_admin_user(db_session, sample_tenant):
    """Create a test user with company_admin role."""
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="company_admin@test.com",
        password_hash=hash_password("password123"),
        full_name="Company Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def technician_user(db_session, sample_tenant):
    """Create a test user with technician role."""
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="technician@test.com",
        password_hash=hash_password("password123"),
        full_name="Technician",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

# ===== Authentication Token Fixtures =====

@pytest.fixture
def super_admin_token(sample_user):
    """Get JWT token for super admin."""
    from app.core.security import create_access_token
    return create_access_token(sample_user.id)

@pytest.fixture
def technician_token(technician_user):
    """Get JWT token for technician."""
    from app.core.security import create_access_token
    return create_access_token(technician_user.id)

# ===== Multi-Tenant Fixtures =====

@pytest.fixture
def tenant_b(db_session):
    """Create a second tenant for isolation tests."""
    from app.models import Tenant
    tenant = Tenant(id=uuid4(), name="Tenant B", status="active")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

# ===== Data Fixtures =====

@pytest.fixture
def sample_work_order(db_session, sample_tenant, sample_client, sample_site):
    """Create a test work order."""
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        site_id=sample_site.id,
        status="created",
        source="corrective",
        category="repair",
        urgency="normal",
        title="Test Work Order",
    )
    db_session.add(wo)
    db_session.commit()
    db_session.refresh(wo)
    return wo

@pytest.fixture
def sample_asset(db_session, sample_tenant, sample_site):
    """Create a test asset."""
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Test Asset",
        category="general",
        max_repair_count=3,
        current_repair_count=0,
        lifecycle_status="active",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset
```

**Usage Example:**

```python
def test_technician_cannot_access_all_users(db_session, technician_token):
    """TC-RBAC-GET-users-technician"""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert response.status_code == 403
```

---

## 12. Appendix B: Sample RBAC Test Implementation

```python
# backend/tests/test_rbac.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ===== User Management Endpoint Tests =====

def test_super_admin_can_list_users(db_session, super_admin_token):
    """TC-RBAC-001: Super admin can GET /users"""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_company_admin_can_list_users(db_session, company_admin_token):
    """TC-RBAC-002: Company admin can GET /users"""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {company_admin_token}"}
    )
    assert response.status_code == 200

def test_technician_cannot_list_users(db_session, technician_token):
    """TC-RBAC-003: Technician cannot GET /users"""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

def test_super_admin_can_create_user(db_session, super_admin_token):
    """TC-RBAC-004: Super admin can POST /users"""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json={
            "email": "new_tech@test.com",
            "password": "SecurePass123!",
            "full_name": "New Technician",
            "role": "technician"
        }
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new_tech@test.com"

def test_company_admin_cannot_create_user(db_session, company_admin_token):
    """TC-RBAC-005: Company admin cannot POST /users"""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {company_admin_token}"},
        json={
            "email": "new_tech@test.com",
            "password": "SecurePass123!",
            "full_name": "New Technician",
            "role": "technician"
        }
    )
    assert response.status_code == 403

# ... (add 25 more RBAC tests for other endpoints)
```

---

## 13. Conclusion

**Summary:**
- Current test coverage is insufficient for production deployment (5% backend, 0% frontend, 0% E2E)
- Critical security gaps exist (no RBAC tests, no tenant isolation tests)
- 250+ tests are missing across backend, frontend, and E2E
- Estimated 7 weeks to reach 80% coverage target

**Next Steps:**
1. Begin Phase 1 (Critical Security Tests) immediately
2. Allocate dedicated QA resources (1 QA engineer full-time)
3. Set up CI pipeline to run tests automatically
4. Create test coverage dashboard for visibility
5. Block production deployment until Phase 4 complete (minimum viable test coverage)

**Production Readiness Target:** 4 weeks from today (with Phase 1-4 complete)

---

**End of Gap Analysis Report**
