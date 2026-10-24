# Program B — Ops intelligence

**Customer promise:** SLA clocks, engineer/technician KPIs, WhatsApp notify + human-triaged intake.  
**Window:** S7–S12 (~12 weeks).  
**Depends on:** Program A (especially A5 data quality) + B0 foundations.

## Slices

### B0. Foundations — before WhatsApp / AI

- Postgres job queue + worker (same image), object storage, `WorkOrderEvent` stream, permission layer.
- Required by vision.md for new runtime. AgDRs: queue choice, object storage.

### B1–B2. SLA + KPI

- `SlaPolicy` + business calendar → fill existing `sla_*_due_at`; breach jobs → notifications.
- Dashboards: SLA %, MTTR, cycle time, **per engineer/technician** vs similar WO class (category × vertical × urgency).
- Materialized views refreshed by worker.

### B3. “Predict issues” v0 — rules, not ML

- Risk score from age, repair count, repeat failures, overdue PM (explainable). Feeds Health Twin later.

### B4. WhatsApp — staged

1. Outbound templates (assigned / status) via Cloud API or KSA-friendly BSP.
2. Inbound → ServiceRequest / WO request queue (**human triage** — never auto-create WO).
3. Start Meta Business verification early (external lead time) — parallel to S1 historically; still open.

## Hardness notes

- Multi-tenant `phone_number_id` → tenant mapping.
- Single-process WebSocket + no worker today → B0 first.
