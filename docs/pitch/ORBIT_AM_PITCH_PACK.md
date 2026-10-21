# Orbit AM — Complete Pitch & Packaging Pack

**Product:** Orbit AM — Hospital Asset & Maintenance Management  
**Company suite:** Orbit AM + Orbit QM  
**Market:** Egypt healthcare FM (year 1)  
**Audiences:** Mid–large FM / maintenance companies + partners  
**Document type:** Detailed sales & partner pack (bootstrap — no fundraising ask)  
**Version:** 2026-07-14  
**Currency:** EGP annual, VAT excluded  

---

## Table of contents

1. [Executive summary](#1-executive-summary)  
2. [Product overview & CMMS definition](#2-product-overview--cmms-definition)  
3. [Feature matrix — implemented vs TBD](#3-feature-matrix--implemented-vs-tbd)  
4. [Packaging & pricing (EGP 420K–3.5M)](#4-packaging--pricing-egp-420k35m)  
5. [Hybrid phase pricing rules](#5-hybrid-phase-pricing-rules)  
6. [Cloud TCO — AWS, Azure, Cloudflare](#6-cloud-tco--aws-azure-cloudflare)  
7. [Hidden costs & full TCO (internal)](#7-hidden-costs--full-tco-internal)  
8. [Partner cost split (detailed)](#8-partner-cost-split-detailed)  
9. [Team plan — founder + 2 interns](#9-team-plan--founder--2-interns)  
10. [Go-to-market & partners](#10-go-to-market--partners)  
11. [Orbit QM + Miraco](#11-orbit-qm--miraco)  
12. [16-slide deck outline](#12-16-slide-deck-outline)  
13. [Pilot offer & next steps](#13-pilot-offer--next-steps)  

---

## 1. Executive summary

Orbit AM is a **multi-tenant CMMS SaaS** for maintenance companies that serve **hospitals** in Egypt. It covers assets, preventive calendars, work orders, structured reports, and invoicing — with Arabic-first RTL UX.

| Item | Decision |
|------|----------|
| Brand | **Orbit AM** |
| Price band (all tiers) | **EGP 420,000 → 3,500,000** / year |
| Tiers | Clinical · Regional · Network · Enterprise |
| Business model | Hybrid annual subscription (asset-band primary + user caps); setup included |
| Cloud | **Not locked** — AWS / Azure / Cloudflare hybrid selection per deal |
| Phase pricing | Hybrid: core + Mobile included; Reporting by tier; **AI** and **Integrations** standalone |
| Traction | Pre-revenue AM; **Orbit QM live at Miraco** |
| Team burn model | Founder (~EGP 80K) + 2 student interns |

---

## 2. Product overview & CMMS definition

### What is CMMS?

**CMMS** = **Computerized Maintenance Management System** — software to register assets, schedule preventive maintenance (PM), run work orders, keep history/compliance records, and (in Orbit AM) generate invoices from completed work.

Orbit AM is **hospital-ready CMMS + billing**, not a claim of full IBM Maximo parity on day one.

### Actors

```
Orbit platform  →  Maintenance / FM company  →  Hospital clients (sites)
   (you)              technicians & admins         biomed / facilities
```

### Value proposition

- One system for FM company and every hospital it serves  
- Arabic default + English  
- Annual price includes onboarding (no surprise implementation invoice)  
- Scales from **1 hospital / 500 assets** to **85 hospitals / 20,000 assets**

---

## 3. Feature matrix — implemented vs TBD

### 3.1 Core platform (sellable foundation)

| Module | Status | Hospital relevance |
|--------|--------|-------------------|
| Multi-tenant SaaS + RBAC | Done | FM vs hospital role split |
| Companies, sites, locations | Done | Multi-hospital per tenant |
| Assets + CSV import + lifecycle | Done | Biomed + facilities equipment |
| Maintenance calendar (M/Q/Y) | Done | PM planning |
| Work orders (full lifecycle) | Done | Corrective + preventive |
| Template reports + approval | Done | Compliance documentation |
| Invoices + branded PDF | Done | FM → hospital billing |
| Labor / time entries | Done | Engineer hours |
| WO requests (hospital → FM) | Done | Request channel |
| Licensing & feature gates | Done | Package enforcement |
| Arabic + English RTL | Done | Egypt differentiator |
| Demo pitch seed / reset | Done | Sales demos |
| Notifications | Partial | Needs production SMTP |
| Automated PM job runner | Partial / TBD | Needed before large contracts |
| AI maintenance | Stub only | Sold as **standalone** later |
| Mobile app | TBD | **Included in packages** when shipped |
| Advanced reporting / KPIs | TBD | Network+ included; lower tiers add-on |
| Systems integration | TBD | **Standalone** paid |

### 3.2 Must close before first hospital contract

| Gap | Effort band |
|-----|-------------|
| Invoice / golden-path E2E green | 2–4 weeks |
| Wave 5 UAT verification | 2–3 weeks |
| Automated PM scheduling jobs | 4–6 weeks |
| Production object storage | 2–3 weeks |
| Hospital report templates | 2–4 weeks |

**Realistic core readiness:** ~8–12 weeks with founder + 2 interns (CMMS-core scope).

### 3.3 Maximo-inspired roadmap (honest phasing)

| Phase | Capabilities | Pricing treatment |
|-------|--------------|-------------------|
| Pre-launch hardening | QA, PM jobs, storage, hospital templates | Included in tiers |
| Phase 2 — Reporting | KPI dashboards, cost-per-asset, compliance exports | **Included Network+**; add-on Clinical/Regional |
| Phase 3 — Mobile | Technician field app | **Included in all packages** when launched |
| Phase 3 — Intelligence | AI recommendations, forecasting | **Standalone — AI Maintenance** |
| Phase 4 — Enterprise connect | HIS/ERP/SSO, webhooks | **Standalone — Systems Integration** |
| Phase 4 — Parts | Inventory UI | Future add-on / later decision |

---

## 4. Packaging & pricing (EGP 420K–3.5M)

### 4.1 Asset scale reference

| Scenario | Hospitals | Assets | Users |
|----------|-----------|--------|-------|
| Pilot | 1 | 300–500 | 10–20 |
| Growth | 5–15 | 2,000–5,000 | 30–60 |
| Network | ~40 | ~10,000 | ~100 |
| Enterprise | up to 85 | up to 20,000 | 80–150+ |

### 4.2 Four tiers (annual)

| Tier | Assets | Users | Hospitals | **Annual EGP** | ~USD @ 50 |
|------|--------|-------|-----------|----------------|-----------|
| **Orbit Clinical** | 500 | 20 | 1 | **420,000** | ~$8,400 |
| **Orbit Regional** | 5,000 | 60 | 15 | **1,050,000** | ~$21,000 |
| **Orbit Network** | 10,000 | 100 | 40 | **2,800,000** | ~$56,000 |
| **Orbit Enterprise** | 20,000 | 150 | 85 | **3,500,000** | ~$70,000 |

**Band check:** Floor **420K** · Ceiling **3.5M** · Network sits **close to Enterprise** (confidence / anchoring).

### 4.3 Effective asset economics (illustrative)

| Tier | EGP / asset / month (at cap) |
|------|------------------------------|
| Clinical (500) | 70 |
| Regional (5,000) | 17.5 |
| Network (10,000) | 23.3 |
| Enterprise (20,000) | 14.6 |

### 4.4 Included in every tier

- Core CMMS modules (assets, WO, calendars, reports, invoices, labor, requests)  
- Arabic + English RTL  
- Onboarding + CSV import assistance + **5 days remote training**  
- Business-hours support (Cairo TZ)  
- Quarterly product updates  
- **Mobile app (when launched)** — not sold separately  

### 4.5 Pilot offer (6-month goal)

**Clinical @ 50% year-1** = **EGP 210,000** for 12 months (1–2 reference logos + UAT feedback).

### 4.6 Suggested overages (order form, not public hero prices)

| Overage | Guide |
|---------|--------|
| +1,000 assets | +EGP 90,000 / year |
| +10 users | +EGP 45,000 / year |
| Dedicated DB | Custom (+40% infra surcharge on that tenant) |
| On-site training travel | EGP 15–30K per trip (optional, billable) |

---

## 5. Hybrid phase pricing rules

### Rule summary

| Item | Treatment |
|------|-----------|
| Core CMMS | Included in **all** tiers forever |
| Mobile technician app | **Included** in all packages when shipped (**not** a paid add-on) |
| Advanced Reporting & KPIs | **Included** from **Network** and Enterprise; **paid add-on** for Clinical & Regional |
| **AI Maintenance** | **Standalone product** — always separately priced |
| **Systems Integration** | **Standalone product** — always separately priced |
| Forecasting | Packaged inside **AI Maintenance** as capability matures |

### Advanced Reporting add-on (Clinical / Regional)

| Guide price | Note |
|-------------|------|
| **EGP 280,000 / year** | Aligns under Network uplift without breaking 3.5M ceiling story |

### Standalone — AI Maintenance (quote)

| Scope | Pricing posture |
|-------|-----------------|
| AI PM suggestions, work-planning assistance, forecasting roadmapped | **Custom annual** — typically mid–high six figures EGP; never “free in Enterprise” |

### Standalone — Systems Integration (quote)

| Scope | Pricing posture |
|-------|-----------------|
| HIS / ERP connectors, SSO, webhooks | **Custom** — per connector or SOW; year-1 optional |

### Sales language (use on deck)

> “Your package includes the full CMMS and, when ready, the mobile app. Advanced reporting is included from Network upward. AI and system integrations are optional modules you can add when you need them.”

---

## 6. Cloud TCO — AWS, Azure, Cloudflare

**Decision state:** Cloud is **selection-based** — not pre-decided. This section is for partner / technical honesty.

### 6.1 Fit for Orbit AM (FastAPI + PostgreSQL + React)

| Provider | Verdict |
|----------|---------|
| **AWS** | Excellent primary: RDS Postgres, ALB, S3, ECS/EC2 |
| **Azure** | Excellent primary: Flexible Server, App Service/AKS, Blob; useful if buyer is Microsoft-centric |
| **Cloudflare** | Best as **edge layer** (CDN, WAF, R2 zero-egress photos). **Not** a full Postgres replacement (D1 = SQLite). Pair with Neon/RDS/Supabase via Hyperdrive if using Workers |

### 6.2 How the bill is triggered

| Line item | Trigger | Scaling note |
|-----------|---------|--------------|
| API compute | Instance / vCPU **hours while running** | Scales with concurrent users & jobs |
| Managed Postgres | **Provisioned** hours + storage GiB | Multi-AZ / zone-redundant ≈ **~2× compute** |
| Extra / dedicated DB | **New instance = new fixed monthly floor** | Only for Network/Enterprise quotes |
| Load balancer | ALB / Azure LB **hourly** + capacity units / processed bytes | Turn on when HA / multi-instance needed |
| Object storage | GiB stored + requests + **egress** | Hospital photo uploads can dominate |
| Backups | Beyond free allotment | Grows with DB |
| Cloudflare | Workers requests, R2 storage (often $0 egress), WAF plan | Cheap edge; **does not cancel** DB bill |

### 6.3 Indicative monthly infra (shared multi-tenant, USD → ~EGP×50)

| Stage | Layout | USD/mo | ~EGP/mo |
|-------|--------|--------|---------|
| Pilot (Clinical) | 1 API + small Single-AZ Postgres + storage + CDN | 80–200 | 4–10K |
| Regional scale | 2 API + Multi-AZ Postgres + ALB + storage | 250–600 | 12–30K |
| Network / heavy shared | Autoscale API + HA Postgres (+ optional read replica) | 500–1,200 | 25–60K |
| Dedicated Enterprise DB add-on | + Multi-AZ Postgres per whale | +200–475 | +10–24K |

### 6.4 Multi-tenant economics (important)

| Pattern | Cost behavior | Orbit year-1 default |
|---------|---------------|----------------------|
| Shared DB + `tenant_id` | Cost grows with **load/size**, not tenant count | **Yes — default** |
| DB-per-tenant | ~$40–150+/tenant/mo baseline | Only with Enterprise ACV + compliance need |

### 6.5 Recommended selection guide (not a lock-in)

1. Start **shared multi-tenant** on **AWS or Azure**  
2. Put **Cloudflare** in front for CDN/WAF; use **R2** if photo egress hurts  
3. Offer **dedicated DB** only on Network/Enterprise custom quotes  

---

## 7. Hidden costs & full TCO (internal)

### 7.1 Monthly burn (pre-revenue / few customers)

| Line item | Low | Base | High |
|-----------|-----|------|------|
| Founder | 70,000 | **80,000** | 90,000 |
| 2 student interns | 8,000 | **9,000** | 10,000 |
| Tools / stipend misc | 2,000 | 3,000 | 5,000 |
| Cloud (dev+demo+pilot) | 3,000 | **6,000** | 12,000 |
| SaaS tools | 4,000 | **8,000** | 15,000 |
| Sales & marketing | 5,000 | **12,000** | 25,000 |
| Legal & accounting (amortized) | 2,000 | **4,000** | 8,000 |
| Contingency | 5,000 | **10,000** | 15,000 |
| **Total / month** | **99,000** | **~132,000** | **180,000** |

**6-month runway (base):** ~**EGP 790,000**

### 7.2 COGS after you sell (what eats margin)

| Tenant | Infra/mo (EGP) | Support load |
|--------|----------------|--------------|
| 500 assets | 3–8K | Low |
| 5,000 assets | 15–35K | Medium |
| 10,000 assets | 30–70K | High |
| 20,000 assets | 50–120K | Highest |

**Hidden COGS triggers:** WO photo storage, custom integrations (your time), on-site travel, payment fees 2.5–3%, FX 1–3%.

### 7.3 Customer-side hidden costs (sales honesty — FAQ, not partner slide)

| Their cost | Typical |
|------------|---------|
| Biomed project owner | 20–40% FTE × 3 months |
| Asset data cleanup before import | Largest delay risk |
| Technician adoption | 2–6 months |
| Enterprise IT / SSO reviews | Network/Enterprise deals |

---

## 8. Partner cost split (detailed)

**Audience:** Partners / implementers / referral agents — **not** end-hospital buyers.  
**Purpose:** Show where annual subscription money goes so partners understand margin and commission integrity.

### 8.1 Year-1 ACV split (indicative)

| Bucket | Share of ACV | What partners should know |
|--------|--------------|---------------------------|
| Cloud & platform ops | **12–18%** | Hosting, DB, LB when needed, backups, monitoring, CDN/WAF |
| Onboarding & delivery | **10–15%** | Included migration/training — partners who implement may earn from this + fee |
| Support & success | **8–12%** | Business-hours support, triage |
| Product & R&D | **20–25%** | CMMS roadmap, Arabic UX, mobile when shipped |
| Sales & partner commission | **10–15%** | Referral commission lives here on partner-sourced deals |
| Gross margin / runway | **25–35%** | Company sustainability; cushions Enterprise COGS |

### 8.2 Worked examples

**Clinical ACV = EGP 420,000**

| Bucket @ mid | EGP |
|--------------|-----|
| Cloud 15% | 63,000 |
| Onboarding 12% | 50,400 |
| Support 10% | 42,000 |
| R&D 22% | 92,400 |
| Sales/partner 12% | 50,400 |
| Margin 29% | 121,800 |

**Referral partner at 12% year-1 ACV** → **EGP 50,400** on a full Clinical deal.

**Regional ACV = EGP 1,050,000** → referral 12% = **EGP 126,000**  
**Network ACV = EGP 2,800,000** → referral 12% = **EGP 336,000**  
**Enterprise ACV = EGP 3,500,000** → referral 12% = **EGP 420,000**

### 8.3 Partner programs

| Stage | Model | Economics |
|-------|--------|-----------|
| 0–3 customers | Direct + warm network | — |
| 3–10 | **Referral** | **10–15% of year-1 ACV** |
| 10+ | **Certified implementer** | **20–25%** + defined implementation fee |

**Year-1 ACV** = first-year subscription only (not recurring forever unless contracted).

### 8.4 Why Network is priced close to Enterprise

Anchors confidence: Network at **2.8M** is a serious hospital-network product; Enterprise at **3.5M** is the national/cap tier — not a 4× jump from Regional that looks arbitrary.

---

## 9. Team plan — founder + 2 interns

| Role | Focus | Mentoring |
|------|--------|-----------|
| Founder | Architecture, hospital domain, sales demos, reviews | 10+ hrs/week with interns |
| Intern A — QA | Playwright E2E, hospital golden path, Wave regression | — |
| Intern B — Frontend | Hospital templates, dashboards, Arabic copy | — |

**Stipend:** EGP 4,000–5,000 each / month (included in burn §7.1).

---

## 10. Go-to-market & partners

| Channel | Action |
|---------|--------|
| Direct | FM companies already in hospitals |
| Demo-first | Pitch Docker demo + 30-min golden path |
| Mix | LinkedIn, referrals, associations |
| Partners | Referral 10–15% year-1 ACV |
| Timeline | First paying customer in **6 months** (Clinical pilot) |

**Support year 1:** Founder-led (cap concurrent customers until partner support or hire).

---

## 11. Orbit QM + Miraco

### Orbit QM (suite sibling)

**Orbit QM** is a **Quality Management Dashboard** for manufacturing quality operations.

**Capabilities (from product workspace):**

| Area | Modules |
|------|---------|
| Overview | Dashboard, Traceability |
| Inspections | **IQC**, **IPQC**, **FQC** |
| Quality | **NCR**, **CAPA**, Suppliers, Calibration, Audits, Complaints |
| Manager tools | Part specs, Process flow, **SPC control charts** |
| System | Master data, Reports, Notifications, Users / RBAC |

Roles span Data Entry → Supervisor → Engineer → Quality Manager / Admin. Printable QMS documents with company letterhead.

### Live customer — Miraco

| Field | Detail |
|-------|--------|
| **Customer** | **Miraco** |
| Legal / trade context | Miraco Company for Air Conditioning & Refrigeration |
| Geography | **Egypt** |
| Context | Manufacturer of **Carrier & Midea** products |
| Product used | **Orbit QM** — quality management system |
| **Pricing** | **Not published in this pack** |

### Cross-sell narrative

Orbit AM (hospital / facility maintenance) and Orbit QM (manufacturing quality) share SaaS DNA: role-based ops, Arabic-ready UX, printable controlled documents. Different domains — complementary credibility for the Orbit brand.

---

## 12. 16-slide deck outline

Use `docs/pitch/ORBIT_AM_SLIDE_PROMPT.md` for generator-ready prompts. Summary:

| # | Slide | Notes |
|---|-------|-------|
| 1 | Title | Orbit AM |
| 2 | Problem | Excel / WhatsApp / expensive CMMS |
| 3 | Solution | Multi-tenant hospital CMMS |
| 4 | How it works | 3-tier actors |
| 5 | Product deep-dive | Core modules |
| 6 | Live vs roadmap | Honest |
| 7 | Package × features matrix | Clinical→Enterprise |
| 8 | Pricing 420K–3.5M | 4 tiers |
| 9 | Standalone AI + Integrations | Mobile included |
| 10 | Why Egypt healthcare | Scale story |
| 11 | GTM | Mix + referral % |
| 12 | **Partner cost split** | Detailed ACV pie |
| 13 | Cloud options | AWS/Azure/CF selection |
| 14 | Orbit suite | AM + QM |
| 15 | Customers | **Miraco** (QM); AM pilots |
| 16 | CTA | 90-day Clinical pilot |

---

## 13. Pilot offer & next steps

### 90-day hospital pilot

1. One hospital · ~300–500 assets · Clinical  
2. Asset import + PM schedules included  
3. Train ≤20 users included  
4. KPIs: PM compliance, WO cycle time, invoice accuracy  

**Pilot price option:** EGP **210,000** year-1 (50% Clinical) for reference customers.

### Immediate actions

1. Freeze v1 sales scope = core CMMS (+ mobile when ready, included)  
2. Keep AI & Integrations off the critical path for first logo  
3. Select cloud with first serious Network/Enterprise prospect (credits / IT preference)  
4. Name first Clinical pilot prospect  
5. Generate slides from `ORBIT_AM_SLIDE_PROMPT.md`

---

## Appendix A — Price card (print)

| Package | Annual EGP | Assets | Users | Hospitals |
|---------|------------|--------|-------|-----------|
| Clinical | 420,000 | 500 | 20 | 1 |
| Regional | 1,050,000 | 5,000 | 60 | 15 |
| Network | 2,800,000 | 10,000 | 100 | 40 |
| Enterprise | 3,500,000 | 20,000 | 150 | 85 |

VAT excluded · Setup included · Mobile included when launched · AI & Integrations standalone

---

## Appendix B — Glossary

| Term | Meaning |
|------|---------|
| CMMS | Computerized Maintenance Management System |
| ACV | Annual Contract Value (one year of subscription) |
| Year-1 ACV | First contract year only (partner commission basis) |
| COGS | Cost to serve a customer (infra + support load) |
| TCO | Total cost of ownership (all parties) |
| PM | Preventive maintenance |
| HIS / ERP | Hospital information / enterprise resource systems |

---

*End of pack. Companion file: `ORBIT_AM_SLIDE_PROMPT.md`*
