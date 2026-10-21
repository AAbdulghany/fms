# [Feature] CLEAN-006: Web app manifest + icon/theme meta

**Labels:** `type:feature` `area:frontend` `area:pwa` `wave:2C` · **Estimate:** S · **Depends on:** — · **PR:** PR3 (commit 1)  
**Tests:** [TC-CLEAN-006-*](../CLEANUP_TEST_CASES.md)

## User story

As a technician on the pilot site, I want to add Orbit to my phone's home screen with a proper icon and name, so that it opens like an app without the browser chrome.

## Context

The icons already exist (untracked) in `public/icons/`: `favicon.svg`, `apple-touch-icon.png`, `icon-192/512.png`, `icon-maskable-192/512.png`. There's no manifest, and `index.html` has only a `viewport` meta.

## Scope

**In:**

- `public/manifest.webmanifest`:
  - `name` "Orbit", `short_name` "Orbit"
  - `start_url` "/", `scope` "/", `display` "standalone"
  - `lang` "ar", `dir` "rtl" (AR is the default language)
  - `theme_color` `#0d7c8c` (`--color-primary-500`), `background_color` `#fafaf9` (`--color-neutral-50`)
  - icons for 192/512 `any` and 192/512 `maskable`
- `index.html` `<head>`:
  - `<link rel="manifest">`, `<meta name="theme-color" content="#0d7c8c">`
  - `<link rel="icon" type="image/svg+xml" href="/icons/favicon.svg">`, `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">`
  - `<meta name="apple-mobile-web-app-capable" content="yes">`, `<meta name="apple-mobile-web-app-title" content="Orbit">`
  - `viewport-fit=cover` added to the viewport meta (needed for safe-area insets in CLEAN-009)
- Commit the `public/icons/*` files.
- Confirm the pilot nginx/static host serves `.webmanifest` (`application/manifest+json`). Add a MIME mapping if not.

**Out:** Service worker (CLEAN-008). Splash screens per iOS device size.

## Acceptance criteria

- [ ] Manifest is valid JSON; every icon path resolves; PNG sizes match the declared sizes
- [ ] DevTools → Application → Manifest shows no errors (a missing-SW note is fine until CLEAN-008)
- [ ] Maskable icon passes the DevTools safe-area preview
- [ ] `GET /manifest.webmanifest` returns 200 on the pilot stack
- [ ] Desktop tab favicon shows the Orbit mark

## Mentor note

What the browser needs before it calls a site "installable". Maskable icons and safe zones. How `theme-color` tints the OS UI.
