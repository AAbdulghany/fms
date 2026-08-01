# Phase 3.1 Master Plan

**Status:** In Progress  
**Prerequisite:** [Phase 3 MVP sign-off](../phase3/PHASE3_SIGNOFF.md) — GO  
**Author:** Hisham (Tech Lead)  
**Architect review:** Tariq (Solution Architect)

---

## Executive summary

Phase 3.1 delivers deferred MVP scope plus three strategic pillars:

1. **Notifications** — DB persistence + actionable deep-links
2. **Invoice lifecycle** — preview → generate → print → email with PDF
3. **Assets (flagship)** — maintenance scheduling, smart labels, client maintenance view

Also: CSV import, demo hosting stack, manual subscription gating, Phase 4 outline.

---

## Foundations (do not rebuild)

| Area | Exists | Gap |
|------|--------|-----|
| WO requests | Review modal, approve/decline | Notifications not persisted / not deep-linked |
| Notifications | WebSocket + in-memory FE | No DB, bell links to WO detail |
| Invoices | billing.py, PDF endpoint | No preview UI; send does not email PDF |
| Assets | MaintenanceSchedule model | No schedule API/UI; no smart labels |
| Hosting | Postgres-only compose | No app services |
| Subscription | Tenant model | No plan/status gating |

---

## Milestones

| ID | Name | Size | Depends |
|----|------|------|---------|
| M0 | Docs + AgDRs | S | Phase 3 sign-off |
| M1 | Notifications | M | M0 |
| M2 | Invoice cycle | M | M0 |
| M3 | Assets flagship | L–XL | M0 |
| M4 | CSV import | M | M3 |
| M5 | Demo hosting | M | — |
| M6 | Subscription | S–M | — |
| M7 | Sign-off + Phase 4 | S | M1–M6 |

**Build order:** M1 → M2 → M3 → M4 → M5 ∥ M6 → M7

---

## M1 — Notifications

- `notifications` table: user_id, type, title, payload_json, read_at, created_at
- REST: `GET /notifications`, `PATCH /notifications/{id}/read`, `POST /notifications/read-all`
- WebSocket = delivery channel; DB = source of truth
- Deep-link: `work_order.requested` → `/work-orders?view=requests&review={woId}`
- Deep-link: `work_order.status_changed` → `/work-orders/{id}` or `?view=my_requests`
- Remove report template selector from WO create/request modals

See [AgDR-PHASE3.1-NOTIFICATIONS.md](AgDR-PHASE3.1-NOTIFICATIONS.md).

---

## M2 — Invoice full cycle

- `GET /work-orders/{id}/invoice-preview` (non-persisting)
- Invoice preview modal before generate
- Enhanced PDF (header, bill-to, reference, work summary, footer)
- `POST /invoices/{id}/send` emails PDF attachment
- Print via inline PDF in browser tab

See [AgDR-PHASE3.1-INVOICE-CYCLE.md](AgDR-PHASE3.1-INVOICE-CYCLE.md).

---

## M3 — Assets flagship

**M3a — Scheduling:** CRUD on `/assets/{id}/schedules`; cron job creates preventive WOs  
**M3b — Smart labels:** `{SITE_CODE}-{CATEGORY}-{SEQ}` + QR payload  
**M3c — Client view:** list sorted by `next_due_at`, filters, enriched detail

See [AgDR-PHASE3.1-ASSETS-SMART-LABELS.md](AgDR-PHASE3.1-ASSETS-SMART-LABELS.md).

---

## M4 — CSV import

Upload → validate → preview → bulk insert. Idempotency: serial per site.

---

## M5 — Demo hosting

Full docker-compose (api, web, db, migrate). `deploy/` folder. [DEMO_DEPLOY.md](DEMO_DEPLOY.md). Target: Railway or Render.

See [AgDR-PHASE3.1-DEMO-HOSTING.md](AgDR-PHASE3.1-DEMO-HOSTING.md).

---

## M6 — Subscription (manual)

`Tenant.settings_json.subscription`: plan, status, valid_until, limits, features.  
Middleware blocks suspended/expired tenants. Super-admin panel (no Stripe).

See [AgDR-PHASE3.1-SUBSCRIPTION.md](AgDR-PHASE3.1-SUBSCRIPTION.md).

---

## M7 — Sign-off

Execute [PHASE3.1_TEST_PLAN.md](PHASE3.1_TEST_PLAN.md), fill [PHASE3.1_SIGNOFF.md](PHASE3.1_SIGNOFF.md), publish [PHASE4_OUTLINE.md](PHASE4_OUTLINE.md).

---

## Phase 4 preview (plan only)

- Payment gateway or self-serve signup
- Dedicated WO Requests dashboard
- SLA automation + escalation
- Mobile/PWA for technicians
- Client analytics dashboard
- Multi-language invoice PDFs

---

**Last updated:** June 2026
