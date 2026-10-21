# [Task] CLEAN-002: Legacy-import guard script + CI step

**Labels:** `type:task` `area:frontend` `area:ci` `wave:2B` `cleanup` · **Estimate:** S · **Depends on:** CLEAN-001 · **PR:** PR2 (commit 2 of 5)  
**Tests:** TC-CLEAN-002-* in [CLEANUP_TEST_CASES.md](../CLEANUP_TEST_CASES.md)

## Driver

There's no ESLint in the repo, so nothing stops a new file importing `@/components/…` or `@/pages/…` again. That matters most for AI agents reading the stale `CLAUDE.md`. A convention that isn't enforced drifts.

## Scope

**In:**

- `scripts/check-legacy-imports.mjs`: a dependency-free Node script that scans `src/**/*.{ts,tsx}` (excluding `src/components/**` and `src/pages/**` while they still exist) for:
  - `from "@/components/…"` and `from "@/pages/…"`
  - `import("@/components/…")` and `import("@/pages/…")` (dynamic)
  - relative specifiers that resolve into `src/components/` or `src/pages/`
- Output: `file:line  <specifier>  → use <canonical>` (canonical is read from the shim's re-export line while it exists; otherwise a generic hint). Exit 1 on any hit.
- `package.json`: `"check:imports": "node scripts/check-legacy-imports.mjs"`
- `.github/workflows/ci.yml` frontend job: run `npm run check:imports` after `npm ci`, before `npm run build`.

**Out:** Adopting ESLint (a separate decision, which would need an AgDR).

## Acceptance criteria

- [ ] Clean tree: exit 0
- [ ] Seeded alias, dynamic, and relative legacy imports each produce exit 1 with file and line
- [ ] CI fails on a PR that introduces a legacy import
- [ ] Script runs on Windows (PowerShell) and Linux CI. Use `node:path`; no shell globbing

## Mentor note

Turn a team rule into a 40-line script plus a CI step. Making the right path the only path beats reminding people in review.
