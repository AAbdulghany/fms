# [Feature] CLEAN-009: `MobileBottomNav` + More sheet below `lg`

**Labels:** `type:feature` `area:frontend` `area:mobile` `area:a11y` `wave:2C` · **Estimate:** L · **Depends on:** CLEAN-005, CLEAN-007 · **PR:** PR3 (commit 4). Split into PR3b if over ~600 changed lines  
**Tests:** [TC-CLEAN-009-*](../CLEANUP_TEST_CASES.md)  
**Design:** layout concepts in `designs/` (UI Designer) · **PRD:** [MOBILE_FIRST_PILOT_PRD.md](../../product/MOBILE_FIRST_PILOT_PRD.md)

## User story

As a technician on a phone, I want my main destinations one thumb-tap away at the bottom of the screen. As a desktop user, I want the sidebar exactly as it is today.

## Context

`Layout.tsx` currently shows a hamburger below `lg` that slides in `Sidebar`. `Sidebar` fetches `/users/me` itself and filters `NAV_ITEMS` (`src/shared/navigation/navItems.ts`) by `hasAnyRole`, `isPlatformStaff`, and `hasFeature`. The bottom nav must use the **same** filter, or phone and desktop will disagree.

## Scope

**In:**

1. Extract pure `getVisibleNavItems(user)` from `Sidebar` into `src/shared/navigation/`, and snapshot-test it per role **before** switching Sidebar to use it (TC-CLEAN-009-00).
2. Lift the `/users/me` fetch into a single `useCurrentUser()` used by both `Sidebar` and `MobileBottomNav`. No double fetch.
3. Add `getMobileTabs(visibleItems)`: an ordered priority list for ≤4 primary tabs, with the rest going to More. Add `mobilePriority` to `NAV_ITEMS` entries rather than hard-coding per role.
4. Add `src/shared/components/MobileBottomNav.tsx`:
   - `lg:hidden`, `fixed bottom-0`, `pb-[env(safe-area-inset-bottom)]`
   - `<nav aria-label>`, `aria-current="page"` on the active tab (same `isActive` rule as Sidebar)
   - minimum 44×44px hit targets
   - logical properties so RTL mirrors automatically
5. Add a More sheet: a bottom sheet with a backdrop, focus trap, Escape/backdrop close, and focus return. It holds the remaining items plus language toggle and logout.
6. `Layout` changes:
   - below `lg`, hide the hamburger + drawer, slim the header (logo, bell), and pad `<main>` by the nav height
   - at `lg+`, change nothing
   - keep the install banner offset above the nav
7. Playwright: add a `mobile-chrome` project (`devices["Pixel 7"]`) to `playwright.config.ts`; add `tests/e2e/domains/shell/mobile-shell.spec.ts` (TC-CLEAN-009-04…10).

**Out:** Per-page mobile layout fixes (follow-up tickets per page). A native shell (deferred, 1C).

## Acceptance criteria

- [ ] ≤1023px: bottom tabs + More visible; sidebar/hamburger not visible
- [ ] ≥1024px: the screenshot matches `main` (sidebar, header unchanged); no bottom nav
- [ ] Tabs and More contain exactly the items `Sidebar` shows for that user (unit-tested for every role)
- [ ] RTL (AR) mirrored and LTR (EN) correct; no horizontal scroll at 360px and 412px
- [ ] Install banner and bottom nav never overlap; last row of `<main>` scrollable into view
- [ ] Keyboard and screen-reader: tabs reachable, More sheet traps focus and returns it on close
- [ ] Golden-path e2e green on both `chromium` and `mobile-chrome`
- [ ] Manual on a notched iPhone in standalone mode: nav clears the home indicator

## Mentor note

One layout with breakpoint-driven navigation. Navigation as data (one filter, two renderers). Logical CSS for RTL. `env(safe-area-inset-*)`. Mobile-first doesn't mean desktop-second.
