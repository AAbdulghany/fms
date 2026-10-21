# Mobile-first cycle — Orbit AM pilot

**Date:** 2026-10-21  
**Operator decisions:** **1A** (responsive web + installable PWA for pilot) · **1C** (native shell deferred to vision horizon) · desktop/web layouts remain first-class · delivery **2A → 2B → 2C**

## Streams

| Stream | Owner role | Artifact |
|--------|------------|----------|
| Architecture vision | Solution Architect | [vision.md](../architecture/vision.md) |
| ManWinWin gap | Product Analyst | [MANWINWIN_GAP_MATRIX.md](../product/MANWINWIN_GAP_MATRIX.md) |
| Pilot PRD + mentor | Product Manager | [MOBILE_FIRST_PILOT_PRD.md](../product/MOBILE_FIRST_PILOT_PRD.md), [EDUCATIONAL_MENTOR_TRACKS.md](../product/EDUCATIONAL_MENTOR_TRACKS.md) |
| Cleanup plan + tickets | Tech Lead | [MOBILE_FIRST_CLEANUP_PLAN.md](./MOBILE_FIRST_CLEANUP_PLAN.md), [tickets/](./tickets/) |
| Layout concepts | UI Designer + UX Writing | [../designs/](../../designs/), `.pen` + copy sheet |
| Pilot shell code | Frontend | `MobileBottomNav`, PWA manifest, install banner wiring |

## PR packing

1. **docs/design** — planning artifacts, gap matrix, vision, mentor tracks, designs  
2. **cleanup** — legacy import hygiene / dead shim plan execution (safe deletes only)  
3. **mobile-shell** — bottom nav + PWA install path for phone; sidebar retained for `lg+`

## Verification (pilot)

- [ ] Phone (≤1023px): primary nav is bottom tabs; More opens remaining items  
- [ ] Desktop (`lg+`): sidebar unchanged; no bottom tabs  
- [ ] RTL (AR) and LTR (EN) both usable  
- [ ] Install banner appears on narrow viewports after dwell/visits; dismiss persists  
- [ ] `manifest.webmanifest` linked; icons resolve  
- [ ] `npm run build` green  

## Non-goals this cycle

- Capacitor / React Native  
- ManWinWin feature parity  
- Splitting WorkOrderDetail god-page (ticketed, not required to merge shell)  
