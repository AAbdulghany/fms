# AgDR: Phase 3.1 Invoice Cycle

**Status:** Approved for Build  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Context

Invoices can be generated from verified WOs but there is no pre-flight preview. `POST /invoices/{id}/send` sets status without emailing the PDF.

## Decision

### Preview-first flow

1. Admin selects verified WO → **preview modal** (labor, parts, fees, totals, work summary).
2. Confirm → `POST /work-orders/{id}/generate-invoice`.
3. Post-create: **Print** (inline PDF) or **Send** (email with attachment).

### New endpoint

`GET /work-orders/{id}/invoice-preview` — wraps billing logic from `build_invoice_for_work_order` without persisting.

### PDF enhancements

| Section | Source |
|---------|--------|
| Header | Tenant name, invoice number, dates |
| Bill-to | Client legal name, billing_email |
| Reference | WO id, title, site, asset, completed dates |
| Line items | labor, parts, fee, surcharge |
| Work performed | Report summary + technician |
| Footer | Payment terms, currency note |

### Send email

Extend SMTP helper to attach PDF bytes. Recipient = `client.billing_email` (override optional in future).

### Template on WO create

UI removes template selector from direct create/request. Templates attach at schedule or report fill time (M3).

## Labor override

Deferred: editable labor override with audit trail → Phase 4 if needed.

## NFRs

- Preview response < 500ms for typical WO
- PDF generation < 3s
- Send is idempotent-safe (re-send allowed with warning in UI)
