# Orbit redesign — customer requirements programs

**Source:** Customer Requirements Roadmap (locked defaults, 2026-10).  
**Active delivery:** Program A slice **A3–A4** (Parts catalog + WO consumption + TaxProfile VAT).  
**Branch:** `feature/a3-a4-parts-vat`

This folder is the program-level documentation home for the redesign. Slice PRDs and sprint cycles also live under [`docs/product/`](../product/) and [`docs/engineering/cycles/`](../engineering/cycles/).

| Document | Purpose |
|----------|---------|
| [ROADMAP.md](./ROADMAP.md) | Phasing, sprint map, risks, AgDR backlog |
| [PROGRAM_A.md](./PROGRAM_A.md) | Core CMMS — verticals, QR, parts, VAT, downtime |
| [PROGRAM_B.md](./PROGRAM_B.md) | Ops intelligence — worker, SLA, KPI, WhatsApp |
| [PROGRAM_C.md](./PROGRAM_C.md) | AI SKU + Asset Health Twin (data-gated) |
| [CUSTOMER_COMMITMENT.md](./CUSTOMER_COMMITMENT.md) | What we commit vs roadmap vs priced add-on |
| [A3_A4_PARTS_VAT.md](./A3_A4_PARTS_VAT.md) | Active slice brief (links to PRD / AgDR / tickets) |
| [PROGRAM_A_COMPLETION_REPORT.md](./PROGRAM_A_COMPLETION_REPORT.md) | Done vs missing for A1–A4 |
| [AUTOMATION_PLAN_1_PM_SERIES.md](../engineering/AUTOMATION_PLAN_1_PM_SERIES.md) | PM calendar until EOL + next-action WO chain (auto-assign deferred) |

## Locked defaults

- **Tax:** per-tenant configurable VAT/rate + rounding in Program A; **ETA/ZATCA e-invoice = priced add-on** (not first ~6 months).
- **Digital Twin:** **Asset Health Twin** only in this package (status, risk, PM due, history). Full BIM/IoT twin = separate undated initiative.
- **Team:** ~2 engineers, 2-week sprints.
- **STT:** mic → description is speech-to-text, not TTS.

## Status (GitHub)

| Slice | Issues | State |
|-------|--------|-------|
| A1 Verticals + AssetTypes | #28–#30 | Closed (PR #31) |
| A2 Asset QR | #32–#34 | Closed (PR #35) |
| A3–A4 Parts + VAT | [#36](https://github.com/AAbdulghany/fms/issues/36)–[#38](https://github.com/AAbdulghany/fms/issues/38) | Active |

## Agile flow (this slice)

```text
Head of Product / PO  →  Product Manager (PRD + AC)
        ↓
   UX Designer (flows)
        ↓
Solution Architect (AgDR TaxProfile) + Tech Lead (task split)
        ↓
Backend Engineer  ‖  Frontend Engineer
        ↓
   QA Engineer (acceptance / E2E scenarios)
        ↓
Rex + Hakim → merge
```
