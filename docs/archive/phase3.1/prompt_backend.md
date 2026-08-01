# Phase 3.1 — Backend Engineer Prompt

**Role:** Senior Backend Engineer  
**Framework:** RCCF

## Context

Phase 3 MVP is signed off. Build Phase 3.1 milestones M1–M6 per AgDRs in `docs/phase3.1/`.

## Tasks

### M1 Notifications
- Add `Notification` model + REST endpoints
- Persist in `wo_notifications.py` helpers; include `action` in payload
- Extend `schema_ensure.py` for existing DBs

### M2 Invoice
- `GET /work-orders/{id}/invoice-preview`
- Enhance `render_invoice_pdf`
- Fix `send_invoice` to email PDF attachment

### M3 Assets
- Schedule CRUD on assets
- `label_code` + smart label generator + label PDF
- List assets with `view=maintenance&sort=next_due`
- Maintenance job script

### M4 CSV
- `POST /assets/import/preview` + `POST /assets/import`

### M5 Hosting
- Dockerfiles in `deploy/`, full `docker-compose-local.yml`

### M6 Subscription
- `subscription.py` service + `ensure_active_subscription` dep
- `GET/PATCH /tenants/{id}/subscription`

## Constraints

- Tenant isolation on all queries
- RBAC unchanged except new super_admin tenant routes
- Tests for each milestone in `backend/tests/`

## Verification

```bash
cd backend && uv run pytest -q
```
