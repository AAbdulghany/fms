# RBAC Matrix - FMS Security Foundation

**Document Version:** 1.0  
**Date:** 2026-04-17  
**Status:** Implemented & Tested

## Overview

This document defines the Role-Based Access Control (RBAC) matrix for the Facility Management System (FMS). It specifies which roles can perform which operations on each endpoint, ensuring proper authorization and tenant isolation.

## Roles

The FMS supports 6 distinct roles, each with specific permissions:

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **Super Admin** | `super_admin` | Full system access | All tenants (if platform_admin) or tenant-wide |
| **Company Admin** | `company_admin` | Full tenant access except user management | Tenant-wide |
| **Client Admin** | `client_admin` | Client data management | Single client only |
| **Site Manager** | `site_manager` | Site operations | Assigned sites only |
| **Technician** | `technician` | Work order execution | Assigned work orders only |
| **Manager** | `manager` | Report approval | Tenant-wide (read-only for most) |

## RBAC Matrix by Endpoint

### User Management (`/api/v1/users`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /users` | ✅ Full access | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| `POST /users` | ✅ Create company_admin, technician | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| `GET /users/me` | ✅ Own profile | ✅ Own profile | ✅ Own profile | ✅ Own profile | ✅ Own profile | ✅ Own profile |

**Notes:**
- Only `super_admin` can create users
- `super_admin` can only create `company_admin` and `technician` roles
- All users can view their own profile via `/users/me`

---

### Work Orders (`/api/v1/work-orders`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /work-orders` | ✅ All WOs | ✅ All WOs | ✅ Client WOs only | ✅ Site WOs only | ✅ Assigned only | ✅ All WOs (read) |
| `POST /work-orders` | ✅ Create | ✅ Create | ✅ Create | ✅ Create | ❌ Forbidden | ❌ Forbidden |
| `GET /work-orders/{id}` | ✅ Any WO | ✅ Any WO | ✅ Client WO only | ✅ Site WO only | ✅ Assigned only | ✅ Any WO (read) |
| `PATCH /work-orders/{id}` | ✅ Update any | ✅ Update any | ✅ Client WO only | ✅ Site WO only | ✅ Assigned only | ✅ Update any |
| `POST /work-orders/{id}/assign` | ✅ Assign | ✅ Assign | ❌ Forbidden | ✅ Assign | ❌ Forbidden | ❌ Forbidden |

**Access Filters:**
- `super_admin`, `company_admin`, `manager`: See all work orders in tenant
- `client_admin`: Filtered by `client_id` (only their client)
- `site_manager`: Filtered by `site_id` in their `UserSiteScope`
- `technician`: Filtered by `assignee_user_id` (only assigned to them)

**Query Parameters:** status, urgency, client_id, site_id, assignee_user_id, date_from, date_to, search, tags

---

### Assets (`/api/v1/assets`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /assets` | ✅ All assets | ✅ All assets | ✅ Client assets | ✅ Site assets | ✅ All assets (read) | ✅ All assets (read) |
| `POST /assets` | ✅ Create | ✅ Create | ❌ Forbidden | ✅ Create | ❌ Forbidden | ❌ Forbidden |
| `GET /assets/{id}/lifecycle` | ✅ Any asset | ✅ Any asset | ✅ Client asset | ✅ Site asset | ✅ Any asset (read) | ✅ Any asset (read) |
| `POST /assets/{id}/reset-lifecycle` | ✅ Reset | ✅ Reset | ❌ Forbidden | ✅ Reset | ❌ Forbidden | ❌ Forbidden |

**Access Filters:**
- `client_admin`: Filtered by sites belonging to their client
- `site_manager`: Filtered by sites in their `UserSiteScope`

**Query Parameters:** site_id, category, search

---

### Invoices (`/api/v1/invoices`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /invoices` | ✅ All invoices | ✅ All invoices | ✅ Client invoices | ✅ All invoices (read) | ✅ All invoices (read)* | ✅ All invoices (read) |
| `GET /invoices/{id}` | ✅ Any invoice | ✅ Any invoice | ✅ Client invoice | ✅ Any invoice (read) | ✅ Any invoice (read)* | ✅ Any invoice (read) |
| `POST /invoices/{id}/approve` | ✅ Approve | ✅ Approve | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| `POST /invoices/{id}/send` | ✅ Send | ✅ Send | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| `POST /invoices/{id}/mark-paid` | ✅ Mark paid | ✅ Mark paid | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |

**Access Filters:**
- `client_admin`: Filtered by `client_id`
- *Technicians have no filtering on invoices - **potential security issue to address**

**Query Parameters:** status, client_id, date_from, date_to

---

### Maintenance Reports (`/api/v1/reports`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `POST /reports/{id}/approve` | ✅ Approve | ✅ Approve | ✅ Approve (client) | ❌ Forbidden | ❌ Forbidden | ✅ Approve |
| `POST /reports/{id}/reject` | ✅ Reject | ✅ Reject | ✅ Reject (client) | ❌ Forbidden | ❌ Forbidden | ✅ Reject |

**Notes:**
- `manager` role specifically exists to approve reports without WO creation rights
- Report access is validated through the associated work order's permissions

---

### Clients (`/api/v1/clients`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /clients` | ✅ All clients | ✅ All clients | ✅ Own client only | ✅ All clients (read) | ✅ All clients (read) | ✅ All clients (read) |
| `POST /clients` | ✅ Create | ✅ Create | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| `GET /clients/{id}` | ✅ Any client | ✅ Any client | ✅ Own client only | ✅ Any client (read) | ✅ Any client (read) | ✅ Any client (read) |

**Access Filters:**
- `client_admin`: Filtered to only their assigned client

---

### Sites (`/api/v1/sites`)

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-------------|---------------|--------------|--------------|------------|---------|
| `GET /sites` | ✅ All sites | ✅ All sites | ✅ Client sites | ✅ Assigned sites | ✅ All sites (read) | ✅ All sites (read) |
| `POST /sites` | ✅ Create | ✅ Create | ❌ Forbidden | ✅ Create | ❌ Forbidden | ❌ Forbidden |

**Access Filters:**
- `client_admin`: Filtered by sites belonging to their client
- `site_manager`: Filtered by sites in their `UserSiteScope`

**Query Parameters:** client_id

---

## Tenant Isolation

### Core Principle

**Every endpoint MUST enforce tenant isolation by filtering queries with `tenant_id`:**

```python
# All queries must include tenant filtering
q = select(Model).where(Model.tenant_id == current_user.tenant_id)
```

### Tenant Context

The `get_current_user` dependency in `app/api/deps.py` automatically sets the tenant context:

```python
def get_current_user(...) -> User:
    # ... validate token and get user ...
    
    # Set tenant context for the request
    from app.database import tenant_context
    tenant_context.set(user.tenant_id)
    
    return user
```

### 404 vs 403 for Security

To prevent **tenant enumeration attacks**, endpoints return `404 NOT_FOUND` instead of `403 FORBIDDEN` when accessing resources from other tenants:

```python
# Good: Returns 404 (resource doesn't exist in your tenant)
if not resource or resource.tenant_id != current_user.tenant_id:
    raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")

# Bad: Returns 403 (confirms resource exists but access denied)
if resource.tenant_id != current_user.tenant_id:
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
```

---

## Security Best Practices

### 1. Role Enforcement Pattern

Use the `require_roles()` dependency for role-based checks:

```python
from app.api.deps import require_roles

@router.post("/work-orders")
def create_work_order(
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, Depends(require_roles(
        UserRole.super_admin,
        UserRole.company_admin,
        UserRole.site_manager
    ))]
) -> WorkOrder:
    # Only super_admin, company_admin, site_manager can create
    ...
```

### 2. Data Scoping Pattern

Always apply role-specific filtering:

```python
def list_resources(db: Session, current: User):
    q = select(Resource).where(Resource.tenant_id == current.tenant_id)
    
    # Role-based filtering
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(Resource.client_id == current.client_id)
    
    if current.role == UserRole.site_manager:
        scoped_sites = db.scalars(
            select(UserSiteScope.site_id)
            .where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped_sites:
            q = q.where(Resource.site_id.in_(scoped_sites))
    
    return list(db.scalars(q).all())
```

### 3. Entity Access Validation

Create helper functions for entity access:

```python
def _access_work_order(db: Session, current: User, wo_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, wo_id)
    
    # Tenant isolation (404 to prevent enumeration)
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    
    # Role-based access
    if current.role == UserRole.technician:
        if wo.assignee_user_id != current.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    if current.role == UserRole.client_admin and current.client_id:
        if wo.client_id != current.client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    if current.role == UserRole.site_manager:
        scoped = db.scalars(
            select(UserSiteScope.site_id)
            .where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    return wo
```

---

## Test Coverage

Comprehensive test suites verify RBAC and tenant isolation:

### RBAC Tests (`backend/tests/test_rbac.py`)

- **44 tests** covering all 6 roles across all critical endpoints
- Verifies both allowed and forbidden operations
- Tests role-specific data scoping (client, site, assigned WOs)

**Test Results:** ✅ All 44 RBAC tests passing

### Tenant Isolation Tests (`backend/tests/test_isolation.py`)

- **24 tests** verifying cross-tenant data isolation
- UUID guessing attack prevention (404 on random UUIDs)
- Cross-tenant modification attempts blocked
- Tenant context properly enforced

**Test Results:** ✅ All 24 isolation tests passing

### Total Security Test Suite

**73 tests total** - All passing ✅
- 4 asset lifecycle tests
- 44 RBAC tests
- 24 tenant isolation tests
- 1 tenant context test

---

## Known Security Issues

### 1. Technician Invoice Access

**Issue:** Technicians can currently list all invoices in their tenant without filtering.

**Risk:** Low (read-only, but violates principle of least privilege)

**Recommendation:** Add role-based filtering to invoices endpoint to restrict technicians to only invoices related to their assigned work orders.

**Fix:**
```python
# In backend/app/api/routes/invoices.py
if current.role == UserRole.technician:
    # Only show invoices for work orders assigned to this technician
    assigned_wos = db.scalars(
        select(WorkOrder.id)
        .where(WorkOrder.assignee_user_id == current.id)
    ).all()
    q = q.where(Invoice.work_order_id.in_(assigned_wos))
```

---

## Maintenance & Updates

### When Adding New Endpoints

1. **Define role requirements** in this document
2. **Apply `require_roles()` dependency** to endpoint
3. **Add tenant filtering** to all queries
4. **Implement data scoping** for restricted roles
5. **Write RBAC tests** covering allowed/forbidden access
6. **Write isolation tests** for cross-tenant scenarios
7. **Update this matrix** with new endpoint permissions

### When Adding New Roles

1. **Define role scope** and intended use case
2. **Update `UserRole` enum** in `backend/app/models.py`
3. **Add role to this matrix** for all endpoints
4. **Write comprehensive test suite** for new role
5. **Document role in schema** (`backend/app/schemas.py`)

---

## References

- [Backend Agent Skill](.claude/skills/senior-backend.md)
- [RBAC Test Suite](../backend/tests/test_rbac.py)
- [Tenant Isolation Tests](../backend/tests/test_isolation.py)
- [Authentication Dependencies](../backend/app/api/deps.py)
- [Security Module](../backend/app/core/security.py)

---

**Document Owner:** Backend Engineering Team  
**Last Updated:** 2026-04-17  
**Next Review:** Before Phase 3 deployment
