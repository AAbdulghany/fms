# EDUCATIONAL_MENTOR_TRACKS — Orbit AM Mobile Pilot Cycle

**Document type:** Founder learning programme — parallel mentor tracks  
**Delivery cycle:** Mobile-first PWA pilot (aligned to `MOBILE_FIRST_PILOT_PRD.md`)  
**Date:** 2026-10-21  
**Author:** Mariam (PM)

---

## Purpose

These three tracks let the founder **learn by building**. Each track mirrors a real delivery milestone in the mobile pilot so that every lesson is grounded in a decision you've already made or work you've already shipped. Reading without doing is skimmed; doing without framing is not retained. This programme does both in parallel.

**Design principle:** A working artifact is the learning proof, not a quiz or certificate.

---

## How to use these tracks

1. Run all three tracks **in parallel** — one week at a time.
2. At the end of each week, confirm the **working artifact** exists before moving to the next.
3. Tracks are intentionally unequal in depth — Product is the lightest each week; Engineering is the heaviest. Adjust pace if you are the sole implementer.
4. Each track ends with a **retrospective prompt** — spend 15 minutes writing answers. These accumulate into investor / partner narrative over time.

---

## Track overview

| Track | Persona | Cadence | Weekly artifact |
|-------|---------|---------|-----------------|
| **A — Product** | Founder as PM | 2–3 hrs/week | Decision log + updated PRD section |
| **B — Design / UX Writing** | Founder as Designer | 3–4 hrs/week | Screen spec or copy patch |
| **C — Engineering** | Founder as Tech Lead | 4–6 hrs/week | Merged code + passing tests |

---

## Track A — Product Management

> *Delivery mirror: Problem → Strategy → Backlog refinement → Metrics review*

### Week 1 — Problem framing & persona validation

**Delivery milestone:** First pass of `MOBILE_FIRST_PILOT_PRD.md` is written.

**Learning outcomes:**
- Distinguish a *problem statement* from a *solution brief* — write one of each for Orbit AM mobile.
- Name the three pilot personas (Faris, Nour, Khaled) and state their **single most important job-to-be-done** without referencing the system.
- Understand **MoSCoW prioritisation**: explain why M-06 (PWA manifest) is Must Have but C-01 (QR camera scan) is Could Have, in terms of risk to the pilot.

**Working artifact:**  
`MOBILE_FIRST_PILOT_PRD.md` exists with sections 1–4 (Problem, Goals, Non-goals, Personas) completed and reviewed by a peer or mentor.

**Resource:**  
Read: *Inspired* by Marty Cagan — chapters 1–3 (or 30-minute summary). Focus on the difference between output and outcome.

**Retrospective prompt:**  
> "If the pilot hospital asked me to demo the mobile app in 10 days, which three features would I show and why?"

---

### Week 2 — Acceptance criteria craft

**Delivery milestone:** AC-01 through AC-04 in PRD §6 are written and reviewed.

**Learning outcomes:**
- Write acceptance criteria in **testable, observable** terms (avoid "should feel fast"; write "LCP ≤ 3.5 s on 4G throttle").
- Understand the difference between *functional* ACs (AC-02: list renders as card stack) and *non-functional* ACs (AC-03-a: layout flips in RTL).
- Know why RTL is a first-class AC, not a QA afterthought — connect it to the "Arabic-first" value prop.

**Working artifact:**  
Pull request or internal doc where at least one AC from AC-03 (RTL) has been reviewed with the engineering track and turned into a Playwright test name.

**Resource:**  
Read: *User Story Mapping* by Jeff Patton — the "acceptance criteria are not test cases" section.

**Retrospective prompt:**  
> "What would a failure in AC-04-e (app shell loads offline) cost us during the first hospital demo? How would we recover?"

---

### Week 3 — MoSCoW backlog with gap traceability

**Delivery milestone:** Feature backlog (PRD §7) is written with ManWinWin gap codes. At least 5 Must Have items have a linked wave 5 task ID or pitch pack gap.

**Learning outcomes:**
- Use a gap matrix (ManWinWin or equivalent) as a **source of truth** for prioritisation — not gut feel.
- Explain why "Won't Have" is as important as "Must Have" in a pilot — find one item you are tempted to build that should stay in W-xx.
- Understand the difference between **PM's job** (define the what and why) and **engineering's job** (the how) — practise staying on your side of that line in backlog reviews.

**Working artifact:**  
`MANWINWIN_GAP_MATRIX.md` exists (or is partially filled); at least one row cross-references a mobile Must Have item from this PRD.

**Resource:**  
Read: Lean Startup chapter on validated learning. Connect: each Must Have item is a hypothesis about pilot user behaviour.

**Retrospective prompt:**  
> "Which gap am I most uncertain about? What is the cheapest way to test that assumption before we write the code?"

---

### Week 4 — Success metrics & pilot KPI baseline

**Delivery milestone:** PRD §9 (success metrics) is discussed with the intern team. A baseline is captured: current WO submission time, current report approval lag.

**Learning outcomes:**
- Distinguish **leading** from **lagging** indicators — give one of each for the mobile pilot.
- Understand why *mobile session bounce rate* is a leading signal for adoption risk, not just a vanity metric.
- Know how to define a **Lighthouse PWA score gate** and why ≥ 80 is the floor, not the goal.

**Working artifact:**  
A shared note or spreadsheet with the baseline numbers captured from production (or demo seed data) for: WO submission time median, report approval lag median.

**Resource:**  
Read: *Measure What Matters* (OKR) — chapter on confidence scores. Apply: for each pilot success metric, assign a confidence score (0–100%) that you will hit it.

**Retrospective prompt:**  
> "If WO mobile submissions are at 30% by month 3 (target 80%), what are the two most likely root causes and what would I do?"

---

### Week 5 — Open questions triage & decision log

**Delivery milestone:** OQ-01 through OQ-10 in PRD §10 are triaged. At least 4 have an answer, an owner, and a due date.

**Learning outcomes:**
- Practise **decision logging** — for each resolved OQ, write a one-line rationale that a future team member can understand without asking you.
- Understand the cost of deferred decisions (OQ-09: do Wave 5 FE tasks block mobile? Deciding late blocks the sprint).
- Learn **when to default** (OQ-06: caching strategy) vs. when to run a spike (OQ-02: bilingual install banner).

**Working artifact:**  
`MOBILE_FIRST_PILOT_PRD.md` §10 updated with 4+ resolved open questions, each with a decision rationale note.

**Retrospective prompt:**  
> "Which open question, if answered wrongly, would hurt the pilot the most? What would I need to know to answer it correctly?"

---

### Week 6 — Pilot readiness review

**Delivery milestone:** Must Have items M-01 through M-12 are either shipped or have a clear owner + ETA.

**Learning outcomes:**
- Run a **go / no-go** decision against the 5 goals in PRD §2 — be honest about which are green, amber, and red.
- Write a 3-sentence pilot readiness summary to a non-technical stakeholder (the hospital FM director).
- Understand the PM's role in a **demo day** — what you control (framing, narrative, fallbacks) and what you do not (live bugs, WiFi).

**Working artifact:**  
A one-page "pilot readiness note" (can be a GitHub issue or Notion page) sent to the first hospital contact.

**Retrospective prompt:**  
> "What would I do differently if I were writing this PRD from scratch with the knowledge I have now?"

---

## Track B — Design / UX Writing

> *Delivery mirror: Mobile layout → RTL copy → Install moment → Component polish*

### Week 1 — Mobile layout principles

**Delivery milestone:** Wireframe (low-fi, even paper/Figma) of the bottom nav and WO card for Faris's journey (J1).

**Learning outcomes:**
- Apply the **44 px minimum tap target** rule — identify every interactive element in the WO card that violates it today.
- Understand **progressive disclosure** on mobile: the card shows the minimum; the detail shows the full picture.
- Know the difference between **mobile-first** (design small then scale up) and **responsive** (design desktop then break it). Orbit AM is currently the latter — learn the cost of retrofitting.

**Working artifact:**  
A Figma frame (or annotated screenshot) of the WO card at 375 px with tap targets highlighted and one note per violation.

**Resource:**  
Read: Material Design 3 — "Touch targets" guidelines. Read: Apple HIG — "Layout" section on compact size class.

**Retrospective prompt:**  
> "If Faris has one hand free (holding a tool), what is the most common action he needs to do? Is it reachable with his thumb?"

---

### Week 2 — RTL layout & Arabic UX writing

**Delivery milestone:** The bottom nav component (M-02) has its Arabic label set reviewed and approved. At least one RTL screenshot is compared against the LTR version.

**Learning outcomes:**
- Understand **bidirectional text** rules: numbers stay LTR inside RTL text; icons with direction must mirror; icons without direction do not.
- Write Arabic UI copy for the 4 bottom nav labels and 3 status chips (Assigned, In Progress, Submitted) — check with a native speaker or Google Translate + back-translation.
- Know the difference between **`dir="rtl"` on the HTML element** and Tailwind's `rtl:` variant — when each applies.

**Working artifact:**  
A copy patch (PR or doc) for the 4 bottom nav labels and 5 WO status chips with EN + AR strings, reviewed.

**Resource:**  
Read: MDN "Making pages work in RTL using CSS logical properties". Read: W3C "Authoring HTML: Handling Right-to-left Scripts".

**Retrospective prompt:**  
> "Which Arabic word choice was hardest? Why? What does that tell you about the domain vocabulary the pilot users will already know?"

---

### Week 3 — PWA install moment design

**Delivery milestone:** `InstallOrbitBanner` component has a reviewed copy + visual design at 375 px in both AR and EN.

**Learning outcomes:**
- Understand the **install moment** as a conversion event: it competes with the user's task (opening a WO). The banner must be frictionless or it fails.
- Write a **value-first** install prompt: "Get instant access to your work orders — add Orbit to your home screen." (AR equivalent.)
- Know the difference between browser-native install prompts (Android Chrome) and manual prompts (iOS Safari) — design for both.

**Working artifact:**  
`InstallOrbitBanner.tsx` has its copy strings updated from placeholder text to reviewed production copy in EN + AR. Screenshot at 375 px attached to PR.

**Resource:**  
Read: Google "What makes a good install prompt?" (web.dev PWA series).

**Retrospective prompt:**  
> "If a user taps Dismiss on the install banner, what does that tell you? What would you change after 10 dismissals in a row?"

---

### Week 4 — Empty states & error copy (mobile)

**Delivery milestone:** The WO list empty state (no WOs assigned) and a network error state have reviewed copy in EN + AR.

**Learning outcomes:**
- Write **useful empty states**: explain *why* the screen is empty and give one actionable next step.
- Distinguish **error** (something went wrong — system fault) from **empty** (nothing here yet — data state). They need different copy and different visual weight.
- Understand that a blank white card at 375 px looks like a broken app to a first-time user. Visual pattern + copy together prevent churn.

**Working artifact:**  
Two new i18n keys (`workOrders.emptyState.noAssigned`, `workOrders.error.networkFail`) in `src/i18n/index.ts` with EN + AR strings.

**Resource:**  
Read: *Writing Is Designing* by Michael Metts — the empty state chapter.

**Retrospective prompt:**  
> "Which user (Faris, Nour, Khaled) is most likely to see an empty state? What is their emotional state when they see it?"

---

### Week 5 — Report form UX on mobile

**Delivery milestone:** The report entry form (for J1 journey) is reviewed for mobile at 375 px. At least 3 field labels are improved for Arabic field-tech clarity.

**Learning outcomes:**
- Understand the cost of **long forms on mobile** — chunking, progress indicators, auto-save patterns.
- Know when to use `<textarea>` vs. a structured radio/select for field data — and why structured data > free text for compliance reports.
- Practise **plain language** in form labels: "Diagnosis" → "What was the fault?" (AR: "ما هو العطل؟")

**Working artifact:**  
A reviewed list of all form field labels on the WO report with: current label | proposed label | EN | AR | rationale.

**Retrospective prompt:**  
> "Which form field is most likely to be skipped by a technician in a hurry? What would you do about it?"

---

### Week 6 — Design QA pass

**Delivery milestone:** All M-01 through M-12 Must Have items pass a visual design review against the acceptance criteria screenshots.

**Learning outcomes:**
- Run a **design QA checklist**: tap targets, colour contrast (AA minimum), font sizes (≥ 16 px body), RTL parity, icon labels.
- Understand the difference between **pixel-perfect** (wrong goal for web) and **design-token consistent** (right goal) — every colour and spacing value should trace back to `tokens.css`.
- File at least one design bug against a shipped feature — practise giving a precise bug report: screenshot + expected vs. actual + Figma reference.

**Working artifact:**  
A GitHub issue or Notion checklist with design QA results for the mobile shell, flagging ≥ 1 real issue.

**Retrospective prompt:**  
> "What design decision made during Week 1 turned out to be wrong by Week 6? What would you change?"

---

## Track C — Engineering

> *Delivery mirror: PWA setup → Mobile layout → RTL → List→Detail → Acceptance testing*

### Week 1 — PWA foundation

**Delivery milestone:** `manifest.json` exists at `/public/manifest.json`, is linked from `index.html`, and passes `lighthouse --preset=pwa` with no manifest errors.

**Learning outcomes:**
- Understand the **PWA checklist**: manifest, service worker, HTTPS, icons — know what each one does and what breaks without it.
- Read the Vite PWA plugin (`vite-plugin-pwa`) docs — understand the tradeoff between the plugin and a hand-rolled service worker.
- Know the difference between `display: standalone`, `display: minimal-ui`, and `display: browser` in the manifest.

**Working artifact:**  
PR: `feat/pwa-manifest` — adds `manifest.json`, links it, adds `<meta name="apple-mobile-web-app-capable">` for iOS, passes Lighthouse PWA check.

**Resource:**  
Read: web.dev "Add a web app manifest". Read: Vite PWA plugin README.

**Retrospective prompt:**  
> "What is the single biggest reliability risk of a service worker caching strategy in a multi-tenant app like Orbit AM?"

---

### Week 2 — Service worker & install hook

**Delivery milestone:** Service worker registers, caches app shell (HTML, CSS, JS). `usePwaInstall.ts` hook wires `beforeinstallprompt` and exposes `triggerInstall()`. `InstallOrbitBanner.tsx` renders and dismisses.

**Learning outcomes:**
- Understand **cache strategies**: Cache First (static assets), Network First (API), Stale-While-Revalidate (list data) — when to use each.
- Know the **service worker lifecycle**: install → activate → fetch intercept. Debug a failed cache in DevTools Application tab.
- Understand why `beforeinstallprompt` does not fire on iOS — and what the fallback UX is.

**Working artifact:**  
PR: `feat/pwa-sw-install` — service worker registers, app shell cached, install banner shows + dismisses with 7-day suppression.

**Resource:**  
Read: Jake Archibald "The Offline Cookbook" (web.dev). Read: MDN `beforeinstallprompt` docs.

**Retrospective prompt:**  
> "If a technician installs the PWA on Monday and you deploy a new build on Tuesday, when does their installed app update? Is that acceptable?"

---

### Week 3 — Mobile breakpoints & bottom nav

**Delivery milestone:** Bottom nav component is built (AC-01 green). All existing page layouts use the Tailwind breakpoint system at ≤ 768 px (no horizontal scroll at 375 px).

**Learning outcomes:**
- Audit the codebase for **Tailwind breakpoint anti-patterns** (`w-full` assumed desktop, tables without scroll containers, `flex-row` with no wrap).
- Understand `safe-area-inset-bottom` on iOS notched devices — bottom nav must not be obscured by the home indicator.
- Know the difference between **`hidden md:flex`** (hide on mobile) and a proper mobile-first component hierarchy.

**Working artifact:**  
PR: `feat/mobile-nav` — `BottomNav.tsx` component, hidden at ≥ 1024 px, RTL-aware, passes AC-01 Playwright tests.

**Resource:**  
Read: Tailwind CSS "Responsive design" docs. Read: CSS Tricks "A Complete Guide to Flexbox" — focus on `flex-wrap` and `gap`.

**Retrospective prompt:**  
> "What is the most common layout bug you found in the audit? What Tailwind utility caused it and how did you fix it?"

---

### Week 4 — WO card list & list→detail pattern

**Delivery milestone:** WO list renders as card stack at ≤ 768 px (AC-02 green). Cards navigate to WO detail on tap. Asset list uses same pattern.

**Learning outcomes:**
- Understand **React Router navigation on mobile**: `useNavigate`, back button handling, scroll-restoration on back-navigation.
- Know the tradeoff between **client-side list** (fast, stale) and **API-fresh list** (slower, accurate) — choose the right strategy for a field CMMS.
- Write a Playwright test that simulates a mobile viewport, taps a card, asserts the detail URL, and taps back.

**Working artifact:**  
PR: `feat/mobile-wo-list` — card layout, navigation, Playwright test at 375 px viewport, AC-02 all green.

**Resource:**  
Read: React Router v6 "Scroll Restoration" docs. Read: web.dev "Optimistic UI" pattern.

**Retrospective prompt:**  
> "How would the list→detail pattern change if Faris often works offline in a basement equipment room? What would you add to S-04 (offline read cache)?"

---

### Week 5 — RTL audit & Playwright regression suite

**Delivery milestone:** Playwright RTL snapshot regression suite runs on CI. All AC-03 criteria pass. At least 3 existing RTL bugs are found and fixed.

**Learning outcomes:**
- Understand **CSS logical properties** (`padding-inline-start` vs. `padding-left`) and when Tailwind's `rtl:` variant is the right tool vs. logical properties.
- Set up a Playwright visual snapshot test: screenshot in LTR, screenshot in RTL, diff them — know what a genuine RTL regression looks like vs. an acceptable difference.
- Know the three most common RTL bugs in React apps: (1) `flex-row` not flipping, (2) icon mirroring, (3) `text-align: left` hardcoded.

**Working artifact:**  
PR: `test/rtl-regression` — Playwright snapshot suite for bottom nav, WO card, and WO detail at 375 px in AR. At least 3 bug fixes included.

**Resource:**  
Read: MDN "CSS Logical Properties". Read: Tailwind "RTL support" docs. Run: existing `playwright` config and add to it.

**Retrospective prompt:**  
> "Which RTL bug was hardest to find? Why? What automated rule would have caught it earlier?"

---

### Week 6 — AC sweep, Lighthouse gate, merge

**Delivery milestone:** All AC-01 through AC-04 criteria are green. Lighthouse PWA ≥ 80, mobile performance ≥ 70, accessibility ≥ 90. `npm run build` passes with 0 type errors.

**Learning outcomes:**
- Run a **Lighthouse audit** in CI (or locally on production build) — understand the score breakdown: PWA, Performance, Accessibility, Best Practices, SEO.
- Know how to interpret **Core Web Vitals** on mobile: LCP (largest content paint — is the WO list the LCP element?), CLS (layout shift — does the bottom nav shift the layout?), INP (interaction to next paint — is the card tap snappy?).
- Write a **technical summary** for a non-technical stakeholder: "The app is now installable, works at 375 px in both Arabic and English, and the WO loop is completable from a phone."

**Working artifact:**  
PR: `feat/mobile-pilot-shell` — all Must Have features M-01..M-12 merged, Lighthouse scores documented in PR description, 0 TypeScript errors.

**Resource:**  
Read: web.dev "Core Web Vitals" series. Run: `npx lighthouse http://localhost:5173 --view --preset=desktop` and then mobile throttle.

**Retrospective prompt:**  
> "What is one thing I would do differently in the next cycle based on what I shipped this cycle?"

---

## Cross-track sync checkpoints

Run these once per fortnight (end of weeks 2, 4, 6):

| Checkpoint | Questions to answer as a team |
|------------|-------------------------------|
| **Week 2 sync** | Is the PWA manifest live? Does the bottom nav spec match the engineering implementation? Are there any AR copy strings missing? |
| **Week 4 sync** | Does the WO card design match the built component at 375 px? Are the AC-02 Playwright tests passing? Are any ManWinWin gap codes still unresolved? |
| **Week 6 sync** | Are all Must Have items green? What is the Lighthouse score? Is the pilot hospital demo booked? What goes on the retrospective wall? |

---

## Learning resources — curated shortlist

| Resource | Track | Why |
|----------|-------|-----|
| *Inspired* — Marty Cagan | A | Product thinking vs. feature factory |
| *User Story Mapping* — Jeff Patton | A | Backlog structure and AC craft |
| Material Design 3 — Touch targets | B | 44 px rule, tap target patterns |
| W3C Internationalization — RTL scripts | B | Authoritative RTL rules |
| *Writing Is Designing* — Metts & Welfle | B | UX copy as design material |
| web.dev PWA series | C | Manifest, SW, install, offline |
| Jake Archibald "The Offline Cookbook" | C | Cache strategies |
| Tailwind CSS "Responsive design" | C | Breakpoint system |
| MDN "CSS Logical Properties" | C | RTL-safe CSS |
| web.dev "Core Web Vitals" | C | LCP, CLS, INP on mobile |

---

*Companion document: `MOBILE_FIRST_PILOT_PRD.md`*  
*Delivery cycle aligned to: Wave artifacts → cleanup → mobile shell start*
