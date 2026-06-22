# Wave 4 — Full Test Case Matrix

**Purpose:** Full-tier traceability (see [TEST_STRATEGY.md](TEST_STRATEGY.md)).  
**Legend:** ✅ automated · 🟡 partial · ⬜ planned · 🔵 manual only · ⏭ deferred

---

## Golden path — company to invoice (GP)

End-to-end business journey for **company_admin** unless noted.

| ID | Step | Role | Acceptance (pytest) | E2E | Status |
|----|------|------|---------------------|-----|--------|
| **GP-01** | Login as company_admin | company_admin | — | ⬜ `wave4-golden-path` | ⬜ |
| **GP-02** | Create client company | — | — | **⏭ Skipped** | API setup only, not UI |
| **GP-03** | Add site on company detail | company_admin | `/companies/:id` Sites → + Add site | — | ⬜ |
| **GP-04** | Register asset on site (schedule monthly) | company_admin | `/assets` → Register | `test_wave4_schedule_anchor` | 🟡 |
| **GP-05** | Create work order for asset | company_admin | `/work-orders` → Create | — | ⬜ |
| **GP-06** | Assign WO → technician | company_admin | `/work-orders/:id` | — | ⬜ |
| **GP-07** | Technician → in_progress | technician | `test_report_in_progress` | ⬜ | 🟡 |
| **GP-08** | Fill + submit maintenance report (labor hours) | technician | `test_report_in_progress` | ⬜ | 🟡 |
| **GP-09** | Mark completed → verified (approve report) | company_admin | `test_report_in_progress` | ⬜ | 🟡 |
| **GP-10** | Invoice preview shows labor + currency | company_admin | `test_invoice_computation` | ⬜ INV-05 | 🟡 |
| **GP-11** | Generate invoice | company_admin | `test_invoice_computation` | ⬜ INV-01 | 🟡 |
| **GP-12** | Download PDF + send invoice | company_admin | `test_maintenance_report_pdf` | ⬜ INV-03,06 | 🟡 |

**GP pass criteria:** GP-01 through GP-12 green in one Playwright run **or** sign-off with split specs + backend coverage noted.

---

## Invoice module (INV)

| ID | Scenario | Acceptance | E2E | Status |
|----|----------|------------|-----|--------|
| INV-01 | Generate from verified WO | `test_invoice_computation` | ⬜ | 🟡 |
| INV-02 | Edit draft billing fields | — | ⬜ | ⬜ |
| INV-03 | Download invoice PDF | `test_maintenance_report_pdf` | ⬜ | 🟡 |
| INV-04 | Tenant without `invoices` feature | `test_wave4_invoices` | ⬜ | 🟡 |
| INV-05 | Preview before generate | `test_invoice_computation` | ⬜ | 🟡 |
| INV-06 | Approve / send workflow | — | ⬜ | ⬜ |

---

## Work order workflow (WO)

| ID | Scenario | Acceptance | E2E | Status |
|----|----------|------------|-----|--------|
| WO-01 | Report editable at in_progress | `test_report_in_progress` | ⬜ GP-07,08 | ✅ / ⬜ |
| WO-02 | REPORT_REQUIRED on complete | `test_report_in_progress` | ⬜ | ✅ |
| WO-03 | Hold reason modal | — | ⬜ | ⬜ |
| WO-04 | Assignee required | — | ⬜ | ⬜ |
| WO-05 | Schedule anchor from install date | `test_wave4_schedule_anchor` | ⬜ | ✅ |

---

## Friendly errors (ERR)

| ID | Raw code | User must see (EN) | i18n key | Status |
|----|----------|-------------------|----------|--------|
| ERR-01 | `FEATURE_NOT_AVAILABLE` | "This feature is not included in your subscription." | `error_feature_not_available` | ⬜ NT-131 |
| ERR-02 | `NOT_FOUND` | "The requested item was not found." | `error_not_found` | ⬜ |
| ERR-03 | `FORBIDDEN` | "You don't have permission for this action." | `error_forbidden` | ⬜ |
| ERR-04 | `EMAIL_ALREADY_IN_USE` | "This email is already registered." | `error_email_already_in_use` | ⬜ |
| ERR-05 | `CODE_IN_USE` | "This company code is already in use." | `error_code_in_use` | ⬜ |
| ERR-06 | `INVALID_TRANSITION` | "This status change is not allowed." | `error_invalid_transition` | ⬜ |
| ERR-07 | `REPORT_REQUIRED` | (existing) | `error_report_required` | ✅ |
| ERR-08 | `HOLD_REASON_REQUIRED` | (existing) | `error_hold_reason_required` | ✅ |
| ERR-09 | `ASSIGNEE_REQUIRED` | (existing) | `error_assignee_required` | ✅ |
| ERR-10 | `CANCELLATION_REASON_REQUIRED` | (existing) | `error_cancellation_reason_required` | ✅ |
| ERR-11 | `INVALID_ASSIGNEE` | "Selected user cannot be assigned to this work order." | `error_invalid_assignee` | ⬜ |
| ERR-12 | `ASSET_RETIRED` | "This asset is retired and cannot be modified." | `error_asset_retired` | ⬜ |

Full catalog target: **~40 codes** — track in NT-131.

---

## Regression scope (always run)

| Suite | Command | Tier |
|-------|---------|------|
| Backend all | `cd backend && pytest -q` | Regression |
| Wave 4 slice | `pytest tests/test_wave4_* tests/test_invoice_* tests/test_billing_* tests/test_report_* tests/test_maintenance_report_pdf.py` | Acceptance + Regression |
| Frontend | `npm run build` | Regression |
| E2E wave 3+4 | `npx playwright test tests/e2e/` | E2E |
