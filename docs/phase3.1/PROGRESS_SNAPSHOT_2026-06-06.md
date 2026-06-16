# Progress Snapshot — Before Customer Restructure

**Date:** 2026-06-06  
**Purpose:** Preserve delivered baseline before Phase 3 architecture / subscription restructure.  
**Status:** Phase 3.1 implementation complete (GO sign-off)

---

## What was delivered (Phase 3 MVP + 3.1)

| Area | Delivered | Key paths |
|------|-----------|-----------|
| WO request flow | Approve/decline, review modal, scoped requesters | `work_orders.py`, `WorkOrdersPage.tsx` |
| Notifications | DB persistence + WS + deep-links | `notification_service.py`, `NotificationContext.tsx` |
| Invoices | Preview → generate → print → email PDF | `billing.py`, `InvoicePreviewModal.tsx` |
| Assets | Schedules, smart labels, CSV import, maintenance sort | `assets.py`, `AssetRegisterModal.tsx` |
| Hosting | docker-compose full stack | `deploy/`, `DEMO_DEPLOY.md` |
| Subscription (MVP) | `settings_json.subscription`, super_admin panel, API freeze | `subscription.py`, `SubscriptionPage.tsx` |

## Test baseline

- Backend: **131 tests** passing (`uv run pytest -q`)
- Frontend: **`npm run build`** green
- Sign-off: [`PHASE3.1_SIGNOFF.md`](PHASE3.1_SIGNOFF.md)

## Known gaps vs new customer request

| Customer ask | Current state |
|--------------|---------------|
| 3-tier role model (SW / Maintenance Co / End Client) | Partial — roles exist but platform vs tenant boundaries not formalized |
| Granular subscription packages (SW-controlled) | Manual JSON; no package catalog |
| License expiry = full freeze | API freeze only; login UX partial |
| Demo DB for pitches | docker seed; no isolated demo/prod split |
| Invoice mandatory fields + SW watermark | Basic PDF; missing watermark + field mandate |
| Asset quarterly/yearly dashboard views | Maintenance sort only; no calendar views |
| AI maintenance planning placeholder | Not in schema |

## Do not regress

When restructuring, preserve passing tests and RBAC isolation unless AgDR explicitly migrates behavior.

---

**Next:** See [`../phase3-restructure/README.md`](../phase3-restructure/README.md) for customer-request PRD and sprint plan.
