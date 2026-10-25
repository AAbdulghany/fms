# Program A (A1–A4) — completion report / sprint signoff

**Date:** 2026-10-24  
**Branch:** `feature/a3-a4-parts-vat`  
**Signoff:** **Accepted for merge readiness** (A1–A4 product slices). A5 is the next sprint.  
**Clean seed:** `python -m app.cli.clean_dev_seed` (1 tenant · 1 hospital client · current roles)

---

## Executive summary

| Slice | Status | Notes |
|-------|--------|--------|
| **A1** Verticals + AssetTypes | **Done** | Create-if-missing on register; library + catalog; DEV clear-all |
| **A2** Asset QR | **Done** (merged #35) | Stickers A/C polish continued on this branch |
| **A3** Parts + WO consumption | **Done** | Bilingual catalog → Inventory; WO parts → invoice |
| **A4** Tax / commercial billing | **Done** | TaxProfile VAT + **Commercial Terms** (General + per-client); draft invoice recalculate |
| **A5** Downtime / failure codes | **Next** | Issues filed with this signoff |

---

## Sprint signoff checklist (A3–A4)

- [x] TaxProfile default + CRUD; tax no longer hardcoded 0
- [x] WorkOrderPart attach → invoice parts lines
- [x] Snapshot on invoice create; profile edit does not rewrite issued invoices
- [x] Admin UI: Inventory, Commercial Terms (merged pricing/tax/contracts)
- [x] Unit/API tests for tax + parts
- [ ] E2E E-BILL-* unskipped end-to-end (skeletons exist; backlog)

**Signoff decision:** Ship A3–A4 on PR from this branch. Residual items move to **backlog** below — they do **not** block A5 kickoff.

---

## Ticket map (this branch)

| Issue | Focus | Commit theme | State |
|-------|--------|--------------|--------|
| #28–#30 A1 | Closed | Shipped PR #31 | Done |
| #32–#34 A2 | Closed | Shipped PR #35 | Done |
| **#36** | BE WorkOrderPart, TaxProfile, VAT | `feat(#36): …` | Implemented — close after PR merge |
| **#37** | FE Inventory, Commercial Terms, WO parts | `feat(#37): …` | Implemented — close after PR merge |
| **#38** | QA acceptance + E2E | docs + e2e skeletons | Partial — E2E unskip backlog |
| **#39–#41** | A5 downtime / codes / history / role labels | Implemented (migration `b9c0d1e2f3a4`) | In progress / ready for PR |

---

## Backlog (post A3–A4 signoff)

| Item | Severity | Target |
|------|----------|--------|
| A5 downtime start/end + failure/symptom codes + WO history | High | **Implemented** (#39–#41) |
| Role display naming (Platform Super Admin / Tenant roles / Client) | Medium | **Done** (EN/AR i18n + RBAC hub; no permission rewrite) |
| Unskip E2E E-BILL-01…05 after seed WO→invoice path | Medium | #38 follow-up |
| Stock ledger (`StockMovement`) | Low | A3b optional |
| ZATCA / ETA e-invoice | Out of scope | Priced add-on |
| AssetType `default_report_template_id` often null after adopt | Medium | A1 polish |
| PM auto-assign (#1b) | Deferred | Needs geo/workload data |

---

## How to reset local DEV DB

```powershell
cd E:\03Workset\fms\backend
..\.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
..\.\.venv\Scripts\python.exe -m app.cli.clean_dev_seed
```

**Login (suffix `123`):** `admin@demo.com` / `admin123` (and other role emails from seed printout).
