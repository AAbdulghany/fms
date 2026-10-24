# A3–A4 sprint cycle — Parts + VAT

**Program:** Orbit Program A, slices A3–A4  
**Date opened:** 2026-10-24  
**Status:** In progress  
**Branch:** `feature/a3-a4-parts-vat`  
**Tickets:** [#36](https://github.com/AAbdulghany/fms/issues/36) BE · [#37](https://github.com/AAbdulghany/fms/issues/37) FE · [#38](https://github.com/AAbdulghany/fms/issues/38) QA  
**AgDR:** [AgDR-A3-tax-profile.md](../AgDR-A3-tax-profile.md)  
**Design:** [A3_A4_PARTS_VAT_TECH_DESIGN.md](../designs/A3_A4_PARTS_VAT_TECH_DESIGN.md)  
**PRD:** [PRD_A3_A4_PARTS_VAT.md](../../product/PRD_A3_A4_PARTS_VAT.md)  
**Task board:** [A3_A4_TASK_BOARD.md](./A3_A4_TASK_BOARD.md)

---

## 1. Done means

- [ ] TaxProfile default + CRUD; tax no longer hardcoded 0
- [ ] WorkOrderPart attach → invoice parts lines
- [ ] Snapshot on invoice create; profile edit does not change old invoices
- [ ] Admin UI: parts, tax, pricing, contracts
- [ ] Unit/API + E2E scenarios below green or skip-wired with ticket note

---

## 2. Unit / API tests

| ID | Test |
|----|------|
| U-TAX-01 | Default TaxProfile 15% exclusive created for new tenant |
| U-TAX-02 | Exclusive 15%: subtotal 1000 → tax 150 → total 1150 |
| U-TAX-03 | Rate 0%: tax 0, total = subtotal |
| U-TAX-04 | Inclusive 15%: tax extracted; total equals pre-tax display contract (documented) |
| U-TAX-05 | Rounding HALF_UP on fractional fils/halalas |
| U-TAX-06 | Invoice metadata contains tax_profile snapshot |
| U-TAX-07 | After profile rate change, existing invoice tax_sar unchanged |
| U-TAX-08 | Cross-tenant cannot GET/PATCH other tenant TaxProfile |
| U-PART-01 | Create part SKU unique per tenant |
| U-PART-02 | Attach WorkOrderPart qty; list on WO |
| U-PART-03 | Invoice prefers WorkOrderPart over empty parts_used |
| U-PART-04 | Report parts_used still works when no WorkOrderPart rows |
| U-PART-05 | Cross-tenant cannot attach part from another tenant |

---

## 3. E2E (Playwright)

| ID | Scenario |
|----|----------|
| E-BILL-01 | Admin creates part → opens WO → adds part qty → (after approve path) invoice tax > 0 |
| E-BILL-02 | Admin sets TaxProfile 15% → new invoice shows tax line |
| E-BILL-03 | Change TaxProfile to 0% → previously issued invoice still shows old tax |
| E-BILL-04 | Pricing profile + contract create via UI |
| E-BILL-05 | Other tenant session cannot see parts list of tenant A |

---

## 4. Review gate

QA pack (#38) reviewed by Tech Lead before marking E2E unskipped.
