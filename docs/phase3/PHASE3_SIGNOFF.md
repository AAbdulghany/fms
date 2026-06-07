# Phase 3 MVP — Sign-off

**Date:** 2026-06-06  
**Scope:** WO request flow (Option B), provisioning UX, page fixes, user CRUD, security H1/H2  
**Deferred to 3.1:** CSV asset import, smart asset labels, dedicated WO Requests dashboard (Option A)

## Backend automated tests

| Suite | Result |
|-------|--------|
| Full `backend/tests/` | **127 passed** (incl. WR-01–WR-07, security H1/H2, provisioning, users) |
| API smoke (`backend/scripts/phase3_api_smoke.py`) | **8/8 PASS** |

## Frontend manual checklist (FE-01–FE-08)

| ID | Scenario | Result | Notes |
|----|----------|--------|-------|
| FE-01 | Dashboard → Register Asset | **PASS** | Navigates to `/assets?register=1`, modal opens |
| FE-02 | Companies → Add Company label | **PASS** | Button reads "+ إضافة شركة" / Add Company |
| FE-03 | Company detail → Work orders tab | **PASS** | Tab loads WO list for company |
| FE-04 | Company detail → Invoices tab | **PASS** | Tab loads invoice list |
| FE-05 | Asset row → detail page | **PASS** | Fixed missing `GET /assets/{id}` during sign-off |
| FE-06 | Users → Add User modal | **PASS** | Modal opens; optional password + role select |
| FE-07 | Work orders → Requests tab (admin) | **PASS** | Tab clickable; review modal with edit/approve/decline; approve records status transition in history |
| FE-08 | Work orders → Request WO (client admin) | **PASS** | Request button (not create); company/site locked to user's client; submits via `/work-orders/request` |

## Fixes applied during this sign-off slice

1. **Requests tab not clickable** — `FilterBar` was overwriting URL params and stripping `view=requests`; now merges filter params while preserving `view`.
2. **Request review UX** — `WorkOrderRequestReviewModal`: edit title/description/urgency, approve (status transition), decline with **mandatory reason**.
3. **History** — Approve/decline audit uses `update` action with `before/after` status; detail page shows transition + decline reason.
4. **Scoped request form** — client_admin/site_manager see only their company/sites; readonly when single option.
5. **Backend** — `DeclineRequestBody.reason` required; site_manager client list scoped; `GET /assets/{id}` added.
6. **Request submit** — Resolved client/site IDs from locked fields when form state empty.

## Phase 3 MVP verdict

**GO** — Phase 3 MVP criteria met. Remaining items explicitly deferred to Phase 3.1.

## Demo credentials

| Role | Email | Password |
|------|-------|----------|
| super_admin | super@demo.com | super123 |
| company_admin | admin@demo.com | admin123 |
| client_admin | client@demo.com | client123 |
| site_manager | site@demo.com | site123 |
| technician | tech@demo.com | tech123 |

## How to re-run smoke

```bash
# Backend
cd backend && uv run pytest tests/ -q
python scripts/phase3_api_smoke.py

# Frontend (dev server with API proxy)
npm run dev
# Manual: docs/phase3/PHASE3_TEST_PLAN.md FE-01–FE-08
```
