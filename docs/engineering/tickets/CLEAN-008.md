# [Feature] CLEAN-008: App-shell service worker (no API caching)

**Labels:** `type:feature` `area:frontend` `area:pwa` `security-review` `wave:2C` · **Estimate:** M · **Depends on:** CLEAN-006 · **PR:** PR3 (commit 3)  
**Tests:** [TC-CLEAN-008-*](../CLEANUP_TEST_CASES.md)

## User story

As a technician with patchy site connectivity, I want Orbit to open instantly from my home screen and show a clear "can't reach server" state, rather than a browser error page.

## Decision needed (record as AgDR)

Use **`vite-plugin-pwa`** with `strategies: "generateSW"` (Workbox), or hand-write `public/sw.js`. Recommendation: `vite-plugin-pwa`. It hashes the precache manifest from the Vite build, handles cache cleanup, and gives `virtual:pwa-register` for the update prompt. The trade-off is one new devDependency. If chosen, it can also own the manifest from CLEAN-006 (`manifest: false` keeps our static file).

## Scope

**In:**

- Register the SW in **production builds only** (`import.meta.env.PROD`)
- Precache the built app shell (`index.html`, hashed JS/CSS, icons); `navigateFallback: "/index.html"`; `navigateFallbackDenylist: [/^\/api\//]`
- Runtime: `/api/*` is **NetworkOnly**. No caching of authenticated responses, ever. Google Fonts get a `StaleWhileRevalidate` cache with an expiry
- `registerType: "prompt"` + an AR/EN "New version available, refresh" toast; `cleanupOutdatedCaches: true`
- Deploy runbook note (`docs/guides/pilot-stack.md`): how to verify the SW update after deploy, and how to unregister in an emergency

**Out:** Offline data, background sync, push.

## Acceptance criteria

- [ ] No SW in `npm run dev`; SW active in `npm run preview` and on the pilot
- [ ] Cache Storage contains **zero** `/api/` entries after a logged-in session (TC-CLEAN-008-03). Paste a screenshot in the PR
- [ ] Offline reload shows the app shell and the existing error state (TC-CLEAN-008-04)
- [ ] Deploying a new build surfaces the update toast; refresh loads new assets without a chunk-load error
- [ ] Logout + Back shows no cached authenticated data
- [ ] Security review (Hakim) sign-off on the caching rules

## Mentor note

The service worker lifecycle (install → activate → fetch). Precache vs runtime cache. Caching authenticated API data on a shared phone is a data leak, not a performance win.
