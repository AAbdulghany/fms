# A3–A4 task board

**Branch:** `feature/a3-a4-parts-vat`  
**Note:** Subagent fan-out hit model usage limits; orchestrator completed PM/UX/Arch/QA docs and is implementing BE/FE.

| Track | Owner role | Issue | Deliverable | DoD |
|-------|------------|-------|-------------|-----|
| Program docs | Tech Lead | — | `docs/redesign/*` | Done |
| PRD | Product Manager | #36–38 | `PRD_A3_A4_PARTS_VAT.md` | Done |
| UX | UX Designer | #37 | `UX_A3_A4_PARTS_VAT_FLOWS.md` | Done |
| AgDR + design | Solution Architect | #36 | AgDR-A3 + tech design | Done |
| Scenarios | QA Engineer | #38 | Sprint cycle + E2E skeletons | In progress |
| BE | Backend Engineer | #36 | TaxProfile, WO parts, VAT compute, tests | In progress |
| FE | Frontend Engineer | #37 | Billing pages + WO parts panel + i18n | In progress |
| Review | Rex + Hakim | PR | Approve before merge | Pending |

## Dependencies

```text
AgDR-A3 → BE migration/VAT → FE Tax/Invoice UI
BE WorkOrderPart API → FE WO panel → E-BILL-01
Catalog APIs (exist) → FE Pricing/Contracts pages
```
