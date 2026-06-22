# Phase 3.1 — Frontend Engineer Prompt

**Role:** Senior Frontend Engineer  
**Framework:** RCCF

## Context

Phase 3.1 backend APIs for notifications, invoices, assets, subscription. Wire UI per AgDRs.

## Tasks

### M1 Notifications
- `NotificationContext`: hydrate from `GET /notifications`, PATCH on read
- `NotificationBell`: route by type/action to review modal or WO detail
- `WorkOrdersPage`: `?review={woId}` opens review modal
- Remove template selector from WO create/request modals

### M2 Invoice
- `InvoicePreviewModal` before generate
- Print button → open PDF inline
- Send with confirmation (billing email)

### M3 Assets
- Schedule fields in `AssetRegisterModal` + detail page
- Client `AssetsPage`: sort by next due, filters
- Label sheet print link

### M4 CSV
- Import modal: upload → preview table → confirm

### M6 Subscription
- `SubscriptionPage` for super_admin (or section in settings)
- Handle 403 subscription suspended gracefully

## Constraints

- i18n AR/EN for new strings
- RTL-safe layouts
- Use existing `apiFetch` patterns

## Verification

Manual checklist N-01 through S-01 in `PHASE3.1_TEST_PLAN.md`.
