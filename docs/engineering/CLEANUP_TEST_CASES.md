# Cleanup & mobile-shell test cases

**Plan:** [MOBILE_FIRST_CLEANUP_PLAN.md](./MOBILE_FIRST_CLEANUP_PLAN.md) · **Tickets:** [tickets/](./tickets/)

Each case has an ID `TC-<ticket>-NN`, a layer, and how it's run.

**Layers:**

- **S:** static. Compiler, script, or `rg`.
- **U:** unit (Vitest).
- **C:** component/integration (Vitest + Testing Library, jsdom).
- **E:** e2e (Playwright).
- **M:** manual. Record evidence in the PR.

**Shared preconditions:**

- **P-PILOT:** the pilot stack is running (`docker compose -f docker-compose-pilot.yml up -d --build`), with `E2E_BASE_URL=http://localhost:9081`.
- **P-MOBILE:** Playwright project `mobile-chrome` (`devices["Pixel 7"]`, 412×915) is in use. Added in CLEAN-009.
- **P-DESKTOP:** Playwright project `chromium` (`devices["Desktop Chrome"]`, 1280×720) is in use.

---

## CLEAN-001: Repoint imports off `@/components/*`

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-001-01 | S | The branch with CLEAN-001 applied | I run `rg -n "from ['\"]@/components/" src --glob '!src/components/**'` | It returns **0** matches |
| TC-CLEAN-001-02 | S | Same | I run `npm run build` | `tsc -b` and `vite build` both exit 0 with no new warnings |
| TC-CLEAN-001-03 | S | `src/shared/components/Sidebar.tsx` | I read its imports | `OrbitLogo` is imported from `@/shared/components/OrbitLogo` (or `./OrbitLogo`), not `@/components/*` |
| TC-CLEAN-001-04 | S | Each repointed import | I compare the new path with the target in the old shim file | The new path equals the shim's re-export target exactly (same module, same named/default export) |
| TC-CLEAN-001-05 | E | P-PILOT, P-DESKTOP | I run the full existing e2e suite | All 5 domain specs pass, the same as on `main` |

## CLEAN-002: Legacy-import guard

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-002-01 | S | A clean tree after CLEAN-001 | I run `npm run check:imports` | Exit 0 and the output says "0 legacy imports" |
| TC-CLEAN-002-02 | S | I add `import { EmptyState } from "@/components/EmptyState";` to any file under `src/features/` | I run `npm run check:imports` | Exit code ≠ 0; output names the file, line, and the canonical replacement path |
| TC-CLEAN-002-03 | S | I add `import { X } from "@/pages/DashboardPage";` | I run the guard | It fails as in -02 |
| TC-CLEAN-002-04 | S | I add a relative import `../../components/EmptyState` from `src/features/x/y.tsx` | I run the guard | It fails |
| TC-CLEAN-002-05 | S | Files inside `src/components/**` or `src/pages/**` (before deletion) | I run the guard | Those directories themselves are ignored, so the shims don't flag themselves |
| TC-CLEAN-002-06 | S | A PR that introduces a legacy import | CI runs the frontend job | The job fails at the `check:imports` step before `build` |

## CLEAN-003: Delete `src/pages/`

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-003-01 | S | The branch with CLEAN-003 applied | I run `git ls-files src/pages` | Empty output |
| TC-CLEAN-003-02 | S | Same | I run `npm run build` and `npm run check:imports` | Both exit 0 |
| TC-CLEAN-003-03 | S | Same | I run `rg -n "pages/(\w+Page)['\"]" src tests --glob '!src/features/**'` | 0 matches (no string or dynamic references) |
| TC-CLEAN-003-04 | E | P-PILOT, P-DESKTOP | I log in as each seeded role and visit `/`, `/work-orders`, `/work-orders/:id`, `/invoices`, `/companies`, `/assets`, `/users`, `/profile` | Every route renders its page; no blank screen; no console `Failed to fetch dynamically imported module` |
| TC-CLEAN-003-05 | E | P-PILOT, P-DESKTOP | I run the full e2e suite | All specs pass |

## CLEAN-004: Delete `src/components/` shims + docs + build info

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-004-01 | S | The branch with CLEAN-004 applied | I run `git ls-files src/components` | Empty output |
| TC-CLEAN-004-02 | S | Same | I run `npm run build` and `npm run check:imports` | Both exit 0 |
| TC-CLEAN-004-03 | S | `CLAUDE.md` § Project Structure | I read it | It shows `src/app/`, `src/features/<domain>/{pages,components}`, `src/shared/{lib,components}`. It does **not** list `src/pages/` or `src/components/` as code locations |
| TC-CLEAN-004-04 | S | `docs/CLEANUP_STAGE.md` § Layout | I read it | The shim lines are removed or marked "removed in CLEAN-003/004" |
| TC-CLEAN-004-05 | S | `git rm --cached tsconfig.tsbuildinfo` applied (already in `.gitignore`) | I run `npm run build`, then `git status` and `git ls-files tsconfig.tsbuildinfo` | `git status` doesn't list it; `ls-files` prints nothing |
| TC-CLEAN-004-06 | S | `dist/` sizes recorded on `main` before PR2 | I build PR2 and compare `dist/assets` total bytes | The delta is within ±2% |
| TC-CLEAN-004-07 | E | P-PILOT, P-DESKTOP | I run the full e2e suite | All specs pass |

## CLEAN-005: Vitest harness

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-005-01 | U | A fresh `npm ci` | I run `npm test` | Vitest runs once (non-watch), finds `src/**/*.test.{ts,tsx}`, and exits 0 |
| TC-CLEAN-005-02 | U | A test importing `@/shared/components/EmptyState` and `@/lib/api` | I run `npm test` | Both aliases resolve, the same as in Vite (`@/lib` maps to `src/shared/lib`) |
| TC-CLEAN-005-03 | C | Smoke test rendering `<EmptyState>` inside an `I18nextProvider` | I run it | Translated text is in the document; `@testing-library/jest-dom` matchers are available |
| TC-CLEAN-005-04 | U | The shared test setup | A test calls `window.matchMedia("(max-width: 1023px)")` | It returns a controllable mock (`setViewport(width)` helper), with no `TypeError` |
| TC-CLEAN-005-05 | S | `.github/workflows/ci.yml` | A PR runs CI | The frontend job runs `npm test` after `npm ci` and fails the job on a failing test |
| TC-CLEAN-005-06 | S | `tsconfig` and the production build | I run `npm run build` | Test files and `vitest` types are **not** in the production bundle; the build still passes |

## CLEAN-006: Manifest + meta

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-006-01 | S | `public/manifest.webmanifest` | I parse it as JSON | Valid JSON with `name`, `short_name` ("Orbit"), `start_url` "/", `scope` "/", `display` "standalone", `theme_color`, `background_color`, `lang` "ar", `dir` "rtl" |
| TC-CLEAN-006-02 | S | The manifest `icons[]` | I check each `src` exists under `public/` | Entries for 192 and 512 `any` + 192 and 512 `maskable` exist; every file resolves; sizes match the actual PNG dimensions |
| TC-CLEAN-006-03 | S | `index.html` | I read `<head>` | It contains `<link rel="manifest" href="/manifest.webmanifest">`, `<meta name="theme-color">`, `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">`, `<link rel="icon" type="image/svg+xml" href="/icons/favicon.svg">`, and `<meta name="apple-mobile-web-app-capable" content="yes">` |
| TC-CLEAN-006-04 | M | `npm run build && npm run preview` in Chrome | I open DevTools → Application → Manifest | Name, icons, and theme show; **no errors** in the Installability section, apart from a missing-SW warning until CLEAN-008 |
| TC-CLEAN-006-05 | M | The maskable icon | I preview it in the DevTools maskable-icon "show only minimum safe area" view | The logo sits fully inside the safe zone |
| TC-CLEAN-006-06 | E | P-PILOT | Playwright requests `/manifest.webmanifest` | HTTP 200 with `Content-Type` containing `manifest+json` or `json` |

## CLEAN-007: Wire `InstallOrbitBanner`

Unit tests run against `usePwaInstall` with `localStorage`, `matchMedia`, the UA, and fake timers mocked.

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-007-01 | U | First visit (visits counter → 1), narrow viewport, Chromium | `beforeinstallprompt` fires and 2.5s elapse | `visible === false` (the hook needs ≥2 visits) |
| TC-CLEAN-007-02 | U | Second visit, narrow viewport, Chromium | `beforeinstallprompt` fires and 2.5s elapse | `visible === true`, `mode === "chromium"`, `canPrompt === true` |
| TC-CLEAN-007-03 | U | Second visit, narrow viewport, Chromium | Only 1s has elapsed | `visible === false` (dwell not met) |
| TC-CLEAN-007-04 | U | Second visit, viewport 1280px | The event fires and dwell passes | `visible === false` |
| TC-CLEAN-007-05 | U | `display-mode: standalone` matches | The hook mounts | `visible === false`; the visit counter is **not** incremented |
| TC-CLEAN-007-06 | U | `localStorage.orbit_pwa_install_dismissed = "1"` | The hook mounts | `visible === false` |
| TC-CLEAN-007-07 | U | Second visit, iPhone UA, no `beforeinstallprompt` | Dwell passes | `visible === true`, `mode === "ios"`, `canPrompt === false` |
| TC-CLEAN-007-08 | U | The banner is visible | `dismiss()` is called | `visible === false` and `localStorage.orbit_pwa_install_dismissed === "1"` |
| TC-CLEAN-007-09 | U | The banner is visible in Chromium mode | `promptInstall()` resolves with `outcome: "accepted"` | `deferred.prompt` was called once; `visible === false`; `canPrompt === false` |
| TC-CLEAN-007-10 | C | Language `ar`, banner forced visible (mode chromium) | It renders | The title, body, CTA, and dismiss show **Arabic** strings from `ar.json`; no raw `pwa_install_` text in the DOM |
| TC-CLEAN-007-11 | C | Language `en`, mode `ios` | It renders | The iOS hint text from `en.json` shows; no install CTA button |
| TC-CLEAN-007-12 | C | The authenticated `Layout` | It renders | Exactly one `role="dialog"` banner instance at most. It isn't rendered on `/login` |
| TC-CLEAN-007-13 | S | `ar.json` and `en.json` | I diff their key sets for the `pwa_install_` prefix | Both contain exactly `pwa_install_title`, `pwa_install_body`, `pwa_install_ios_hint`, `pwa_install_cta`, `pwa_install_dismiss` |
| TC-CLEAN-007-14 | M | An Android device, second visit to the deployed pilot | I wait about 3s on the dashboard | The banner appears; tapping Install shows the native prompt; after install, the app opens standalone and the banner doesn't show there |

## CLEAN-008: App-shell service worker

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-008-01 | M | `npm run dev` | I open DevTools → Application → Service Workers | **No** SW is registered in dev |
| TC-CLEAN-008-02 | M | `npm run build && npm run preview` | I load the app | The SW is registered and activated; the precache contains `index.html` and the hashed JS/CSS from `dist/assets` |
| TC-CLEAN-008-03 | M/E | The SW is active, logged in | I load `/work-orders`, then inspect Cache Storage | **No** cache entry has a URL matching `/api/`. Network panel shows `/api/*` served "from network", never "from ServiceWorker" cache |
| TC-CLEAN-008-04 | M | The SW is active | I go offline in DevTools and reload `/work-orders/123` | The app shell (`index.html`) loads from cache; the page shows the existing API-error state instead of the browser's offline dinosaur |
| TC-CLEAN-008-05 | M | The SW is active on build A | I deploy build B and revisit | A "new version available" toast appears (AR/EN). Tapping refresh activates the new SW and loads build B's assets, with no chunk-load error |
| TC-CLEAN-008-06 | M | Logged in, SW active | I log out, then press Back | No authenticated data is shown from cache; the route guard redirects to `/login` |
| TC-CLEAN-008-07 | M | An Android Chrome device | I visit the pilot twice | Chrome offers install (banner via CLEAN-007, or the omnibox install icon) |
| TC-CLEAN-008-08 | S | The build output | I inspect `dist/` | It contains `sw.js` (or the configured name) and a registration call guarded by `import.meta.env.PROD` |

## CLEAN-009: `MobileBottomNav` + More sheet

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-009-00 | U | `getVisibleNavItems(user)`, extracted from `Sidebar` | It's called with fixtures for each role (technician, site_manager, company_admin, client_admin, super_admin/platform staff) | The output equals the list the pre-refactor `Sidebar` filter produced for the same fixture (snapshot taken before extraction) |
| TC-CLEAN-009-01 | U | `getMobileTabs(visibleItems)` | It's called with the technician's visible items | It returns ≤4 primary tabs (e.g. Dashboard, Work orders, Assets, Profile) plus More holding the rest; every item comes from `visibleItems` |
| TC-CLEAN-009-02 | U | The same function | It's called for `company_admin` and `super_admin` | Primary tabs differ per role as specified; items that don't fit go to the More list; no item appears twice |
| TC-CLEAN-009-03 | U | A user whose subscription lacks an item's `requiredFeature` | `getVisibleNavItems` + `getMobileTabs` run | That item is absent from both tabs and More (same `hasFeature` rule as `Sidebar`) |
| TC-CLEAN-009-04 | E | P-MOBILE, logged in as technician | The dashboard loads | The bottom nav (`role="navigation"`, labelled) is visible; the desktop sidebar isn't visible; the hamburger isn't visible |
| TC-CLEAN-009-05 | E | P-DESKTOP, the same user | The dashboard loads | The sidebar is visible exactly as on `main`; the bottom nav isn't in the DOM (or is `display:none`) |
| TC-CLEAN-009-06 | E | P-MOBILE, the install banner forced visible | The page renders | The banner sits **above** the bottom nav; neither covers the other's buttons; the last list row in `<main>` is fully scrollable into view |
| TC-CLEAN-009-07 | E | P-MOBILE | I tap the Work orders tab | The URL becomes `/work-orders`; the tab has `aria-current="page"`; the previous tab loses it |
| TC-CLEAN-009-08 | E | P-MOBILE | I tap More | A sheet opens with the remaining items; focus moves into the sheet; Escape or tapping the backdrop closes it; focus returns to More |
| TC-CLEAN-009-09 | E | P-MOBILE, language AR | The page renders | Tab order is mirrored (first tab at the right); the sheet text is right-aligned; no horizontal scroll at 412px |
| TC-CLEAN-009-10 | E | P-MOBILE | I run the golden-path spec (`wave4-golden-path.spec.ts`) | It passes using the bottom nav, or direct URLs where the spec navigates by URL |
| TC-CLEAN-009-11 | M | An iPhone with a notch, installed standalone | I open Orbit | The bottom nav clears the home indicator (`env(safe-area-inset-bottom)` padding); the header clears the status bar |
| TC-CLEAN-009-12 | M | A 1024px-wide viewport (the `lg` boundary) | I resize from 1023 to 1024 | It switches cleanly from bottom nav to sidebar with no overlap frame; no layout shift in `<main>` content width beyond the sidebar |

## CLEAN-010: Split `WorkOrderDetailPage`

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-010-01 | U | `ALLOWED_TRANSITIONS`, extracted to `features/work-orders/lib/workOrderRules.ts` | For every `WorkOrderStatus` key | The returned list equals the pre-refactor table (snapshot test written **before** the extraction against the original constant) |
| TC-CLEAN-010-02 | U | `statusAllowsReport(status)` | It's called for each status | It returns `true` exactly for the statuses in `REPORT_UNLOCKED_STATUSES` |
| TC-CLEAN-010-03 | C | `useWorkOrderDetail(id)` with `apiFetch` mocked | The hook mounts | It calls `/work-orders/:id`, then in parallel `/users/me`, `/history`, `/comments`, `/assignable-users`, and `/documents`; exposes `{wo, me, history, comments, documents, assignable, reload}`; `reload()` refetches |
| TC-CLEAN-010-04 | C | Mocked WO in status `completed` with a submitted report, user `client_admin` | The page renders | The Approve button is visible; the Generate invoice button isn't (the report isn't approved yet) |
| TC-CLEAN-010-05 | C | Mocked WO with an approved report, status `verified`, user `company_admin` | The page renders | The Generate invoice control is visible and enabled |
| TC-CLEAN-010-06 | C | A user selects status `on_hold` | They confirm | The Hold modal opens; submitting with an empty reason is blocked; submitting with a reason calls `PATCH /work-orders/:id` once with that reason |
| TC-CLEAN-010-07 | C | A user adds a comment | They submit | `POST /work-orders/:id/comments` is called, then the comments list refreshes; the input clears |
| TC-CLEAN-010-08 | S | After the refactor | I run `wc -l` on `WorkOrderDetailPage.tsx` | ≤ 400 lines; no extracted file > 300 lines; `useState` count in the page ≤ 8 |
| TC-CLEAN-010-09 | E | P-PILOT, P-DESKTOP + P-MOBILE | I run `wave4-workflows.spec.ts` and `wave4-golden-path.spec.ts` | Both pass unchanged (selectors not edited unless a test-id is added) |
| TC-CLEAN-010-10 | M | AR and EN | I walk a WO: assign → in progress → report draft → submit → approve → verify → invoice | Same behaviour and strings as on `main` |

## CLEAN-011: Split `WorkOrdersPage`

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-011-01 | U | `buildWorkOrderQuery(filters)` (extracted) | It's called with status, site, assignee, date range, and search | It returns the exact query string the old inline code produced (snapshot written pre-refactor) |
| TC-CLEAN-011-02 | U | Empty filters | It's called | It returns the base query with pagination only |
| TC-CLEAN-011-03 | C | Filters set in the URL (`?status=assigned`) | The page mounts | `FilterBar` shows `assigned` selected and the list fetch uses it |
| TC-CLEAN-011-04 | C | A pending request row | The user opens request review | `WorkOrderRequestReviewModal` opens with that row's data (imported from `@/features/work-orders/components/…`) |
| TC-CLEAN-011-05 | S | After the refactor | I count lines | Page ≤ 350 lines; no extracted file > 300 |
| TC-CLEAN-011-06 | E | P-PILOT, desktop + mobile | I run the work-order e2e specs | They pass |

## CLEAN-012: Split `CompanyDetailPage` + `AssetDetailPage`

| ID | Layer | Given | When | Then |
|----|-------|-------|------|------|
| TC-CLEAN-012-01 | C | `CompanyDetailPage` with mocked company + 2 sites | It renders | The profile section, sites list, and action buttons render. Edit opens `CompanyEditModal`; Provision site opens `SiteProvisionModal` |
| TC-CLEAN-012-02 | C | `SiteProvisionModal` success response with credentials | The modal completes | `ProvisionCredentialsModal` shows the returned credentials once |
| TC-CLEAN-012-03 | C | `AssetDetailPage` with mocked asset + lifecycle events | It renders | The lifecycle badge, timeline (events in date order), and WO panel render; Edit opens `AssetEditModal` |
| TC-CLEAN-012-04 | S | After the refactor | I count lines | Each page ≤ 350; no extracted file > 300 |
| TC-CLEAN-012-05 | E | P-PILOT, desktop + mobile | I run `wave3-assets.spec.ts` | It passes |
| TC-CLEAN-012-06 | M | `company_admin` | I create a company, provision a site, assign a manager, edit the site, view the QR | Every flow works as on `main` in AR and EN |
