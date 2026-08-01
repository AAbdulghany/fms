# Phase 3.1 — Test Plan

**Scope:** Notifications, invoice cycle, assets flagship, CSV import, demo hosting, subscription.

## Backend automated tests

### Notifications (`test_notifications.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| N-BE-01 | List notifications for user | 200, tenant-scoped |
| N-BE-02 | Mark one read | read_at set |
| N-BE-03 | Mark all read | all unread cleared |
| N-BE-04 | WO request creates notification row for admin | type=`work_order.requested` |

### Invoice preview (`test_invoice_preview.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| I-BE-01 | Preview verified WO | labor/parts/total returned, no invoice row |
| I-BE-02 | Preview unverified WO | 400 |
| I-BE-03 | Send invoice emails PDF when SMTP configured | status=sent |

### Assets / schedules (`test_asset_schedules.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| A-BE-01 | Create schedule on asset | next_due_at computed |
| A-BE-02 | List assets sort=next_due | ordered ASC |
| A-BE-03 | Register asset generates label_code + qr_payload | unique per tenant |
| A-BE-04 | CSV import preview + commit | 10 rows inserted |

### Subscription (`test_subscription.py`)

| ID | Scenario | Expected |
|----|----------|----------|
| S-BE-01 | Suspended tenant API call | 403 SUBSCRIPTION_SUSPENDED |
| S-BE-02 | super_admin updates subscription | settings persisted |

---

## Frontend manual / E2E checklist

| ID | Area | Steps | Expected |
|----|------|-------|----------|
| N-01 | Notifications | Client submits WO request as client_admin | Admin bell shows unread; click opens review modal |
| N-02 | Notifications | Admin approves request | Client notified; persists after refresh |
| I-01 | Invoice | Generate from verified WO | Preview modal shows labor/parts before commit |
| I-02 | Invoice | Print + Send | PDF opens; send marks sent (email logged/SMTP) |
| A-01 | Assets | Register with schedule | Client asset list sorted by next due |
| A-02 | Smart label | Register asset | Label code + QR; printable sheet link |
| A-03 | CSV | Import 10 assets | Preview validation then success |
| H-01 | Hosting | Demo URL / docker compose up | Seed login works |
| S-01 | Subscription | Set tenant suspended | Login/API blocked with message |

---

## Regression

- All Phase 3 backend tests pass
- Phase 3 FE checklist FE-01–FE-08 still pass
- RBAC / tenant isolation unchanged

---

**Last updated:** June 2026
