# Cleanup Stage — Wave 6 (Repo Hygiene & Documentation)

**Status:** Complete — pending merge ([PR #20](https://github.com/AAbdulghany/fms/pull/20))  
**Branch:** `feature/phase-3-restructure/cleanup`  
**Progress:** [WAVE6_PROGRESS.md](./phase3-restructure/WAVE6_PROGRESS.md)

---

## Goals — all met (except optional deferrals)

| Goal | Status |
|------|--------|
| Feature-oriented layout | ✅ Routes → `domains/`; UI → `features/` + `shared/` |
| Remove dead code + artifacts | ✅ |
| Single source of truth for run/test/deploy | ✅ `docs/guides/*` |
| Archive superseded phase docs | ✅ `docs/archive/` |

---

## Phase completion

| Phase | Status |
|-------|--------|
| **C0** Hygiene | ✅ 100% |
| **C1** Docs IA | ✅ 100% |
| **C2** Backend domains + cli | ✅ ~95% (services stay in `app/services/`) |
| **C3** Frontend features + shared | ✅ ~95% (i18n monolith deferred) |
| **C4** Tests by domain | ✅ 100% |
| **C5** models/schemas + AgDR | ✅ 100% |

---

## Layout (final)

```
backend/app/domains/{auth,users,clients,assets,work_orders,reports,billing,platform,…}
backend/app/cli/{docker_migrate,seed*,report_template_sync_cli}
backend/app/api/routes/*.py          # shims → domains

src/features/{auth,companies,assets,work-orders,invoices,…}/pages|components
src/shared/{lib,components}
src/pages/*.tsx                      # shims → features
src/components/*.tsx                 # shims → shared/features

backend/tests/domains/*
tests/e2e/domains/*
```

---

## Gates

| Gate | Result |
|------|--------|
| pytest 219+ | ✅ |
| npm run build | ✅ |
| Rex review | ⬜ |
| Human merge | ⬜ |
