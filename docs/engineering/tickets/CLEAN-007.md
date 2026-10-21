# [Feature] CLEAN-007: Wire `InstallOrbitBanner` + AR/EN copy

**Labels:** `type:feature` `area:frontend` `area:pwa` `area:i18n` `wave:2C` · **Estimate:** S · **Depends on:** CLEAN-005, CLEAN-006 · **PR:** PR3 (commit 2)  
**Tests:** [TC-CLEAN-007-*](../CLEANUP_TEST_CASES.md#clean-007-wire-installorbitbanner)

## User story

As a returning phone user, I want a gentle, dismissible prompt to install Orbit. On iPhone, I want instructions, since Safari has no install button.

## Context

`src/features/pwa/usePwaInstall.ts` and `InstallOrbitBanner.tsx` exist but are untracked and mounted nowhere. The hook already gates on:

- not standalone
- not dismissed
- viewport ≤1023px
- ≥2 visits
- 2.5s dwell

It also handles Chromium `beforeinstallprompt` vs the iOS hint. **The 5 i18n keys it uses don't exist**, so mounting it today renders raw keys.

## Scope

**In:**

- Add `pwa_install_title`, `pwa_install_body`, `pwa_install_ios_hint`, `pwa_install_cta`, `pwa_install_dismiss` to `src/i18n/locales/ar.json` and `en.json`. Get the copy from the UX-writing sheet. The iOS hint must name Share → "Add to Home Screen" / «إضافة إلى الشاشة الرئيسية».
- Mount `<InstallOrbitBanner />` once in `src/shared/components/Layout.tsx` (authenticated shell only, never on `/login`)
- Unit tests for `usePwaInstall`: TC-CLEAN-007-01…09
- Component tests for the banner: TC-CLEAN-007-10…12

**Out:** Changing the gating thresholds. Analytics events (a follow-up ticket, if wanted).

## Acceptance criteria

- [ ] Both locale files contain exactly the 5 keys; no raw key visible in AR or EN
- [ ] Banner never renders at `lg+`, in standalone mode, or after dismiss (persisted)
- [ ] Banner positioning leaves room for the bottom nav once CLEAN-009 lands (expose a CSS var or bottom offset)
- [ ] `npm test` green with the new tests
- [ ] Manual: an Android second visit shows the banner and Install triggers the native prompt; on iPhone the hint shows

## Mentor note

The `beforeinstallprompt` lifecycle, and the fact that iOS has no install API. Asking at the right moment (visits + dwell) is product design, not just code.
