# [Task] CLEAN-004: Delete `src/components/` shims, correct docs, untrack build info

**Labels:** `type:task` `area:frontend` `area:docs` `wave:2B` `cleanup` · **Estimate:** S · **Depends on:** CLEAN-001, CLEAN-002 · **PR:** PR2 (commit 4 of 5)  
**Tests:** [TC-CLEAN-004-*](../CLEANUP_TEST_CASES.md)

## Driver

Once CLEAN-001 lands, the 29 shims in `src/components/` have zero consumers. `CLAUDE.md` still describes `src/pages/*` as the real page location, which keeps misdirecting contributors and agents. `tsconfig.tsbuildinfo` is in `.gitignore` but still tracked, so it pollutes every diff.

## Scope

**In:**

- `git rm -r src/components`
- `CLAUDE.md` § Project Structure: replace the tree with the real layout (`src/app/`, `src/features/<domain>/{pages,components}`, `src/features/pwa`, `src/shared/{lib,components,navigation}`, `src/i18n/locales/*.json`, `src/styles/`). Fix the `lib/api.ts` path (`src/shared/lib/api.ts`, aliased as `@/lib`).
- `docs/CLEANUP_STAGE.md` § Layout: drop the two shim lines; add "Shims removed in CLEAN-003/004".
- `git rm --cached tsconfig.tsbuildinfo`
- Guard script: drop the now-unneeded directory exclusions.

**Out:** Moving any real component between `shared` and `features`.

## Acceptance criteria

- [ ] `git ls-files src/components` is empty
- [ ] `npm run check:imports` and `npm run build` green; full e2e green
- [ ] `CLAUDE.md` contains no reference to `src/pages/` or `src/components/` as code locations
- [ ] After `npm run build`, `git status` doesn't list `tsconfig.tsbuildinfo`
- [ ] `dist/assets` total size within ±2% of `main` (record both numbers in the PR)

## Mentor note

Docs are part of the code. A wrong map is worse than no map, especially for AI pair-programmers. And build artifacts never belong in git.
