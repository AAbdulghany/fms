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
| E QA + E2E | qa-engineer | NT-127, NT-132, NT-133 | 🟡 In progress |
| F UX errors | frontend-engineer + backend-engineer | NT-131 | ⬜ Planned |

---

## Tickets

| Ticket | Title | Agent | Depends | Status | Tests |
|--------|-------|-------|---------|--------|-------|
| **NT-122** | WO workflow simplification (report before complete, FSM payloads) | BE + FE | Wave 3 | ✅ | `test_report_in_progress.py`, `test_wave4_schedule_anchor.py` |
| **NT-123** | Invoice validation at generate (billing fields, labor hours) | backend-engineer | NT-122 | ✅ | `test_invoice_computation.py`, `test_billing_setup.py` |
| **NT-124** | Branded PDF mandatory fields (invoice + maintenance report) | backend-engineer | NT-123 | ✅ | `test_maintenance_report_pdf.py` |
| **NT-125** | PDF SW copyright watermark (platform_settings) | backend-engineer | NT-124 | ✅ | `test_maintenance_report_pdf.py` (watermark assert) |
| **NT-126** | Enforce `invoices` feature gate (API + nav + routes) | BE + FE | NT-108 | ✅ | `test_wave4_invoices.py` + FE `FeatureRoute` |
| **NT-127** | Invoice module QA (INV-01–INV-06) | qa-engineer | NT-122–126 | 🟡 | Backend 25/25; Playwright suite B |
| **NT-131** | User-friendly error messages (no raw codes in UI) | FE + BE | NT-122 | 🟡 | Catalog + handler + invoice/WO pages; ~30 codes remain |
| **NT-132** | Golden path E2E: company → invoice (GP-01–GP-12) | qa-engineer + FE | NT-127 | 🟡 | Spec scaffold `wave4-golden-path.spec.ts` |
| **NT-133** | Test strategy: acceptance / regression / E2E / full matrix | qa-engineer + tech-lead | — | ✅ | [TEST_STRATEGY.md](TEST_STRATEGY.md) + matrix |

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
- [ ] Playwright suite B `wave4-invoices.spec.ts` (INV-01–06)
- [x] E2E plan documented in [WAVE4_E2E.md](WAVE4_E2E.md)

### NT-131
- [ ] Central `resolveApiError()` — all pages use it (not raw `parseApiError` codes)
- [ ] i18n AR/EN for ~40 API error codes (see ERR table in full matrix)
- [ ] E2E spot-check: no `SCREAMING_SNAKE` visible in UI on forced errors
- [ ] API keeps stable machine codes for tests/logs (no breaking change)

### NT-132
- [ ] Playwright suite A GP-03–GP-12 (serial spec; GP-02 skipped)
- [ ] API fixture: `POST /clients` before GP-03 (company with 0 sites)
- [ ] **Separate flows GP-03–06:** company detail (site) → `/assets` → `/work-orders` → WO detail
- [ ] Unique company/site names per run (`E2E-{timestamp}`)
- [ ] Technician + company_admin role switch mid-journey (GP-07–09)
- [x] Navigation model documented in [WAVE4_E2E.md](WAVE4_E2E.md)

### NT-133
- [x] Four-tier model documented ([TEST_STRATEGY.md](TEST_STRATEGY.md))
- [x] Full matrix stub ([WAVE4_FULL_TEST_MATRIX.md](WAVE4_FULL_TEST_MATRIX.md))
- [ ] PR template + ticket tracker columns for tier mapping
- [ ] CI job labels acceptance vs regression vs E2E

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
| NT-127 | Playwright INV-01–06 | qa-engineer | Suite B in [WAVE4_E2E.md](WAVE4_E2E.md) |
| NT-131 | Friendly error messages | FE + BE | ~40 codes still show raw in many pages |
| NT-132 | Golden path E2E GP-03–12 | qa-engineer | GP-02 skipped; API setup + GP-03 add site |
| NT-133 | Test taxonomy docs | qa-engineer | Acceptance / regression / E2E / full matrix |

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
