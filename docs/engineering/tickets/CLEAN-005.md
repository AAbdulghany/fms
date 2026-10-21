# [Task] CLEAN-005: Add Vitest + Testing Library harness

**Labels:** `type:task` `area:frontend` `area:testing` `wave:2B` · **Estimate:** M · **Depends on:** — · **PR:** PR2 (commit 5 of 5). Move to PR2b if review stalls  
**Tests:** [TC-CLEAN-005-*](../CLEANUP_TEST_CASES.md#clean-005-vitest-harness)

## Driver

The frontend has zero unit/component tests; only Playwright e2e against a Docker stack. The PWA hook (CLEAN-007), nav config (CLEAN-009), and every god-page split (CLEAN-010–012) need fast, isolated tests. Splitting 1474 lines without them is gambling.

## Scope

**In:**

- devDependencies: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`
- `vitest.config.ts` that reuses `vite.config.ts` aliases (`@/lib` → `src/shared/lib` **before** `@` → `src`), `environment: "jsdom"`, `setupFiles: ["src/test/setup.ts"]`, `include: ["src/**/*.test.{ts,tsx}"]`
- `src/test/setup.ts`: jest-dom matchers; a `matchMedia` mock with a `setViewport(width)` helper; `localStorage.clear()` between tests
- `src/test/renderWithProviders.tsx`: i18n (AR/EN switchable) + `MemoryRouter`
- One smoke test, `src/shared/components/EmptyState.test.tsx`
- `package.json`: `"test": "vitest run"`, `"test:watch": "vitest"`
- CI frontend job: `npm test` after `check:imports`
- Exclude `src/test/**` and `**/*.test.*` from the `tsc -b` app project (or give them their own tsconfig) so production type-check and bundle stay clean

**Out:** Coverage thresholds. Those get decided after CLEAN-010.

## Acceptance criteria

- [ ] `npm test` exits 0 locally (Windows) and in CI (Linux)
- [ ] Smoke test passes in both AR and EN
- [ ] `npm run build` unaffected; no test code in `dist/`
- [ ] `docs/guides/testing.md` has a short "Unit/component tests" section (run, file naming, the `matchMedia` helper)

## Mentor note

Know the layers: unit, component, e2e. jsdom has no real CSS media queries, so you mock `matchMedia`. Tests are the precondition for refactoring.
