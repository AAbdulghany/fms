# Wave 4 E2E Test Plan — Invoices (Playwright)

**Branch:** `feature/phase-3-restructure/wave4`  
**Owner:** qa-engineer (NT-127)  
**Tool:** Playwright (see [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md))  
**Seed:** pitch demo (`admin@demo.com`, `super@demo.com`)

---

## Scenarios (INV-01 – INV-06)

| ID | Role | Scenario | Pass criteria |
|----|------|----------|---------------|
| **INV-01** | company_admin | Generate invoice from verified WO | Invoice created; appears on list |
| **INV-02** | company_admin | Invoice detail edit draft fields | billing_email, dates, currency persist |
| **INV-03** | company_admin | Download invoice PDF | PDF returns 200; contains tenant + platform names |
| **INV-04** | company_admin | Tenant **without** `invoices` feature | Nav hidden OR 403 on direct URL |
| **INV-05** | company_admin | Invoice preview before generate | Preview shows labor hours + currency |
| **INV-06** | company_admin | Approve / send invoice workflow | Status transitions draft → approved → sent |

---

## Implementation status

| ID | Automated | File | Status |
|----|-----------|------|--------|
| INV-01 | ⬜ | `wave4-invoices.spec.ts` | Planned — backend covered by `test_invoice_computation.py` |
| INV-02 | ⬜ | ↑ | Planned |
| INV-03 | ⬜ | ↑ | Planned — PDF smoke in `test_maintenance_report_pdf.py` |
| INV-04 | ⬜ | ↑ | Planned — backend `test_wave4_invoices.py` |
| INV-05 | ⬜ | ↑ | Planned |
| INV-06 | ⬜ | ↑ | Planned |

NT-127 closes when all rows are ✅ or explicitly deferred with sign-off note.
