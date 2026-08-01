# Technical Design: Work Order Request Flow (Phase 3 MVP)

**Status:** Approved for Build (Option B — pending team sign-off)  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Overview

Client admins and site managers **request** work orders; only `super_admin` and `company_admin` **create/approve** them into active workflow. MVP uses **Option B**: requests appear as a filter tab on the existing Work Orders page with notification to company admins. Option A (dedicated queue page) is documented as Phase 3.1 fallback if request volume grows.

## Domain Model

### Work order status extension

Add `requested` to `WorkOrderStatus`:

| Status | Meaning | Who sets |
|--------|---------|----------|
| `requested` | Pending company admin review | client_admin, site_manager |
| `created` | Approved and in normal FSM | super_admin, company_admin (on approve) |
| `declined` | Rejected request (terminal) | super_admin, company_admin |

FSM additions:

```
requested → created | declined
created → … (existing FSM unchanged)
```

### Authorization matrix

| Action | super_admin | company_admin | client_admin | site_manager |
|--------|-------------|---------------|--------------|--------------|
| Submit request | ✓ | ✓ | ✓ (scoped) | ✓ (scoped) |
| Direct create (skip request) | ✓ | ✓ | ✗ | ✗ |
| Approve / decline request | ✓ | ✓ | ✗ | ✗ |
| List requests | ✓ | ✓ | own only | own only |

## API Design

| Method | Path | Description |
|--------|------|-------------|
| POST | `/work-orders/request` | Scoped roles submit; status=`requested` |
| POST | `/work-orders` | Admins only; status=`created` (existing) |
| POST | `/work-orders/{id}/approve-request` | Admin → `created`, audit + notify requester |
| POST | `/work-orders/{id}/decline-request` | Admin → `declined`, optional reason body |
| GET | `/work-orders?status=requested` | Filter (existing list endpoint) |

## Notifications

On request submit: notify all active `company_admin` users in tenant (WebSocket + optional email hook). On approve/decline: notify requester (`created_by_user_id`).

## Frontend (Option B)

- `WorkOrdersPage`: tab/filter **Requests** for admins; **My requests** for client/site roles
- Approve / Decline actions on row or detail when status=`requested`
- Remove create-WO modal for client_admin / site_manager; show **Request work order** instead

## NFRs

- Tenant + role scoping on all endpoints (reuse `ensure_client_access`, `ensure_site_access`)
- Audit log on request, approve, decline
- RBAC tests: negative cases for cross-client/site request

## Phase 3.1 (backup — Option A)

Dedicated `/work-order-requests` route with queue UI if >20 open requests per tenant or operator feedback requires it.

## Traceability

| Requirement | Coverage |
|-------------|----------|
| Only admins create WOs | Direct POST restricted; request path for others |
| Notify company admin | `notify_work_order_requested` background task |
| Review / edit / accept / decline | Approve endpoint + PATCH before approve for edit |
