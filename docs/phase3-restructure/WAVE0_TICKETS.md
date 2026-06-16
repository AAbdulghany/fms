# Wave 0 Ticket Tracker

**Epic:** Phase 3 Multi-Tenant Restructure  
**Gate:** ✅ CLOSED — Wave 1 unblocked  
**Sign-off:** [WAVE0_SIGNOFF.md](WAVE0_SIGNOFF.md)

| Ticket | Title | Agent | Status | Tests | GitHub |
|--------|-------|-------|--------|-------|--------|
| NT-101 | AgDR sign-off + ERD | solution-architect | ✅ Done | — | [#3](https://github.com/AAbdulghany/fms/issues/3) |
| NT-102 | DB migration tables | backend-engineer | ✅ Done | 4/4 | [#4](https://github.com/AAbdulghany/fms/issues/4) |
| NT-103 | Migrate settings_json | backend-engineer | ✅ Done | 3/3 | [#6](https://github.com/AAbdulghany/fms/issues/6) |
| NT-104 | APP_ENV matrix | platform-engineer | ✅ Done | 4/4 | [#5](https://github.com/AAbdulghany/fms/issues/5) |

## Wave 0 exit criteria

- [x] NT-101 ERD published; AgDR approved for build
- [x] NT-102 tables exist on startup
- [x] NT-103 legacy migration idempotent
- [x] NT-104 `APP_ENV` documented; dev/demo bypass
- [x] `uv run pytest tests/test_wave0_*.py -q` — 11 passed
- [x] Full suite — **142 passed**, 0 regressions

## Wave 1 (next)

| Ticket | Title | Depends |
|--------|-------|---------|
| NT-105 | Platform API: CRUD subscription_packages | NT-102 |
| NT-106 | Assign package + valid_until to tenant | NT-105 |
| NT-107 | License freeze middleware + dev bypass | NT-103 |
| NT-108 | Feature gate dependency | NT-105 |
