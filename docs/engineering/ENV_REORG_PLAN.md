# Environment reorg — demo → pilot / dev / production

**Date:** 2026-10-21  
**Owner:** Tech Lead  
**Status:** In progress (wave 1 — structure + aliases)  
**Related:** [MOBILE_FIRST_CLEANUP_PLAN.md](./MOBILE_FIRST_CLEANUP_PLAN.md), [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md)

## Goal

Retire the overloaded **demo** naming. Orbit has three environments:

| Env | `APP_ENV` | Purpose | Typical DB | License |
|-----|-----------|---------|------------|---------|
| **Dev** | `development` | Local coding, hybrid Vite | `fms_local` / `fms_dev` | Bypassed |
| **Pilot** | `pilot` | Sales/UAT/field pilot (was “demo”) | `fms_pilot` | Bypassed |
| **Production** | `production` | Paying tenants | `fms_prod` | Enforced |

`APP_ENV=demo` remains accepted as a **deprecated alias of `pilot`** until CI and the live VM are cut over (wave 2).

## Layout

```
deploy/
  Dockerfile.api
  Dockerfile.web
  nginx.conf
  dev/           # local/dev overlays + .env.example
  pilot/         # was deploy/demo/
  production/    # production overlay + .env.example

docker-compose-local.yml          # DEV stack (unchanged name)
docker-compose-hybrid.yml         # DEV host-API overlay
docker-compose-pilot.yml          # PILOT stack (canonical)
docker-compose-demo.yml           # DEPRECATED → same as pilot (compat)
docker-compose-prod.yml           # PRODUCTION
docker-compose-pilot-supabase.yml # optional managed-Postgres pilot
```

## Wave 1 (this change)

- [x] Document matrix + plan
- [x] `deploy/dev`, `deploy/pilot`, `deploy/production` with `.env.example` only
- [x] `docker-compose-pilot.yml` (+ optional supabase pilot compose)
- [x] Keep `docker-compose-demo.yml` working but marked deprecated
- [x] Backend treats `pilot` like `demo` for license bypass + reset endpoint
- [x] Archive phase3 DEMO_*.md under `docs/archive/demo/`
- [x] New guide: `docs/guides/environments.md`
- [x] `npm run check:imports` (CLEAN-002 guard) + `backend/.env.pilot.example`
- [ ] Point CI workflows at pilot (wave 2 — needs secret renames on GitHub)
- [ ] Rename DB volume `fms_demo` → `fms_pilot` on live VM (wave 2 — data migration)

## Wave 2 (cutover — separate PR)

**Partial (this branch):** Playwright E2E uses `docker-compose-pilot.yml`; deploy workflow comments + display name say Pilot but still uses `DEMO_*` secrets and `deploy/demo/` paths on the VM; CI runs `check:imports`.

Still needs a human:

1. Rename GitHub secrets `DEMO_*` → `PILOT_*` (or keep aliases).
2. Rename workflow `deploy-orbit-demo.yml` → `deploy-orbit-pilot.yml`; branch `demo/live` → `pilot/live` if desired.
3. On the VM: copy `deploy/demo/.env` → `deploy/pilot/.env`, switch compose to pilot files, then remove `docker-compose-demo.yml`.
4. Drop `APP_ENV=demo` alias after tests updated.
5. Delete `deploy/demo/` when live path no longer references it.

## What NOT to delete yet

| Path | Why keep |
|------|----------|
| `backend/app/pitch_seed.py` | Still seeds pilot; rename later to `pilot_seed` |
| `backend/app/cli/_demo_passwords.py` | Used by pitch seed; rename with seed |
| `.github/workflows/*demo*` | Live deploy until secrets renamed |
| Public hostname `demo.orbittech.co` | DNS/marketing; can stay or CNAME `pilot.` |

## Verification

```bash
# Dev
docker compose -f docker-compose-local.yml config >/dev/null

# Pilot
docker compose -f docker-compose-pilot.yml config >/dev/null

# Deprecated alias still parses
docker compose -f docker-compose-demo.yml config >/dev/null

# Backend env helpers
cd backend && pytest tests/domains/platform/test_app_env.py -q
```

## Cleanup tickets (parallel)

Continue [CLEAN-002](./tickets/CLEAN-002.md) … [CLEAN-004](./tickets/CLEAN-004.md) for frontend shim removal on the same hygiene wave.
