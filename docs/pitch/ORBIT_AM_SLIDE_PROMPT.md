# Orbit AM — Detailed Slide Generation Prompt

**Use this prompt** in Gamma, Beautiful.ai, Plus AI, Copilot, or a design agent to generate the sales deck.  
**Audience:** Mid–large FM companies serving hospitals (Egypt, year 1) + **partners / resellers**.  
**Language:** English. **Brand:** Orbit AM. **Tone:** Product-confident, clear, not investor-fundraising.

---

## Master prompt (copy into your slide tool)

```
Create a professional product sales pitch deck (16 slides) for Orbit AM —
Hospital Asset & Maintenance Management, a multi-tenant CMMS SaaS sold in Egypt
to maintenance / facility companies that serve hospitals.

BRAND
- Product name: Orbit AM
- Suite sibling: Orbit QM (Quality Management Dashboard)
- Tagline: Maintain every asset. One orbit.
- Visual: modern, global/tech, clean blue-teal professional healthcare — NOT purple gradients,
  NOT cream terracotta, NOT dark neon cyber. Prefer clear hierarchy, whitespace, one accent.
- Arabic-first / RTL is a differentiator — mention once on solution/product slides, not every slide.

AUDIENCE MIX
- Primary: FM company buyers (commercial / ops directors)
- Secondary: Partners (referral / implementation) — slides 12–13 are partner-facing cost split

CONSTRAINTS
- Prices are annual EGP, VAT excluded, setup/onboarding/training INCLUDED in subscription
- Price band across ALL tiers: EGP 420,000 → EGP 3,500,000 maximum
- Four tiers: Clinical, Regional, Network, Enterprise
- Cloud provider (AWS / Azure / Cloudflare) is NOT decided — show “cloud-agnostic SaaS”
  and a partner appendix note that hosting is selected per deal (shared multi-tenant default)
- Bootstrap company — NO fundraising ask. CTA = 90-day hospital pilot
- Product-focused: expand packages + features; do not bury pricing in thin tables

HYBRID PHASE PRICING RULES (must appear accurately on package / roadmap slides)
- CORE CMMS modules: included in ALL tiers
- Mobile technician app: INCLUDED in packages (bundled when launched — not a paid add-on)
- Advanced Reporting & KPI pack: included from Network upward; optional paid add-on for Clinical & Regional
- AI Maintenance (recommendations / planning): STANDALONE paid feature
- Systems Integration (HIS / ERP / SSO connectors): STANDALONE paid feature
- Forecasting may be described under the AI standalone module

PROOF
- Orbit QM live customer: Miraco (Miraco Company for Air Conditioning & Refrigeration, Egypt —
  manufacturer of Carrier & Midea products). Show as credibility, NO QM pricing.
- Orbit AM: pre-revenue / pilot-ready; demo environment exists

Generate exactly the 16 slides below. Each slide: title, bullet content, speaker notes (2–4 lines).
Use comparison tables on slides 7–9 and 12. Do not invent features beyond the list provided.
```

---

## Slide-by-slide specification

### Slide 1 — Title

**Title:** Orbit AM  
**Subtitle:** Hospital Asset & Maintenance Management  
**Tagline:** *Maintain every asset. One orbit.*  
**Footer:** Cairo · Egypt · Product sales deck (partners & FM buyers)  
**Visual:** Full-bleed calm hospital/engineering visual OR abstract “orbit” path around equipment icons — brand-first, one CTA line: “Multi-tenant CMMS for hospital maintenance.”

**Speaker notes:** Introduce as Arabic-first SaaS for FM companies serving hospitals; sister product Orbit QM already in market (Miraco).

---

### Slide 2 — The problem

**Title:** Hospitals run on assets — maintenance still runs on Excel & WhatsApp  

**Bullets:**
- Biomedical, HVAC, electrical, and facilities assets — hundreds per hospital
- Work orders scattered across paper, Excel, WhatsApp — no single audit trail
- Preventive maintenance missed → downtime and compliance risk
- International CMMS (e.g. Maximo-class) is expensive and heavy to deploy in Egypt
- FM companies struggle to bill accurately from completed field work

**Visual:** “Today’s stack” vs “What hospitals need” two-column.

---

### Slide 3 — Solution

**Title:** Orbit AM — one platform for the FM company and every hospital client  

**Bullets:**
- Multi-tenant SaaS: Platform → Maintenance company → Hospital sites
- Assets → preventive calendars → work orders → structured reports → invoices
- Arabic default + English, full RTL
- Cloud-hosted; annual subscription includes onboarding & training
- Built for Egypt healthcare FM outsourcing, priced for local buying cycles

**Footer callout:** CMMS = Computerized Maintenance Management System

---

### Slide 4 — How it works (actors)

**Title:** Three-tier operating model  

**Diagram (must show):**
1. **Orbit (software company)** — packages, licensing, platform admin  
2. **Maintenance / FM company** — technicians, managers, invoicing  
3. **Hospital clients** — request work, view assets & WO status  

**Flow strip:** Register hospital → Import assets → Schedule PM → Execute WO → Approve report → Invoice

---

### Slide 5 — Product deep-dive (core)

**Title:** What Orbit AM does today  

**Six module cards:**
1. **Assets** — registry, lifecycle, CSV import, spare flag  
2. **Maintenance calendar** — monthly / quarterly / yearly  
3. **Work orders** — corrective & preventive, full lifecycle  
4. **Template reports** — draft → submit → approve  
5. **Invoicing & PDF** — generate from verified work, branded PDF  
6. **RBAC + hospital requests** — client/site roles; request queue  

**Aside:** Multi-tenant licensing & pitch demo environment ready

---

### Slide 6 — Live vs roadmap

**Title:** Delivery honesty — sell what is ready; roadmap is clear  

**Two columns:**

| Live / near-production | Roadmap (phased) |
|------------------------|------------------|
| Multi-tenant auth & RBAC | Advanced reporting & KPI dashboards |
| Companies, sites, locations | Automated PM job fleet at scale |
| Assets + calendars + WO + invoices | Forecasting & AI recommendations |
| Labor, PDF reports, Arabic/RTL | Parts inventory UI |
| Feature-gated packages | Systems integrations (HIS/ERP/SSO) |
| Demo reset for sales | Mobile app (INCLUDED in packages when shipped) |

**Footer:** First sales target: hardened core CMMS (hospital golden path) — not full Maximo parity on day one.

---

### Slide 7 — Package matrix (features × tiers)

**Title:** Packages — what’s included  

**Table columns:** Feature | Clinical | Regional | Network | Enterprise  

**Rows (✓ / — / Add-on):**

| Feature | Clinical | Regional | Network | Enterprise |
|---------|----------|----------|---------|------------|
| Core CMMS (assets, WO, PM calendar, reports, invoices, labor, requests) | ✓ | ✓ | ✓ | ✓ |
| Arabic + English RTL | ✓ | ✓ | ✓ | ✓ |
| Onboarding + CSV import + remote training | ✓ | ✓ | ✓ | ✓ |
| Mobile technician app (when launched) | ✓ | ✓ | ✓ | ✓ |
| Advanced Reporting & KPIs | Add-on | Add-on | ✓ | ✓ |
| AI Maintenance module | Standalone | Standalone | Standalone | Standalone |
| Systems Integration (HIS/ERP/SSO) | Standalone | Standalone | Standalone | Standalone |
| Dedicated database option | — | — | Quote | Quote |
| Business-hours support | ✓ | ✓ | ✓ | ✓ |
| Priority / expanded support | — | — | ✓ | ✓ |

**Limits row block under table:**

| | Clinical | Regional | Network | Enterprise |
|--|----------|----------|---------|------------|
| Assets | 500 | 5,000 | 10,000 | 20,000 |
| Users | 20 | 60 | 100 | 150 |
| Hospitals / sites | 1 | 15 | 40 | 85 |

---

### Slide 8 — Pricing

**Title:** Annual pricing — Egypt (EGP), setup included  

**Large tier cards:**

| Tier | Annual (EGP) | Best for |
|------|--------------|----------|
| **Orbit Clinical** | **420,000** | Single-hospital pilot |
| **Orbit Regional** | **1,050,000** | Multi-site FM (growth) |
| **Orbit Network** | **2,800,000** | Large hospital networks |
| **Orbit Enterprise** | **3,500,000** | National FM · up to 85 hospitals / 20K assets |

**Notes under cards:**
- VAT excluded  
- Setup, migration support, and 5 days remote training **included**  
- Band: floor **420K** · ceiling **3.5M**  
- Pilot option: Clinical at **50% year-1** for 1–2 reference customers (case study required)

**Compare line:** International CMMS often 2–3× higher + separate implementation fees.

---

### Slide 9 — Standalone modules (paid)

**Title:** Optional modules — priced separately  

**Two standalone products (not bundled):**

1. **AI Maintenance**  
   - Scope: AI-assisted PM recommendations, work planning hints, anomaly / priority suggestions  
   - Forecasting capability sits in this module as it matures  
   - Pricing: custom quote (annual) — **not** included in tier price  

2. **Systems Integration**  
   - Scope: HIS / ERP connectors, webhooks, SSO (SAML/OIDC) as packaged services  
   - Pricing: custom quote per connector / scope  

**Also show as package add-on (not standalone platform product):**  
- **Advanced Reporting pack** — for Clinical & Regional only (Network+ already includes)

**Emphasize:** Mobile app is **not** sold separately — it is **included** in all packages when released.

---

### Slide 10 — Why healthcare · Egypt

**Title:** Why hospital FM in Egypt  

**Bullets:**
- Asset-dense sites: 300–500 assets typical; large tenants to 20,000  
- FM outsourcing common — buyer is often the maintenance company  
- Localization wins: Arabic UX, Cairo timezone support, EGP contracts  
- Competitive set: Excel/WhatsApp + international CMMS (too costly / heavy)  
- Path: Clinical pilot → Network/Enterprise expansion

---

### Slide 11 — Go-to-market

**Title:** How we sell  

**Channels:**
- Direct outreach to FM companies serving hospitals  
- Demo-first: pitch environment + 30-minute golden path  
- Mix of network referrals + industry partners  
- Referral partners: **10–15% of year-1 ACV**  
- Later: certified implementers (20–25% + fixed fee)

**Timeline callout:** Target first paying customer within **6 months** (Clinical pilot).

---

### Slide 12 — Partner cost split (PARTNER SLIDE — not for end-customer)

**Title:** How ACV is split — partner edition  

**Purpose:** Transparent unit economics so partners trust margin and referral value.

**Pie or stacked bar — indicative year-1 ACV split (example Regional EGP 1.05M):**

| Bucket | Share of ACV | What it covers |
|--------|--------------|----------------|
| **Cloud & platform ops** | 12–18% | Hosting, DB, storage, CDN/WAF, backups, monitoring (AWS / Azure / Cloudflare hybrid TBD per deal) |
| **Onboarding & delivery** | 10–15% | Asset import, training, configuration (included in subscription) |
| **Support & success** | 8–12% | Business-hours support, bug triage, tenant health |
| **Product & R&D** | 20–25% | Continuous CMMS development, Arabic UX, mobile when shipped |
| **Sales & partner commission** | 10–15% | Direct CAC + referral (your 10–15% sits here on referred deals) |
| **Gross margin / runway** | 25–35% | Company sustainability, buffer for Enterprise COGS spikes |

**Second mini-table — COGS by tenant scale (infra orientation for partners):**

| Tenant profile | Relative infra load | Notes |
|----------------|---------------------|-------|
| Clinical (~500 assets) | Low | Shared multi-tenant DB |
| Regional (~5K) | Medium | Shared; watch attach storage |
| Network (~10K) | High | May need read tuning |
| Enterprise (~20K) | Highest | Dedicated DB optional (quote) |

**Speaker notes:** Cloud vendor (AWS vs Azure vs Cloudflare+managed Postgres) chosen per selection; default is shared multi-tenant. Multi-AZ / load balancers activate as tenants scale — costs are **usage-triggered** (compute hours, provisioned DB, ALB hours, storage GiB, egress).

---

### Slide 13 — Cloud options (partner / technical appendix slide)

**Title:** Hosting options — selection-based  

**Three columns (do not declare a winner):**

| | AWS | Azure | Cloudflare (+ managed Postgres) |
|--|-----|-------|----------------------------------|
| Fit for Orbit stack | Strong (RDS, ALB, S3) | Strong (Flexible Server, App LB) | Edge/CDN/R2 excellent; Postgres still external (e.g. Neon/RDS) |
| Multi-DB / dedicated | Native RDS per tenant | Native Flexible Server | Via Postgres vendor |
| Load balancing | ALB / NLB | Azure LB / App Gateway | Edge proxy + origin LB |
| Bill triggers | Instance-hours, Multi-AZ ~2× DB, ALB hours, storage, egress | Similar (vCore-hours + HA) | Workers/R2 usage + separate DB bill |
| When to pick | Default enterprise SaaS | Buyer is Microsoft-centric | WAF/CDN/zero-egress photos + separate DB |

**Footer:** Year-1 default architecture = **shared multi-tenant Postgres**; dedicated DB only on Network/Enterprise quotes.

---

### Slide 14 — Product family

**Title:** Orbit suite  

**Two product cards:**

**Orbit AM**  
Hospital Asset & Maintenance Management — multi-tenant CMMS + billing for FM companies and hospitals.

**Orbit QM**  
Quality Management Dashboard — manufacturing quality ops: IQC / IPQC / FQC, NCR, CAPA, SPC control charts, audits, traceability, supplier & calibration modules.

**Cross-sell line:** Same operating DNA (Arabic-ready SaaS, role-based ops dashboards) — assets/maintenance vs quality on the production floor.

---

### Slide 15 — Customers & traction

**Title:** In the field  

**Orbit QM — live customer**
- **Miraco** — Miraco Company for Air Conditioning & Refrigeration (Egypt)  
- Manufacturer associated with **Carrier & Midea** product lines  
- Uses Orbit QM for quality management: inspections (IQC/IPQC/FQC), NCR/CAPA, SPC charts, process & part specs, audits  

**Orbit AM**
- Pitch-ready demo environment  
- Pre-revenue · healthcare FM packaging live · pilots invited  

**Note:** No QM pricing on this slide.

---

### Slide 16 — Call to action

**Title:** Start a 90-day hospital pilot  

**Steps:**
1. Select **1 hospital** (~300–500 assets) → **Clinical**  
2. We import assets & configure PM schedules (included)  
3. Train up to **20 users** (included)  
4. Measure: PM compliance, WO cycle time, invoice accuracy  

**CTA block:** Book a demo · [email] · [phone]  

**Closing line:** Orbit AM — Maintain every asset. One orbit.

---

## Design system for the generator

- Fonts: Inter or similar geometric sans for UI; one distinctive display font for titles only (avoid Inter-as-only-brand if possible — e.g. Plus Jakarta / Manrope for UI, modest display for H1)
- Colors: deep teal `#0F766E` primary, slate `#0F172A` text, soft mist backgrounds; accent amber sparingly for CTAs
- Icons: line icons for modules; no emoji
- Tables: high contrast, zebra optional, bold package names
- Partner slides (12–13): labeled **“Partners”** in corner chip

## What NOT to invent

- Do not claim Maximo full parity  
- Do not claim AI is live  
- Do not publish Orbit QM prices  
- Do not lock AWS or Azure as “the” cloud  
- Do not put investor raise amounts on slides  

## Optional appendix slides (if tool allows +2)

A1. Full feature checklist Implemented / Partial / TBD  
A2. Overage: +1,000 assets / +10 users price cards (derive as ~10% of Regional annual per 1K assets ≈ guidance only)

---

*End of slide generation prompt.*
