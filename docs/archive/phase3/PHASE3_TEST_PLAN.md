# Phase 3 MVP — Test Plan

**Scope:** MVP slice (WO request flow, provisioning UX, page fixes, user CRUD). CSV import and smart asset labels deferred to Phase 3.1.

## Backend tests (`backend/tests/`)

### WO request flow (`test_work_order_requests.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| WR-01 | client_admin submits request for own client/site | 201, status=`requested` |
| WR-02 | site_manager submits for scoped site | 201 |
| WR-03 | site_manager submits for unscoped site | 403 |
| WR-04 | client_admin direct POST `/work-orders` | 403 |
| WR-05 | company_admin approves request | status=`created`, notify requester |
| WR-06 | company_admin declines request | status=`declined` |
| WR-07 | technician cannot approve | 403 |

### Provisioning (`test_provisioning.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| PR-01 | Company "Giza Systems" → code contains slug | Unique client code |
| PR-02 | Manager "Abdullah" → username `abdullah-cmgr@gizasystems` | Unique in tenant |
| PR-03 | Site manager → `abdullah-smgr@gizasystems` | Unique in tenant |
| PR-04 | Duplicate username collision | Suffix appended |

### Users (`test_users_crud.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| US-01 | super_admin lists users | 200, tenant-scoped |
| US-02 | company_admin creates technician | 201 |
| US-03 | User PATCH own password + full_name | 200, username unchanged |
| US-04 | User PATCH username | 400/403 |

## Frontend manual / E2E checklist

| ID | Page | Steps | Expected |
|----|------|-------|----------|
| FE-01 | Dashboard | Register Asset button | Opens asset modal or navigates with register open |
| FE-02 | Companies | Add Company label | Button reads "Add Company" |
| FE-03 | Company detail | Work orders tab | Lists WOs for company + site column + filters |
| FE-04 | Company detail | Invoices tab | Lists invoices with status |
| FE-05 | Assets | Select asset row | Detail page loads without error |
| FE-06 | Users | Add User | Modal creates user; status/last login display correctly |
| FE-07 | Work orders | Requests tab (admin) | Shows pending requests; approve works |
| FE-08 | Work orders | Request WO (client admin) | Creates request, not direct WO |

## Security review gate

Run `/security-review` checklist on: auth profile endpoints, WO approve/decline RBAC, provisioning username uniqueness, CSV upload (Phase 3.1).
