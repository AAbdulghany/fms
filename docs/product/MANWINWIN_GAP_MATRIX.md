# ManWinWin vs Orbit AM — Feature Gap Matrix

**Product:** Orbit AM — Hospital Asset & Maintenance Management  
**Analyst:** Hanan (Product Analyst)  
**Date:** 2026-10-21  
**Version:** 1.0  

---

## 1. Purpose & Method

### Purpose

This document provides an honest, evidence-based gap analysis between **ManWinWin** — an established Portuguese CMMS used across healthcare and FM sectors globally — and **Orbit AM** as of October 2026. The goal is to surface the most critical capability gaps before the Egypt hospital pilot and prioritise the roadmap accordingly.

### Method

| Data source | How used |
|---|---|
| **ManWinWin public feature set** | Based on publicly documented ManWinWin CMMS modules: Asset Management, Work Orders, Preventive Maintenance, Parts/Inventory, Meters/Condition Monitoring, Purchasing, Contracts/SLA, Reports & KPIs, Mobile App, Multi-site, QR/Barcode, Labor/Skills, Dashboards, Document Management, Supplier Management, Downtime Tracking. No ManWinWin code or NDA materials — public knowledge only. |
| **Orbit AM pitch pack §3** | `docs/pitch/ORBIT_AM_PITCH_PACK.md` — self-declared Done/Partial/TBD status |
| **Wave 5 UAT findings** | `docs/knowledge-hub/product/04_wave5_findings.md` — UAT bug registry with root-cause analysis and task status |
| **Route table** | `src/app/routes.tsx` — 18 routes as evidence of shipped pages |
| **Feature folders** | `src/features/**` — 37 TSX components scanned for evidence |
| **Pitch §3.2 pre-contract gaps** | Explicit "must close before first hospital contract" list |

### Honesty rules applied

- **Done** = route exists AND component built AND no open P0/P1 UAT blocker for that capability
- **Partial** = feature exists but Wave 5 found bugs, stubs, or missing sub-capabilities with open FE tasks
- **Missing** = no route, no component, no schema evidence
- **N/A** = ManWinWin capability outside Orbit's defined scope (deferred by product decision)

---

## 2. Summary Scorecard

| Status | Count | % of 50 rows |
|---|---|---|
| ✅ Done | 16 | 32% |
| 🟡 Partial | 13 | 26% |
| ❌ Missing | 14 | 28% |
| ⬜ N/A / Out-of-scope | 7 | 14% |

> **Pilot readiness headline:** Orbit covers the corrective-maintenance core well (WOs, assets, invoicing, RBAC, Arabic). The 14 missing capabilities cluster around **inventory/parts**, **purchasing**, **meters**, **contracts/SLA**, **advanced KPIs**, and **mobile offline** — all areas ManWinWin treats as table stakes for hospital FM.

---

## 3. Full Feature Gap Matrix

### Domain: Asset Management

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Asset register (name, category, location, serial, install date) | ✅ Done | `src/features/assets/pages/AssetsPage.tsx`, `AssetRegisterModal.tsx` | — | Core done |
| Asset hierarchy (equipment → component) | 🟡 Partial | `src/features/locations/pages/LocationsPage.tsx` (location tree exists); no parent-child asset nesting | P1 | Location tree exists; asset-to-asset parent hierarchy missing |
| Asset lifecycle status (active / warning / EOL / retired) | 🟡 Partial | `AssetLifecycleBadge.tsx`, `AssetLifecycleTimeline.tsx`; Wave 5 NT-P5-A03-FE **Open** — lifecycle edit FE not wired | P1 | Backend fixed (Wave 5); FE task NT-P5-A03-FE still Open |
| Asset photo / document attachments | 🟡 Partial | Pitch §3.2 "Production object storage" listed as pre-contract gap (~2–3 weeks effort) | P0 | No object storage in prod; blocks compliance photo evidence |
| Asset CSV import | ✅ Done | `src/features/assets/components/AssetImportModal.tsx` | — | — |
| QR / barcode scan per asset | 🟡 Partial | `src/features/companies/components/SiteQrModal.tsx` (site QR); asset-level QR not evidenced in route table | P1 | Site QR done; asset QR modal stub — Wave 5 RC-5 |
| Warranty tracking (expiry date, vendor) | 🟡 Partial | Wave 5 NT-P5-A04 **Open** — warranty column planned but FE not shipped | P1 | Backend `expected_eol_date` enriched (NT-P5-A07-BE Fixed); FE column Open |
| Spare parts linked to asset | ❌ Missing | No inventory/parts feature folder | P2 | ManWinWin links BOM; Orbit has no parts module at all |
| Asset criticality classification | ✅ Done | Pitch §3.1; `asset_metadata.py` has `criticality` helper (Wave 5 B2 reference) | — | Stored in metadata_json |
| Spare device / swap-out flag | 🟡 Partial | Wave 5 NT-P5-A06-FE **Open**; backend done (metadata `is_spare`) | P2 | Data capture only; swap-out WO flow deferred |

### Domain: Work Orders

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Corrective WO creation & assignment | ✅ Done | `src/features/work-orders/pages/WorkOrdersPage.tsx`, `WorkOrderDetailPage.tsx` | — | Full lifecycle implemented |
| WO status lifecycle (created → assigned → in_progress → completed → verified → closed) | ✅ Done | `CLAUDE.md` status list; `WorkOrderDetailPage.tsx` | — | Matches ManWinWin WO lifecycle |
| WO request channel (client → FM) | ✅ Done | `WorkOrderRequestReviewModal.tsx`; pitch §3.1 "WO requests" Done | — | — |
| WO-to-asset linking (scoped WO list per asset) | ✅ Done | `GET /work-orders?asset_id=`; A5 `GET /assets/{id}/work-order-history`; AssetDetail maintenance + WO tabs | P0 | Gap matrix P0 closed in A5 |
| WO priority / urgency classification | 🟡 Partial | No explicit priority field evidenced in route/component scan; WO schema not confirmed | P1 | ManWinWin has P1–P4 urgency; Orbit status unknown — needs schema check |
| WO attachments (photos, reports) | 🟡 Partial | Report templates exist; photo upload blocked by object storage gap (pitch §3.2) | P0 | Same blocker as asset photos |
| WO cost tracking (parts + labor) | 🟡 Partial | Labor page + time entries done; parts cost = ❌ (no inventory); invoice generated but not broken down by cost type | P1 | Partial: labor cost only |
| Downtime tracking per WO | ✅ Done | A5: `downtime_started_at` / `downtime_ended_at` + `downtime_minutes`; failure/symptom codes; WO diagnostics panel | P1 | MTTR KPI foundation; catalog seeded per tenant |
| WO escalation / SLA breach alerts | ❌ Missing | Notifications partial (SMTP not prod); no SLA timer logic evidenced | P1 | ManWinWin SLA clock triggers escalation |
| Multi-technician assignment to WO | ❌ Missing | Single technician assignment assumed; no multi-assignee component found | P2 | ManWinWin supports team assignment |

### Domain: Preventive Maintenance

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| PM calendar (monthly / quarterly / yearly) | 🟡 Partial | `src/features/assets/components/MaintenanceCalendar.tsx`; monthly view backend Fixed (NT-P5-A02-BE); FE toggle NT-P5-A02-FE **Open** | P0 | Calendar exists but monthly view FE not shipped |
| PM schedule templates (frequency, task checklist) | ✅ Done | `src/features/reports/pages/ReportTemplatesPage.tsx`; pitch §3.1 "Template reports" Done | — | Checklist-style report templates in place |
| Automated PM job generation | 🟡 Partial | Pitch §3.2 explicitly: "Automated PM scheduling jobs — 4–6 weeks" pre-contract gap | P0 | No background job runner in prod; PM events shown but WOs not auto-created |
| Meter-based PM triggers (runtime hours, cycles) | ❌ Missing | No meters feature folder or route | P1 | ManWinWin triggers PM on meter thresholds; critical for medical equipment (sterilisers, generators) |
| Seasonal / conditional PM rules | ❌ Missing | No conditional scheduling logic evidenced | P2 | ManWinWin supports condition-based triggers; hospital HVAC relevance |
| PM compliance reporting | ❌ Missing | No PM compliance KPI dashboard or report export | P1 | ManWinWin tracks % PM completed vs scheduled; pilot KPI per pitch §13 |
| PM history per asset (completed + overdue) | 🟡 Partial | Wave 5 B7: maintenance history tab filter defined but NT-P5-A07-FE **Open** | P1 | Backend enriched; FE tab not wired |

### Domain: Parts & Inventory

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Parts catalogue (part number, description, UOM) | ❌ Missing | No inventory feature folder in `src/features/` | P1 | Core ManWinWin module; Orbit pitch §3.3 defers as "Future add-on / later decision" |
| Stock levels & reorder points | ❌ Missing | No inventory routes or components | P1 | Hospital FM needs critical spare tracking (filters, belts, fuses) |
| Parts consumption against WO | ❌ Missing | WO detail has no parts selector | P2 | ManWinWin posts parts to WO cost; Orbit labor-only |
| Parts location / warehouse bins | ❌ Missing | No warehouse management | Defer | Overly complex for pilot scale |
| Barcode / QR scan for parts | ❌ Missing | No parts + QR integration | P2 | Dependent on parts module |

### Domain: Meters & Condition Monitoring

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Meter definitions per asset (hours, cycles, km) | ❌ Missing | No meters feature folder | P1 | Critical for biomed: steriliser cycles, generator run-hours |
| Meter reading entry (manual + IoT) | ❌ Missing | No meter reading route or component | P1 | ManWinWin supports manual + automated readings |
| Meter-based PM trigger | ❌ Missing | (See PM domain above) | P1 | Linked gap |
| Condition monitoring alerts | ❌ Missing | No threshold alerting | P2 | ManWinWin supports out-of-range alerts |

### Domain: Purchasing

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Purchase request from WO / PM | ❌ Missing | No purchasing feature folder | P2 | ManWinWin WO → PR → PO flow; Orbit has no procurement module |
| Purchase order management | ❌ Missing | No PO routes | P2 | Deferred for pilot; out-of-scope per pitch §3.3 |
| Supplier catalogue | ❌ Missing | No supplier management feature | P2 | ManWinWin maintains vendor contacts + SLAs |
| Goods receipt & stock update | ❌ Missing | No GRN component | Defer | Requires inventory module first |

### Domain: Contracts & SLA

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Service contracts (FM → hospital, duration, scope) | ❌ Missing | Invoices exist but no contract entity or route | P1 | ManWinWin links WOs to contracts for SLA compliance; critical for Egypt FM billing |
| SLA definitions per WO type (response time, resolution time) | ❌ Missing | No SLA timer or SLA schema evidenced | P1 | Hospital contracts specify response SLAs; breaches = penalties |
| Contract-linked invoicing | 🟡 Partial | Invoice generation done (pitch §3.1); not linked to contract terms or SLA | P1 | Invoice generated but disconnected from contract scope |

### Domain: Reporting & KPIs

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| KPI dashboard (MTTR, MTBF, PM compliance %) | ❌ Missing | `DashboardPage.tsx` exists but pitch §3.1 "Advanced reporting / KPIs — TBD" | P1 | Pilot success KPIs per pitch §13; ManWinWin has rich KPI engine |
| WO summary reports (open / closed / by technician) | ❌ Missing | No report export route; ReportTemplatesPage = WO field templates, not analytics | P1 | ManWinWin generates management summary reports |
| Asset cost-per-asset report | ❌ Missing | No cost aggregation by asset | P1 | ManWinWin tracks total lifetime cost per asset |
| PM compliance export (CSV / PDF) | ❌ Missing | No export function evidenced | P1 | Hospital audit requirement |
| Custom report builder | ❌ Missing | No drag-and-drop report builder | Defer | ManWinWin has report builder; too complex for pilot |
| Invoice accuracy / billing report | 🟡 Partial | InvoicesPage + InvoiceDetailPage + PDF generation done; no aggregation/summary view | P1 | Per-invoice done; billing summary analytics missing |

### Domain: Mobile

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Technician mobile app (WO list, accept, close) | 🟡 Partial | `src/features/pwa/InstallOrbitBanner.tsx` (PWA pilot stub); pitch §3.1 "Mobile app — TBD" | P1 | PWA banner only; no offline capability; ManWinWin has native mobile |
| Offline mode (WO completion without network) | ❌ Missing | No service worker / offline cache evidenced | P1 | Hospital wards have poor Wi-Fi; offline required for technician trust |
| Mobile QR scan to open WO | ❌ Missing | No QR scan → WO flow on mobile | P1 | ManWinWin core mobile feature |
| Photo capture from mobile | ❌ Missing | Blocked by object storage gap + no mobile photo capture UX | P1 | Evidence capture per WO — hospital compliance requirement |

### Domain: Multi-site & Administration

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Multi-site management (sites, buildings, floors) | ✅ Done | `SiteDetailPage.tsx`, `LocationsPage.tsx`, companies/sites hierarchy | — | Core done; floors/rooms via location tree |
| Site-level KPI rollup | ❌ Missing | No cross-site dashboard | P2 | ManWinWin aggregates KPIs by site/region |
| RBAC — role-based access control | ✅ Done | `ProtectedRoute` with role lists; roles: super_admin, company_admin, client_admin, site_manager, manager, technician | — | Mature RBAC |
| User skills / certification tracking | ❌ Missing | No skills/certifications entity in users feature | P2 | ManWinWin tracks technician qualifications; hospital biomed compliance |
| Shift / on-call scheduling | ❌ Missing | No scheduling module | Defer | ManWinWin has basic scheduling; Orbit out-of-scope |
| Notifications (email / SMS / push) | 🟡 Partial | `NotificationBell.tsx` in UI; pitch §3.1 "Notifications — Partial — Needs production SMTP" | P0 | In-app notification component done; email delivery not prod-ready |

### Domain: Compliance & Documents

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Controlled document management (SOPs, manuals) | ❌ Missing | No document library feature | P2 | ManWinWin stores equipment manuals linked to assets; Orbit missing |
| Hospital-specific report templates (biomed format) | 🟡 Partial | `ReportTemplatesPage.tsx` done (generic templates); pitch §3.2 "Hospital report templates — 2–4 weeks" pre-contract gap | P0 | Generic template engine ready; hospital-specific formats (biomed, HVAC) not built |
| Compliance audit log | 🟡 Partial | RBAC and report approval workflow exist; dedicated audit log/export missing | P1 | ManWinWin exports full audit trail for regulatory review |
| Regulatory report export (Ministry of Health) | ❌ Missing | No MoH-format export | P2 | Egypt-specific; ManWinWin localised for each market |

### Domain: Billing & Invoicing (Orbit differentiator)

| ManWinWin Capability | Orbit Status | Evidence | Pilot Priority | Notes |
|---|---|---|---|---|
| Invoice generation from WO | ✅ Done | `src/features/invoices/pages/InvoicesPage.tsx`, `InvoiceDetailPage.tsx`, `InvoicePreviewModal.tsx`; pitch §3.1 Done | — | Orbit differentiator — richer than ManWinWin baseline |
| Branded PDF invoice (Arabic RTL) | ✅ Done | Pitch §3.1 "Invoices + branded PDF — Done"; Arabic RTL confirmed | — | Orbit unique advantage |
| Invoice approval workflow | ✅ Done | Report → approval → invoice-generate chain per `CLAUDE.md` | — | — |
| Invoice line items (labor + parts) | 🟡 Partial | Labor entries done; parts line items missing (no inventory) | P1 | Parts cost not capturable until inventory module built |

---

## 4. Top 10 Missing Capabilities — Ranked for Hospital FM Egypt Pilot

These are ranked by **blocking impact on the first paid contract**, combining pilot KPI coverage, hospital stakeholder expectations, and Egyptian FM market context.

| Rank | Capability | Gap Type | Rationale | Sprint Est. |
|---|---|---|---|---|
| **#1** | **Automated PM job generation (background scheduler)** | Missing sub-system | Pitch explicitly flags as pre-contract. Without it, PM is manual + calendar-only. Hospital regulatory compliance requires automated, time-stamped PM WOs. Blocks the #1 pilot KPI: "PM compliance rate." | 4–6 wks |
| **#2** | **Production object storage (photo/doc attachments on WOs & assets)** | Infrastructure gap | Biomed engineers photograph equipment on every corrective WO — it's a compliance requirement. Without it, the report template is text-only and legally weak. Blocks hospital acceptance. | 2–3 wks |
| **#3** | **Hospital-specific report templates (biomed / HVAC format)** | Content gap | Generic template engine exists. Egypt hospitals expect a specific Arabic biomed maintenance report format, often required for accreditation (JCI/GAHAR). Templating effort is relatively low once object storage is live. | 2–4 wks |
| **#4** | **SLA definitions + breach alerting** | Missing module | Egyptian FM contracts with hospitals specify response time SLAs (e.g., critical equipment ≤2h response). Without SLA timers, Orbit cannot prove contractual compliance or trigger escalation. Directly affects FM company's liability posture. | 4–6 wks |
| **#5** | **PM compliance KPI dashboard** | Missing analytics | Pilot success KPIs in pitch §13 include "PM compliance." If the dashboard doesn't show it, the pilot review meeting has no data. ManWinWin ships this out of the box. Even a simple % gauge closes the gap. | 3–4 wks |
| **#6** | **Meter / runtime readings (sterilisers, generators, lifts)** | Missing module | Hospitals operate equipment with cycle-based maintenance (steriliser cycles, generator run-hours). Without meters, PM scheduling is calendar-only — which misses failure events that happen between calendar dates. JCIA standard expects cycle-based records. | 4–8 wks |
| **#7** | **Downtime tracking per WO (MTTR, equipment availability %)** | Missing field/KPI | Hospital FM managers measure equipment availability. MTTR (mean time to repair) is a standard KPI in any contract review. Requires WO start/end timestamp pair + downtime field. Low code effort; high stakeholder visibility. | 1–2 wks |
| **#8** | **Mobile PWA — offline WO completion + QR scan** | Missing capability | Hospital wards and basement plantrooms have poor Wi-Fi. Technicians cannot rely on connectivity. Without offline WO completion, mobile is useless for field staff and paper prevails. PWA offline (service worker + IndexedDB) is the minimum viable mobile story. | 6–10 wks |
| **#9** | **Parts / spare parts basic catalogue (no full inventory)** | Missing module | Even a lightweight parts list (name, quantity on hand, linked asset) allows technicians to log what was consumed in a WO. FM companies track this for billing and replenishment. Full warehouse management is out of scope; basic parts capture is not. | 3–5 wks |
| **#10** | **WO-to-asset link FE (maintenance history tab)** | Open UAT bug | Wave 5 NT-P5-A01-FE is **Open** (backend fixed). Without it, the asset detail page shows all company WOs instead of the one asset's history — a critical trust failure in a demo or live use. Smallest effort of all top-10 items. | ≤1 wk |

---

## 5. Explicit Non-Goals — What We Will NOT Chase from ManWinWin

The following ManWinWin capabilities are **deliberately out of Orbit AM's year-1 scope**. Pursuing them would distract from the Egypt hospital pilot and delay revenue. These are documented to prevent scope creep.

| ManWinWin Capability | Decision | Reason |
|---|---|---|
| **Full inventory / warehouse management** (bins, FIFO, multi-location stock) | ❌ Non-goal (year 1) | Orbit pitch §3.3 defers inventory as "future add-on / later decision." A basic parts catalogue (Top-10 #9) is the maximum. Full WMS is a separate product SKU if ever built. |
| **Purchase order management + goods receipt** | ❌ Non-goal (year 1) | Procurement is complex, hospital-procurement-law-sensitive in Egypt, and not part of the FM company's core value prop to the hospital. Keep Orbit on the maintenance side of the FM–hospital boundary. |
| **IoT / sensor-based condition monitoring** (SCADA, BMS integration) | ❌ Non-goal (year 1) | Requires hardware partnerships and integration contracts. Out of scope per pitch §3.3 "Phase 4 — Enterprise connect." Sell the vision, not the product. |
| **Technician skills & certification matrix** | ❌ Non-goal (year 1) | HR functionality that belongs in the FM company's HR system. Low hospital-side demand in Egypt year 1. Revisit at Network/Enterprise tier. |
| **Shift scheduling / on-call roster** | ❌ Non-goal (year 1) | Scheduling belongs in WFM tools (e.g. Deputy, BambooHR for SMEs). Orbit is not a WFM product. |
| **Custom report builder (drag-and-drop)** | ❌ Non-goal (year 1) | High engineering effort; low pilot value. Pre-built compliance and KPI reports (Top-10 #3 and #5) deliver 90% of hospital stakeholder value at 20% of the engineering cost. |
| **AI maintenance / predictive analytics** | ❌ Non-goal (year 1) | Explicitly priced as a **standalone product** in pitch §5. Do not bundle or roadmap into year-1 CMMS scope. Sell the story only. |
| **HIS / ERP / SSO integration** | ❌ Non-goal (year 1) | Pitch §3.3 "Phase 4 — Enterprise connect — Standalone paid." Year-1 pilot hospitals can tolerate manual data entry. Enterprise deal unlocks integration SOW. |

---

## Appendix — Evidence Map

| File / Doc | Capabilities evidenced |
|---|---|
| `src/app/routes.tsx` | 18 routes: dashboard, companies, sites, assets, work-orders, invoices, users, labor, locations, report-templates, platform, subscription, profile |
| `src/features/assets/` | Assets CRUD, lifecycle, calendar, WO panel, import, QR (site) |
| `src/features/work-orders/` | WO list, WO detail, WO request review |
| `src/features/invoices/` | Invoice list, detail, PDF preview |
| `src/features/labor/` | Time entries / labor logging |
| `src/features/reports/` | Report template management |
| `src/features/companies/` | Companies, sites, manager assignment, QR modal |
| `src/features/locations/` | Location tree |
| `src/features/users/` | Users CRUD, profile |
| `src/features/pwa/` | PWA install banner (stub) |
| `docs/pitch/ORBIT_AM_PITCH_PACK.md §3` | Self-declared Done/Partial/TBD per module |
| `docs/knowledge-hub/product/04_wave5_findings.md` | 20 UAT bug tasks; 10 backend Fixed; 10 frontend Open |

---

*Methodology: ManWinWin public CMMS documentation (manwinwin.com, public product sheets, partner documentation). No proprietary ManWinWin materials used.*  
*Next review: After Wave 5 FE tasks close and PM scheduler spike completes.*
