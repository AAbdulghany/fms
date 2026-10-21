# MOBILE_FIRST_PILOT_PRD — Orbit AM

**Document type:** Product Requirements Document  
**Domain:** Mobile-First PWA Pilot Shell  
**Version:** 1.0  
**Date:** 2026-10-21  
**Author:** Mariam (PM)  
**Status:** Draft — pending ManWinWin gap matrix ratification

---

## Table of contents

1. [Problem statement](#1-problem-statement)
2. [Goals & success](#2-goals--success)
3. [Non-goals](#3-non-goals)
4. [Personas](#4-personas)
5. [User journeys](#5-user-journeys)
6. [Acceptance criteria — pilot shell](#6-acceptance-criteria--pilot-shell)
7. [Feature backlog (MoSCoW)](#7-feature-backlog-moscow)
8. [ManWinWin gap alignment](#8-manwinwin-gap-alignment)
9. [Success metrics](#9-success-metrics)
10. [Open questions](#10-open-questions)

---

## 1. Problem statement

### Context

Orbit AM is a multi-tenant CMMS SaaS built for FM/maintenance companies serving hospitals in Egypt. The core platform runs as a desktop-first React SPA. The pitch pack packages mobile as **included in every tier when launched** (§4.4, §5) — it is a contractually expected capability, not optional.

### Field reality

Hospital maintenance work happens on floors, in equipment rooms, and across sites. Technicians rarely sit at a desktop. The current workflow forces field staff to:

1. Receive paper or WhatsApp WO assignments.
2. Walk to a supervisor's PC to update status.
3. Miss the structured report / approval loop entirely.

This creates data lag, compliance gaps, and invoice inaccuracy — all of which reduce Orbit AM's value prop at the very moment a pilot hospital is watching.

### Architectural decision (locked)

**Decision 1A** (locked): Responsive web + installable PWA for the pilot. Desktop layouts remain first-class. **Decision 1C** (locked): Native app deferred to a later horizon.

### The gap

The current React codebase has no mobile shell, no bottom navigation, no touch-first list→detail patterns, and no offline-install prompt. First hospital pilot conversations will surface this gap within the first demo day.

---

## 2. Goals & success

### Pilot goals (6-month horizon)

| # | Goal | Measurable form |
|---|------|-----------------|
| G1 | Technicians can open, action, and submit a WO entirely from a mobile browser | ≥80% of pilot WO submissions via mobile in month 3 |
| G2 | PWA is installable on Android Chrome and iOS Safari | Zero "how do I install?" support tickets during pilot |
| G3 | RTL (Arabic) and LTR (English) both render correctly at ≤375 px viewport | 0 RTL layout regressions in QA sweep |
| G4 | Offline install banner fires on first visit; app shell loads without network on re-open | Lighthouse PWA score ≥ 80 |
| G5 | Site manager gets a mobile summary view of open WOs per site | Site manager uses mobile dashboard weekly during pilot |

### Scope boundary

This PRD covers the **pilot shell** — the structural mobile layer. Feature depth (AI, reporting, full asset management) is out of scope for this cycle.

---

## 3. Non-goals

| Non-goal | Rationale |
|----------|-----------|
| Native iOS/Android app | Decision 1C — deferred |
| Offline-first full data sync | Pilot = hospital WiFi assumed available; offline shell only |
| Push notifications | Needs production SMTP/FCM; separate ticket |
| Camera-based QR scanning for assets | Nice-to-have; not pilot blocker |
| Advanced KPI dashboard on mobile | Reporting module is Network+ tier add-on |
| Parts / inventory management on mobile | Not in Wave 5 scope |
| Mobile-specific backend changes | PWA consumes existing REST API; no new endpoints this cycle |

---

## 4. Personas

### P1 — Faris (Field Technician)

| Attribute | Detail |
|-----------|--------|
| Role in system | `technician` |
| Device | Personal Android phone (mid-range, 4G or hospital WiFi) |
| Language | Arabic primary; can read English labels |
| Technical fluency | Low–medium; WhatsApp-native |
| Core job on mobile | See assigned WOs → navigate to asset → update status → fill report → submit |
| Pain today | Gets WO number via WhatsApp; must find a PC to update the system |
| Definition of done | Submitted WO from phone without asking supervisor for help |

### P2 — Nour (Site Manager)

| Attribute | Detail |
|-----------|--------|
| Role in system | `site_manager` |
| Device | Mix: laptop at desk, Android phone during floor rounds |
| Language | Arabic; comfortable with English tech UI |
| Technical fluency | Medium–high |
| Core job on mobile | Check open WO backlog per site, spot overdue items, reassign if needed |
| Pain today | Needs laptop for any meaningful oversight; floor decisions are blind |
| Definition of done | Opened mobile app during a floor walk and reassigned a WO without returning to desk |

### P3 — Khaled (Company Admin)

| Attribute | Detail |
|-----------|--------|
| Role in system | `company_admin` |
| Device | Desktop primary; iPhone secondary |
| Language | Arabic + English |
| Technical fluency | High |
| Core job on mobile | Approve submitted reports, check outstanding invoices, glance at site-level WO counts |
| Pain today | Report approval requires laptop; delays billing cycle |
| Definition of done | Approved a submitted report from iPhone without switching to laptop |

---

## 5. User journeys

### Journey J1 — Faris completes a corrective WO in the field

```
[Notification/WhatsApp] → Opens Orbit AM in Chrome on phone
        ↓
[PWA install banner fires on first visit] → optionally installs
        ↓
[Bottom nav → Work Orders tab]
        ↓
[Assigned WO list] → taps card "Replace IV pump filter — Ward 3B"
        ↓
[WO detail screen — mobile layout]
  • Asset name + location displayed prominently
  • Status chip: "Assigned"
        ↓
[Taps "Start work" → status → In Progress]
        ↓
[Report tab] → fills structured report fields (Arabic labels)
        ↓
[Taps "Submit for approval"] → success toast
        ↓
[Returns to WO list — WO shows "Submitted" badge]
```

**Success signal:** Full loop completed without desktop.  
**ManWinWin gap closed:** Technician adoption lag (2–6 months risk per §7.3 TCO)

---

### Journey J2 — Nour reviews her site's open backlog during a floor round

```
[Opens installed PWA from home screen]
        ↓
[Dashboard / Home tab — site summary card]
  • Open WOs: 12  |  Overdue: 2  |  In Progress: 7
        ↓
[Taps "Overdue" pill → filtered WO list]
        ↓
[Sees "Steriliser boiler PM — overdue 3 days"]
  → taps to open detail
        ↓
[Unassigned — taps "Assign"] → picks Faris from technician list
        ↓
[WO saved — returns to list]
        ↓
[Sends WhatsApp to Faris referencing WO number] (out of app — real world)
```

**Success signal:** Assignment made from phone in under 60 seconds.  
**ManWinWin gap closed:** PM compliance tracking at site level.

---

### Journey J3 — Khaled approves a report and triggers an invoice

```
[Email notification: "Report submitted — WO #1047"] (future; for now: opens app directly)
        ↓
[Bottom nav → Work Orders → filter "Submitted"]
        ↓
[Taps WO #1047 → Report tab]
  • Full structured report rendered on mobile
  • Scroll to review all fields
        ↓
[Taps "Approve report"]
  • Confirm dialog: "This will mark the report approved and enable invoice generation."
  • Taps Confirm
        ↓
[Report status → Approved — success toast]
        ↓
[Taps "Generate Invoice"] → invoice PDF created
  • "Invoice created — view in Invoices" toast
        ↓
[Navigates to Invoices tab — sees new invoice with PDF download link]
```

**Success signal:** Full approval + invoice loop completed from mobile.  
**ManWinWin gap closed:** Invoice accuracy and billing cycle delay.

---

## 6. Acceptance criteria — pilot shell

The following criteria define the **minimum shippable pilot shell**. All must be green before the first hospital demo.

### AC-01 — Bottom navigation

| ID | Criterion | Test method |
|----|-----------|-------------|
| AC-01-a | Bottom nav is visible and sticky on all screens at viewport ≤ 768 px | Manual + Playwright at 375 px |
| AC-01-b | Bottom nav tabs: Home (dashboard), Work Orders, Assets, Invoices, Menu | Visual regression screenshot |
| AC-01-c | Active tab is visually distinct (filled icon + label highlight) | Visual |
| AC-01-d | Bottom nav is hidden at viewport > 1024 px (desktop sidebar takes over) | Playwright at 1440 px |
| AC-01-e | Nav renders correctly in RTL (tabs in natural reading order right→left) | Manual RTL toggle + screenshot |

### AC-02 — List → Detail pattern

| ID | Criterion | Test method |
|----|-----------|-------------|
| AC-02-a | WO list renders as a card stack at ≤ 768 px (not a data table) | Playwright viewport check |
| AC-02-b | Each card shows: WO title, status chip, asset name, assigned-to, date | Visual |
| AC-02-c | Tapping a card navigates to WO detail page | Playwright click test |
| AC-02-d | WO detail page has a back button / swipe-back gesture hint | Manual |
| AC-02-e | List and detail share the same data source (no mobile-only API) | Code review |
| AC-02-f | Asset list follows same card pattern at ≤ 768 px | Visual |

### AC-03 — RTL (Arabic) layout

| ID | Criterion | Test method |
|----|-----------|-------------|
| AC-03-a | Switching language to AR flips all layout directions (flex-row, padding, margins) | Playwright LTR/RTL snapshot diff |
| AC-03-b | Arabic text renders with correct font (not fallback serif) | Screenshot inspection |
| AC-03-c | Icons do not mirror (directional icons: back arrow mirrors; non-directional: do not) | Visual |
| AC-03-d | Form inputs accept Arabic text input on mobile keyboard | Manual |
| AC-03-e | Status chips and badge labels have Arabic translations | i18n key audit |
| AC-03-f | Bottom nav labels render in Arabic at ≤ 375 px without truncation | Screenshot at 375 px |

### AC-04 — Offline install banner

| ID | Criterion | Test method |
|----|-----------|-------------|
| AC-04-a | A web manifest (`manifest.json`) exists with `name`, `short_name`, `icons` (192+512 px), `start_url`, `display: standalone`, `theme_color`, `background_color` | `lighthouse --preset=pwa` |
| AC-04-b | A service worker registers and caches the app shell on first load | DevTools Application tab |
| AC-04-c | `InstallOrbitBanner` component renders on first visit when the browser fires `beforeinstallprompt` | Playwright PWA install simulation |
| AC-04-d | Banner is dismissible and does not re-appear for 7 days after dismissal | localStorage check |
| AC-04-e | App shell loads without network after install (blank/spinner is a failure) | DevTools offline mode |
| AC-04-f | iOS Safari displays "Add to Home Screen" meta tag prompt (no `beforeinstallprompt` on iOS) | Manual iPhone test or BrowserStack |
| AC-04-g | App icons appear on home screen after install (both 192 and 512 present) | Manual install on Android Chrome |

---

## 7. Feature backlog (MoSCoW)

> ManWinWin gap references use `[MWW-xx]` tags — these will be linked to `MANWINWIN_GAP_MATRIX.md` once it is written. Where that file is absent, the pitch pack §3.2 gap codes are used.

### Must Have — Pilot shell (Wave: mobile shell start)

| ID | Feature | ManWinWin gap | Notes |
|----|---------|---------------|-------|
| M-01 | Responsive breakpoint system (≤ 768 px cards, ≥ 1024 px desktop) | [MWW-MOB] Technician adoption | Tailwind `sm`/`md`/`lg` breakpoints; audit all pages |
| M-02 | Bottom navigation component (Home / WOs / Assets / Invoices / Menu) | [MWW-MOB] | New component; replaces sidebar on mobile |
| M-03 | WO card list layout (mobile) | [MWW-MOB] | Replace table with card stack at mobile BP |
| M-04 | WO detail — mobile-optimised layout | [MWW-MOB] | Single-column, large tap targets (min 44 px) |
| M-05 | Asset card list layout (mobile) | [MWW-MOB] | Same card pattern as WO |
| M-06 | PWA manifest + app icons (192, 512, maskable) | [MWW-INST] Install capability | Icons already in `/public/icons`; wire manifest |
| M-07 | Service worker — app shell caching | [MWW-INST] | Vite PWA plugin or manual SW |
| M-08 | `InstallOrbitBanner` component | [MWW-INST] | Hook `usePwaInstall` already scaffolded |
| M-09 | RTL audit pass — all mobile views | [MWW-AR] Arabic UX differentiator | Automated Playwright RTL snapshot regression |
| M-10 | Touch-friendly form inputs (min 44 px hit areas, large selects) | [MWW-MOB] | Global Tailwind utility pass |
| M-11 | WO status update from mobile (In Progress → Completed) | [MWW-WO] WO golden path E2E | Reuses existing API; verify on mobile |
| M-12 | Report submit from mobile (field report entry + submit) | [MWW-RPT] Hospital report templates | Critical for compliance value prop |

### Should Have — Pilot depth (Wave: mobile shell + 2)

| ID | Feature | ManWinWin gap | Notes |
|----|---------|---------------|-------|
| S-01 | Site manager mobile dashboard (open / overdue / in-progress counts) | [MWW-KPI] Site oversight | Reuses existing summary API |
| S-02 | Company admin report approval from mobile | [MWW-RPT] | Reuses approval endpoint |
| S-03 | Invoice list mobile view + PDF download link | [MWW-INV] Invoice golden path | Reuses invoice API |
| S-04 | Offline-capable WO list (read cache only — no write offline) | [MWW-CONN] Low-connectivity wards | Service worker cache strategy |
| S-05 | WO assignment action from mobile (site manager persona) | [MWW-WO] | Reuses PATCH /work-orders endpoint |
| S-06 | Asset detail mobile view (info + maintenance history tab) | [MWW-AST] Wave 5 asset cleanup | Post wave-5 cleanup; depends on NT-P5-A07-FE |
| S-07 | Language toggle persisted across sessions | [MWW-AR] | localStorage; small effort |
| S-08 | Pull-to-refresh on list views | [MWW-MOB] UX polish | Standard mobile pattern |

### Could Have — Post-pilot enrichment

| ID | Feature | Notes |
|----|---------|-------|
| C-01 | Camera / QR scan to open asset detail | Requires HTML5 camera API; Android Chrome works, iOS Safari limited |
| C-02 | Mobile photo attachment on WO report | `<input type="file" capture="environment">` on mobile |
| C-03 | Push notifications (WO assigned, report approved) | Requires production SMTP/FCM; separate phase |
| C-04 | Haptic feedback on status change (mobile) | Minor delight; Chrome Vibration API |
| C-05 | Swipe gestures on card list (swipe right = quick-complete) | Polish; assess after pilot feedback |
| C-06 | Offline WO status write + sync queue | Full offline-first; significant complexity |

### Won't Have — This cycle

| ID | Feature | Reason |
|----|---------|--------|
| W-01 | Native iOS / Android app | Decision 1C locked |
| W-02 | AI maintenance recommendations on mobile | Standalone product; not pilot scope |
| W-03 | Parts/inventory management | Not in CMMS core v1 |
| W-04 | Custom hospital report template builder (mobile) | Desktop authoring; mobile consumption only |
| W-05 | Advanced KPI dashboards | Network+ tier add-on |
| W-06 | Systems integration (HIS/ERP) | Standalone product |

---

## 8. ManWinWin gap alignment

> *Note: `MANWINWIN_GAP_MATRIX.md` was not present at PRD authoring time. The gap codes below are provisional, derived from the pitch pack §3.2 and Wave 5 findings. Reconcile and update IDs when the gap matrix is written.*

| Gap code | Gap description | Pitch pack / Wave 5 source | Mobile features addressing it |
|----------|----------------|---------------------------|-------------------------------|
| MWW-MOB | No mobile interface for field staff | Pitch §3.1 "Mobile app: TBD" | M-01 through M-05, M-10 |
| MWW-INST | App not installable as PWA | Pitch §3.1 | M-06, M-07, M-08 |
| MWW-AR | RTL layout gaps at narrow viewports | Pitch §1 "Arabic-first RTL UX" | M-09, S-07 |
| MWW-WO | WO lifecycle not accessible in field | Wave 5 NT-P5-A01 (WO scoping) | M-11, S-05 |
| MWW-RPT | Report submission / approval delayed | Pitch §3.2 "Hospital report templates" | M-12, S-02 |
| MWW-INV | Invoice cycle delayed by desktop dependency | Pitch §3.2 "Invoice E2E green" | S-03 |
| MWW-KPI | No site-level visibility for managers in field | Pitch §3.3 Reporting (Phase 2) | S-01 |
| MWW-AST | Asset data quality on mobile compromised | Wave 5 NT-P5-A07-FE (asset detail header) | S-06 |
| MWW-CONN | Hospital ward WiFi unreliable | Pitch §7.3 "Technician adoption 2–6 months" | S-04 |

---

## 9. Success metrics

### Leading indicators (during pilot — months 1–3)

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| WO submissions via mobile | ≥ 50% of total in month 1; ≥ 80% by month 3 | Backend `user_agent` log analysis |
| PWA install rate (among pilot users) | ≥ 60% of technician accounts | `beforeinstallprompt` accepted event; install beacon |
| Report submission time (field to submitted) | ≤ 4 hours median (vs. next-day baseline) | `created_at` vs `submitted_at` delta on WO reports |
| Mobile session bounce rate | ≤ 40% | GA / Plausible event tracking |
| RTL layout defects filed during pilot | 0 critical, ≤ 3 minor | Issue tracker |

### Lagging indicators (end of pilot — month 6)

| Metric | Target | Measurement method |
|--------|--------|--------------------|
| PM compliance rate (planned vs completed) | ≥ 85% | CMMS report (existing) |
| Invoice accuracy (no disputes due to data lag) | 100% during pilot | Invoice review with hospital FM contact |
| Pilot hospital renewal signal | Letter of intent or verbal commit to Clinical tier | Sales tracking |
| Technician satisfaction (informal survey) | ≥ 7/10 ease of use | Founder-run 5-question WhatsApp survey |

### Technical health gates

| Gate | Standard |
|------|---------|
| Lighthouse PWA score | ≥ 80 |
| Lighthouse mobile performance | ≥ 70 (LCP ≤ 3.5 s on 4G throttle) |
| Lighthouse accessibility | ≥ 90 |
| `npm run build` passes with 0 type errors | Always |
| RTL Playwright snapshot regression | 0 failures on main branch |

---

## 10. Open questions

| # | Question | Owner | Due | Default if unresolved |
|---|----------|-------|-----|----------------------|
| OQ-01 | Does the pilot hospital use Android, iOS, or both? Affects PWA install path testing priority. | Founder / sales | Before shell dev starts | Test both; prioritise Android Chrome |
| OQ-02 | Should the offline install banner be bilingual (AR + EN) at first render, or detect browser locale? | Design/PM | Week 1 mobile sprint | Browser locale detection with AR fallback |
| OQ-03 | Is bottom nav the right pattern for company admin (power user with many tabs)? Consider hamburger menu + bottom nav hybrid. | UX | Design sprint | Bottom nav 4 tabs + overflow menu for admin-only actions |
| OQ-04 | ManWinWin gap matrix — which gaps are customer-validated vs assumed? | Founder | During gap analysis run | Use provisional codes from this PRD |
| OQ-05 | What is the hospital's minimum supported Android version? | Sales / pilot contact | Before QA | Android 8+ (Chrome 88+) |
| OQ-06 | Service worker caching strategy: network-first or cache-first for API calls? | Engineering | Architecture spike | Network-first with stale-while-revalidate for lists |
| OQ-07 | Should WO status transitions require connectivity (no offline write in v1)? | PM + Engineering | Sprint 1 | Yes — no offline writes in pilot shell (S-04 = read cache only) |
| OQ-08 | Are mascot/brand icons included in the PWA manifest icon set, or generic? | Design | Before M-06 | Use `orbit` brand icons already in `/public/icons` |
| OQ-09 | Wave 5 FE tasks (NT-P5-C01-FE through A07-FE) are still Open — do they block mobile shell work? | Tech Lead | Immediate | No hard block; schedule mobile shell in parallel; asset detail mobile (S-06) waits for A07-FE |
| OQ-10 | Does the 90-day hospital pilot offer (§13) include a formal mobile demo? | Founder | Before pitch | Yes — include mobile demo in golden path script |

---

## Appendix A — Wave sequence map

```
Wave: artifacts → cleanup → mobile shell start
        │               │               │
        │               │               └─ M-01..M-12 (Must Have shell)
        │               └─ Wave 5 FE remaining open tasks (NT-P5-C01-FE...A07-FE)
        └─ This PRD + EDUCATIONAL_MENTOR_TRACKS.md
```

## Appendix B — Files already scaffolded

The following files exist in the repo and relate to this PRD:

| File | Purpose |
|------|---------|
| `src/features/pwa/InstallOrbitBanner.tsx` | M-08 install banner component |
| `src/features/pwa/usePwaInstall.ts` | M-08 install hook |
| `public/icons/favicon.svg` | Base icon; scale to 192/512 for manifest |
| `public/icons/icon-192.png` | M-06 manifest icon |
| `public/icons/icon-512.png` | M-06 manifest icon |
| `public/icons/icon-maskable-192.png` | M-06 maskable icon |
| `public/icons/icon-maskable-512.png` | M-06 maskable icon |
| `public/icons/apple-touch-icon.png` | M-06 iOS Safari "Add to Home Screen" |

---

*Companion document: `EDUCATIONAL_MENTOR_TRACKS.md` — weekly learning outcomes mirroring this delivery.*  
*Depends on: `MANWINWIN_GAP_MATRIX.md` (update gap codes when available).*
