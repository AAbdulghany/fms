# AgDR: Phase 3.1 Assets & Smart Labels

**Status:** Approved for Build  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Context

`MaintenanceSchedule` model exists without API/UI. Assets lack human-readable labels and client-facing maintenance sort.

## Decision — Option B (balanced)

### M3a Maintenance scheduling

- CRUD: `POST/GET /assets/{id}/schedules`
- Frequency: monthly, quarterly, yearly, custom days
- Template required when schedule enabled
- Background job: `next_due_at <= now()` → create preventive WO with linked template

### M3b Smart labels

| Field | Format | Example |
|-------|--------|---------|
| `label_code` | `{SITE_CODE}-{CATEGORY}-{SEQ}` | `HQ-HVAC-014` |
| `qr_payload` | URL `/assets/{id}` (relative or demo base URL) | Deep link to detail |

Print: `GET /assets/{id}/label-sheet` returns PDF with QR + label + next due.

**Not in 3.1:** NFC, Zebra SDK (Phase 4).

### M3c Client experience

- `GET /assets?view=maintenance&sort=next_due`
- Default sort: overdue first, then `next_due_at ASC`
- Filters: overdue / due this week / due this month
- Detail page: schedule timeline, WO history

### M4 CSV import

Columns: site_code, name, category, serial, installed_on, schedule_frequency, template_code.  
Idempotency: skip duplicate serial per site.

## Constraints

- `label_code` unique per tenant
- Schedule template must belong to same tenant
- Site manager scoped to assigned sites
