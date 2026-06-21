# Wave 4 Ticket Tracker — Invoices & Workflows

**Started:** 2026-06-22  
**Branch:** `feature/phase-3-restructure/wave4`  
**Gate:** Wave 3 merged ([PR #18](https://github.com/AAbdulghany/fms/pull/18))  
**Spec:** [03_wave4_mega_prompt.md](../knowledge-hub/product/03_wave4_mega_prompt.md)  
**E2E plan:** [WAVE4_E2E.md](WAVE4_E2E.md) (INV-01–INV-06)

---

## Parallel lane assignment

| Lane | Agent | Tickets | Status |
|------|-------|---------|--------|
| A WO workflow | backend-engineer + frontend-engineer | NT-122 | ✅ Done |
| B Invoice validation | backend-engineer | NT-123 | ✅ Done |
| C Branded PDFs | backend-engineer | NT-124, NT-125 | ✅ Done |
| D Feature gate | backend-engineer + frontend-engineer | NT-126 | ✅ Done |
| E QA + E2E | qa-engineer | NT-127 | 🟡 Partial — backend tests + E2E plan; Playwright deferred |

---

## Tickets

| Ticket | Title | Agent | Depends | Status | Tests |
|--------|-------|-------|---------|--------|-------|
| **NT-122** | WO workflow simplification (report before complete, FSM payloads) | BE + FE | Wave 3 | ✅ | `test_report_in_progress.py`, `test_wave4_schedule_anchor.py` |
| **NT-123** | Invoice validation at generate (billing fields, labor hours) | backend-engineer | NT-122 | ✅ | `test_invoice_computation.py`, `test_billing_setup.py` |
| **NT-124** | Branded PDF mandatory fields (invoice + maintenance report) | backend-engineer | NT-123 | ✅ | `test_maintenance_report_pdf.py` |
| **NT-125** | PDF SW copyright watermark (platform_settings) | backend-engineer | NT-124 | ✅ | `test_maintenance_report_pdf.py` (watermark assert) |
| **NT-126** | Enforce `invoices` feature gate (API + nav + routes) | BE + FE | NT-108 | ✅ | `test_wave4_invoices.py` + FE `FeatureRoute` |
| **NT-127** | Invoice module QA (INV-01–INV-06) | qa-engineer | NT-122–126 | 🟡 | Backend 25/25 wave4 tests; E2E spec planned |

---

## Acceptance criteria (summary)

### NT-122
- [x] Report editor unlocked at `in_progress` / `on_hold` (Architect A2)
- [x] `REPORT_REQUIRED` blocks → `completed` until report submitted
- [x] Transition payloads: assignee, hold_reason, cancellation_reason (A3)
- [x] Schedule anchor from `installed_on` when no last maintenance (A1)

### NT-123
- [x] Generate invoice requires verified WO + approved report + labor hours
- [x] Billing setup fields validated (email, currency, tax rate)
- [x] Draft invoice recalculation on charge edits

### NT-124
- [x] Invoice PDF: tenant branding, line items, currency, dates
- [x] Maintenance report PDF: bilingual AR/EN, template schema sections
- [x] Arabic shaping via `arabic_utils` + embedded fonts

### NT-125
- [x] Platform copyright watermark on invoice PDF footer
- [x] Watermark sourced from `DEFAULT_BRANDING["copyright_watermark"]` / platform settings

### NT-126
- [x] `require_feature("invoices")` on invoice + billing-action routes
- [x] Sidebar hides invoices nav when feature absent
- [x] `/invoices` routes wrapped in `FeatureRoute feature="invoices"`

### NT-127
- [x] Backend regression suite for invoice/billing/PDF paths
- [ ] Playwright `wave4-invoices.spec.ts` (INV-01–06) — deferred to follow-up PR
- [x] E2E plan documented in [WAVE4_E2E.md](WAVE4_E2E.md)

---

## Deliverables checklist

| Area | Expected paths | Status |
|------|----------------|--------|
| Backend FSM | `work_order_fsm.py`, `report_validation.py` | ✅ |
| Backend billing | `billing.py`, `billing_setup.py`, `billing_actions.py` | ✅ |
| Backend PDF | `invoice_pdf.py`, `maintenance_report_pdf.py`, `pdf_brand.py`, fonts | ✅ |
| Backend reports | `report_context.py`, `report_schema_resolve.py`, template sync | ✅ |
| Frontend | `WorkOrderDetailPage.tsx`, `InvoicesPage.tsx`, `InvoicePreviewModal.tsx` | ✅ |
| Feature gate FE | `App.tsx`, `Sidebar.tsx` | ✅ |
| Tests | `test_wave4_*.py`, `test_invoice_computation.py`, `test_billing_setup.py`, etc. | ✅ 25/25 |
| Docs | This file, `WAVE4_E2E.md`, mega prompt status | ✅ |

---

## Known gaps / follow-up

| ID | Gap | Owner | Notes |
|----|-----|-------|-------|
| NT-P2-W03 | WO lifecycle RBAC UI hints (partial) | FE | FSM backend complete; dropdown hints optional |
| NT-127 | Playwright INV-01–06 | qa-engineer | Backend coverage sufficient for wave merge; E2E in next sprint slice |

---

## Test evidence

```text
Wave 4 backend: 25/25 passed (2026-06-22)
  test_wave4_invoices.py          3
  test_invoice_computation.py     3
  test_billing_setup.py           2
  test_wave4_schedule_anchor.py   9
  test_maintenance_report_pdf.py  3
  test_report_in_progress.py      5
Frontend:       npm run build — pending CI
E2E:            0/6 Playwright (plan only)
```

---

## PR order (this wave)

```
NT-122 → NT-123 → NT-124 → NT-125 → NT-126 → NT-127 (docs + tests)
```

---

## Next wave

Wave 5 (`feature/phase-3-restructure/wave5`) opens after Wave 4 merge + sign-off.
