# Decision Notes — Keep stack, go mobile-first PWA

> **Type:** Decision record notes (pre-AgDR). Follows the repo's named AgDR convention (`docs/decisions/AgDR-<TOPIC>.md`). Promote to `docs/decisions/AgDR-MOBILE-FIRST-PWA.md` via `/decide` before Q0 build work starts.
> **Date:** 2026-10-21 · **Status:** Accepted (operator-locked) · **Context doc:** [vision.md](vision.md)

## Context

- The pilot's main users are **field technicians on phones**. Today's web UI is desktop-oriented, and technician screens are only "mobile-friendly".
- [ARCHITECTURE.md §8.3](../ARCHITECTURE.md) planned a React Native manager app for Phase 3. Nothing native exists yet.
- PWA groundwork is partial. Icons and an uncommitted `src/features/pwa/` install banner and hook exist, but there is **no web manifest and no service worker**.
- The backend (FastAPI, sync SQLAlchemy, Postgres, JWT, row-level tenancy, 219+ tests) is stable and is not the bottleneck.

## Decision

1. **Keep** React 18 + Vite + Tailwind + react-router + i18next on the front end, and FastAPI + Postgres on the back end.
2. **Make the web client mobile-first and responsive.** Phone layout is the base and desktop is progressive enhancement. Desktop and office flows stay fully supported.
3. **Ship it as an installable PWA:** manifest, service worker (app-shell precache, offline page, update prompt), install prompt, and later Web Push and offline-lite drafts.
4. **Defer native shells** (Capacitor / React Native) to a Q3 2027 evidence checkpoint. Until then they are anti-scope.

## Options considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Keep stack + mobile-first PWA** | Zero rewrite; one codebase and one deploy; instant updates without store review; reuses the RTL/i18n work and all API contracts | iOS PWA limits (push only on iOS 16.4+ after install, constrained background sync, cache eviction); no store presence | **Chosen** |
| B. Capacitor wrapper now | Store presence; native plugins (camera, push, background); same web code | Store signing and release pipeline; two update channels; solves problems we haven't observed yet | Deferred to Q3 checkpoint. It is the first fallback if the PWA falls short |
| C. React Native app | Best native UX and device access | Second UI codebase; RTL/i18n duplicated; months of delay to field use | Rejected for this cycle |
| D. Next.js rewrite | SSR/edge features | No SEO need behind login; adds a Node runtime; complicates the SW and offline story; stalls delivery | Rejected (anti-scope) |

## Consequences

- **Positive:** fastest path to technicians' hands; every desktop improvement also lands on phones (and the reverse); Q0 changes are cheap and reversible.
- **Negative / accepted risks:**
  - iOS limitations may cap push and offline reliability. *Mitigation:* online-first with IndexedDB drafts, and the Q3 checkpoint.
  - Service worker caching bugs can serve stale bundles. *Mitigation:* `sw.js` served with `no-cache`, a versioned precache, and a user-visible update prompt.
  - Tokens in `localStorage` persist longer in an installed app. *Mitigation:* clear on logout, server-side refresh revocation, and revisit httpOnly cookies on any XSS finding.
- **Follow-up decisions needing their own AgDR:** PWA tooling (`vite-plugin-pwa`/Workbox vs a hand-rolled SW); frontend error-capture vendor; Web Push adoption; object-storage provider; offline-lite conflict policy (Q2).

## Reversal point

Everything before Q2 offline-lite is cheap to reverse. A manifest and service worker can be unregistered, and a Capacitor wrapper can host the same build. The first costly commitment is the Q2 outbox/sync protocol (idempotency keys, conflict semantics), and it needs its own AgDR and design review.
