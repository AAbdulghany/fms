# Wave 6 — Progress review (plan vs work)

**Branch:** `feature/phase-3-restructure/cleanup`  
**Date:** 2026-06-22  
**Original analysis:** [CLEANUP_STAGE.md](../CLEANUP_STAGE.md)

---

## Summary

Wave 6 delivered **organizational debt reduction** without behavior changes. The repo is easier to navigate for tests, docs, and ORM/schemas. Backend route and frontend page migrations are **started with shims**, not finished — intentional scope cap to keep the PR mergeable.

| Metric | Before | After |
|--------|--------|-------|
| pytest layout | Flat `backend/tests/` (31 files) | `backend/tests/domains/*` (11 domains) |
| E2E layout | Flat by wave name | `tests/e2e/domains/*` |
| ORM | Monolithic `models.py` (~585 LOC) | `app/models/` package (11 modules) |
| Schemas | Monolithic `schemas.py` (~1000 LOC) | `app/schemas/` package (12 modules) |
| Docs top-level | phase1–3.1 + orphans | `guides/`, `architecture/`, `archive/` |
| RBAC docs | 3 conflicting sources | 1 canonical + redirect |
| Dead code | 3 orphans + artifacts | Removed |
| Docker ports | 3000/9000 mismatch | 8080/8000 aligned |

---

## Phase-by-phase scorecard

### C0 — Hygiene ✅ 100%

- `.gitignore` for artifacts (`test-results/`, `tsbuildinfo`, `*.bak`, `_test_report.pdf`)
- Deleted `sla.py`, notifications stub, `TagBadge.tsx`
- Docker compose ports fixed

### C1 — Docs IA ✅ 100%

- `docs/README.md` + 4 operator guides
- Root README rewritten (219 tests, Wave 4, correct demo login)
- Supersession banners on `HOW_TO_RUN.md`, `USER_GUIDE.md`
- `docs/archive/phase{1,2,3,3.1}/` with README
- `docs/architecture/RBAC.md` canonical
- Knowledge-hub links updated (`models/` package, RBAC path)

### C2 — Backend shell 🟡 ~40%

| Item | Status |
|------|--------|
| `app/cli/docker_migrate` | ✅ |
| `app/cli/{seed,seed_super,pitch_seed,test_seed}` | ✅ + shims |
| `domains/auth/` router | ✅ + API shim |
| Remaining `api/routes/*` → domains | ⬜ NT-CLEAN-19 |
| `work_orders.py` route split (~1145 LOC) | ⬜ NT-CLEAN-21 |

### C3 — Frontend features 🟡 ~15%

| Item | Status |
|------|--------|
| `src/app/routes.tsx` | ✅ |
| `FeatureRoute` unified gating | ✅ |
| Vite `@/` alias | ✅ |
| `features/auth/pages/LoginPage` | ✅ pilot |
| Remaining 19 pages → `features/*` | ⬜ NT-CLEAN-20 |
| `shared/` extraction (Layout, lib) | ⬜ NT-CLEAN-20 |
| `providers.tsx` extraction | ⬜ optional |

### C4 — Tests by domain ✅ 100%

- Backend: 11 domain folders, 31 test files
- E2E: 5 specs under `domains/{assets,invoices,work-orders,golden-path,errors}`
- CI path updated in `wave-e2e.yml`
- Wave-prefixed filenames retained for traceability (rename optional in NT-CLEAN-23)

### C5 — God files + migration ✅ 100%

- `models.py` → `app/models/`
- `schemas.py` → `app/schemas/`
- [AgDR-SCHEMA-ENSURE.md](../decisions/AgDR-SCHEMA-ENSURE.md)
- `schema_ensure.py` documented as legacy safety net only

---

## Commits on cleanup branch

1. `a909ff2` — C0/C1: docs, hygiene, dead code, Docker ports, FeatureRoute  
2. `5908303` — tests fix, auth domain, cli migrate, routes extraction  
3. `2b94156` — NT-CLEAN-12–17: domain tests, archive, models/schemas split  
4. *(pending)* — C1/C2/C3 partial fixes, progress docs, seed consolidation  

---

## Follow-up tickets (Wave 6b)

| ID | Title | Effort |
|----|-------|--------|
| NT-CLEAN-18 | Move `report_template_sync_cli.py` → `cli/` | S |
| NT-CLEAN-19 | Backend domains: platform, clients, assets, WO, billing, reports | L |
| NT-CLEAN-20 | Frontend: migrate remaining pages → `features/*`, extract `shared/` | M |
| NT-CLEAN-21 | Split `api/routes/work_orders.py` by concern | M |
| NT-CLEAN-22 | i18n: split `ar.json` / `en.json` from monolith | S |
| NT-CLEAN-23 | Rename `test_wave*_*.py` to domain names (optional) | S |

---

## Risks accepted

1. **Dual paths during shim window** — old `app.seed_super` and new `app.cli.seed_super` both work.
2. **E2E CI** — `wave-e2e.yml` triggers on wave3/wave4 branches only until cleanup merges.
3. **Incomplete domain folders** — acceptable; tests and docs reflect target layout.

---

## Recommendation

**Merge cleanup PR** to `dev` or `main` per governance. Schedule Wave 6b for structural remainder without blocking Wave 5 hardening (NT-128–130).
