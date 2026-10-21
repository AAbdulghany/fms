# [Task] CLEAN-003: Delete `src/pages/` shim directory

**Labels:** `type:task` `area:frontend` `wave:2B` `cleanup` · **Estimate:** S · **Depends on:** CLEAN-002 · **PR:** PR2 (commit 3 of 5)  
**Tests:** [TC-CLEAN-003-*](../CLEANUP_TEST_CASES.md)

## Driver

All 20 files in `src/pages/` are 2-line `@deprecated` re-exports. `src/app/routes.tsx` already imports every page from `@/features/*/pages/*`. Verified on `main` @ `d6b0175`, nothing in `src/`, `tests/`, or the build config references `src/pages`.

## Scope

**In:** `git rm -r src/pages`. Remove the `src/pages/*.tsx` exclusion from the guard script, if present.

**Out:** Moving or renaming any real page.

## Acceptance criteria

- [ ] `git ls-files src/pages` is empty
- [ ] `npm run check:imports` and `npm run build` green
- [ ] `rg -n "pages/(\w+Page)['\"]" src tests --glob '!src/features/**'` returns 0 (no string or dynamic refs)
- [ ] Every route in `src/app/routes.tsx` renders for its role on the demo stack (TC-CLEAN-003-04)
- [ ] Full e2e suite green

## Rollback

Restore a single file from git with `git checkout <sha>~1 -- src/pages/<File>.tsx`. You don't need to revert the whole commit.

## Mentor note

Prove a file is unused (zero consumers, green build, green e2e) before deleting it. Deleting code is a feature.
