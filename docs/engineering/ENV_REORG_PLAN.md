# Environment reorg — demo → dev / pilot / production

**Date:** 2026-10-21
**Owner:** Tech Lead
**Branch:** `feature/mobile-first-pilot-cycle`
**Status:** Repo side done. Server/GitHub cutover pending (see [Follow-ups](#follow-ups)).
**Related:** [environments.md](../guides/environments.md) (env matrix), [pilot-stack.md](../guides/pilot-stack.md), [MOBILE_FIRST_CLEANUP_PLAN.md](./MOBILE_FIRST_CLEANUP_PLAN.md)

## Goal

Retire the overloaded **demo** naming. Orbit has exactly three environments:

| Env | `APP_ENV` | Purpose | Compose | Server env file | License |
|-----|-----------|---------|---------|-----------------|---------|
| **Dev** | `development` | Local coding, hybrid Vite, CI | `docker-compose-local.yml` (+ `-hybrid`) | `deploy/dev/.env` (optional) | Bypassed |
| **Pilot** | `pilot` | Sales, UAT, field pilot (was "demo") | `docker-compose-local.yml` + `docker-compose-pilot.yml` (+ `deploy/pilot/docker-compose.live.yml` on the VM) | `deploy/pilot/.env` | Bypassed |
| **Production** | `production` | Paying tenants | `docker-compose-prod.yml` | `deploy/production/.env` | Enforced |

Any other `APP_ENV` value now fails at startup (see [Compatibility aliases](#compatibility-aliases)).

## Layout after the reorg

```
deploy/
  Dockerfile.api, Dockerfile.web, nginx.conf
  dev/          .env.example
  pilot/        .env.example, .env.supabase.example, docker-compose.live.yml, setup-ubuntu.sh, README.md
  production/   .env.example
docker-compose-local.yml           # dev stack
docker-compose-hybrid.yml          # dev: host API + Docker DB
docker-compose-pilot.yml           # pilot overlay (project fms-pilot, volume fms_pilot_pgdata)
docker-compose-pilot-supabase.yml  # pilot against managed Postgres
docker-compose-prod.yml            # production
```

Only `.env*.example` files are tracked. `.gitignore` covers `deploy/{dev,pilot,production,demo}/.env` and `deploy/pilot/.env.supabase`.

## Inventory — what changed

### Renamed (`git mv`, history preserved)

| From | To |
|------|----|
| `.github/workflows/deploy-orbit-demo.yml` | `.github/workflows/deploy-orbit-pilot.yml` |
| `.github/workflows/playwright-e2e-demo.yml` | `.github/workflows/playwright-e2e-pilot.yml` |
| `backend/app/cli/pitch_seed.py` | `backend/app/cli/pilot_seed.py` (`seed_pilot()`) |
| `backend/app/cli/_demo_passwords.py` | `backend/app/cli/_seed_passwords.py` |
| `backend/tests/domains/platform/test_demo_environment.py` | `.../test_pilot_environment.py` |
| `deploy/pilot/BRANCH_MANIFEST.md` | `deploy/pilot/README.md` (rewritten) |

### Moved in the wave-1 commit (`b908b30`)

| From | To |
|------|----|
| `deploy/demo/*` (examples, live overlay, setup script) | `deploy/pilot/*` |
| `docker-compose-demo.yml` content | `docker-compose-pilot.yml` |
| `docker-compose-supabase-demo.yml` content | `docker-compose-pilot-supabase.yml` |
| `backend/.env.demo.example` | `backend/.env.pilot.example` |
| `docs/phase3-restructure/DEMO_*.md` | `docs/archive/demo/` |

### Deleted (`git rm`)

| Path | Replaced by |
|------|-------------|
| `docker-compose-demo.yml` | `docker-compose-pilot.yml` |
| `docker-compose-supabase-demo.yml` | `docker-compose-pilot-supabase.yml` |
| `backend/.env.demo.example` | `backend/.env.pilot.example` |
| `deploy/demo/.env.example`, `.env.supabase-demo.example` | `deploy/pilot/.env.example`, `.env.supabase.example` |
| `deploy/demo/docker-compose.live.yml`, `setup-ubuntu.sh` | `deploy/pilot/` equivalents |
| `deploy/demo/README.md`, `BRANCH_MANIFEST.md` | `deploy/pilot/README.md` (original archived) |
| `docs/guides/demo-stack.md` | `docs/guides/pilot-stack.md` (original archived) |

### Archived under `docs/archive/demo/`

`demo-stack.md`, `BRANCH_MANIFEST.md`, `supabase-demo-runbook.md`, plus the phase3 `DEMO_*.md` files from wave 1. Historical wave sign-off docs in `docs/phase3-restructure/WAVE*` and `docs/knowledge-hub/product/` still mention demo paths. They are point-in-time records and were left as written.

### Code changes

- `backend/app/config.py`: `APP_ENV` is normalised and validated (`development` / `pilot` / `production`). New `is_pilot` and `bypasses_license` properties.
- `backend/app/domains/platform/router.py`: `POST /platform/pilot/reset` (canonical), and `POST /platform/demo/reset` (hidden alias). Both return 403 `PILOT_ENV_ONLY` outside pilot.
- `backend/app/services/subscription.py`: license bypass uses `settings.bypasses_license`.
- `backend/app/cli/docker_migrate.py`: `SEED_MODULE=pilot` (canonical) and `pitch` (alias).
- `deploy/pilot/docker-compose.live.yml`: only nginx is published (`WEB_PORT`, default 8080). DB and API host ports are removed with `!reset []`. `SECRET_KEY`, `CORS_ORIGINS` and `PUBLIC_APP_URL` are required.
- `deploy-orbit-pilot.yml`: deploys `pilot/live` (or legacy `demo/live`). Reads `PILOT_*` secrets with a `DEMO_*` fallback. It moves `deploy/demo/.env` to `deploy/pilot/.env` once, stops the old `fms-demo` project (the volume is kept), then starts `fms-pilot`.
- `ci.yml`: runs on `feature/**` and `pilot/live` PRs and runs the `check:imports` guard.
- Frontend CLEAN-002 to CLEAN-004: the `src/pages/*` and `src/components/*` shims were removed and `scripts/check-legacy-imports.mjs` was added (commits `28eca74`, `f2e4110`).

## Compatibility aliases

Kept for one release cycle so the live VM and old scripts keep working. Remove them in ENV-F02.

| Legacy | Resolves to | Where |
|--------|-------------|-------|
| `APP_ENV=demo` / `dev` / `prod` | `pilot` / `development` / `production` | `config.py` validator |
| `SEED_MODULE=pitch` | `pilot` | `docker_migrate.py` |
| `DEMO_PASSWORD_SUFFIX` | `SEED_PASSWORD_SUFFIX` | `_seed_passwords.py` |
| `POST /platform/demo/reset` | `/platform/pilot/reset` | platform router (hidden from OpenAPI) |
| `app.pitch_seed`, `seed_pitch_demo` | `app.cli.pilot_seed.seed_pilot` | shim module |
| `secrets.DEMO_*`, `vars.DEMO_URL`, branch `demo/live` | `PILOT_*`, `PILOT_URL`, `pilot/live` | deploy workflow |

## Cutover (live VM)

1. Merge to `main`, then push the deploy branch (`demo/live` still works, or create `pilot/live`).
2. The workflow handles the env-file move, `fms-demo` down and `fms-pilot` up automatically.
3. **Data:** the new project uses volume `fms_pilot_pgdata`, so the pilot starts with a freshly seeded DB. The old `fms_demo_pgdata` volume is **not** deleted. If you need to carry demo data over, `pg_dump` from the old volume before step 1 and restore it into the pilot DB afterwards.
4. Smoke test: `curl -f http://<host>:8080/api/v1/health`, then log in with a seed account.

**Rollback:** `docker compose -p fms-pilot down`, check out the previous commit, then run `docker compose -f docker-compose-local.yml -f docker-compose-demo.yml -f deploy/demo/docker-compose.live.yml -p fms-demo up -d`. The old volume is still intact.

## Verification (run on this branch)

| Check | Result |
|-------|--------|
| `docker compose ... config` for local, hybrid, pilot, pilot + live, and pilot-supabase | All parse. Pilot + live publishes only `8080`, with `APP_ENV=pilot`, `SEED_MODULE=pilot` and volume `fms_pilot_pgdata` |
| `pytest tests/domains/platform/test_pilot_environment.py test_app_env.py` | 32 passed* |
| Full backend `pytest` | 252 passed, 1 failed* (`test_error_handler_expands_string_code` also fails on clean `HEAD`) |
| `npm run check:imports` | OK |
| `npm run build` | OK |
| `rg` for deleted paths (`docker-compose-demo`, `deploy/demo/`, `demo-stack.md`, `pitch_seed`, ...) | Only compat code, this plan, and historical wave records |
| `git log -p` for secrets | None. Local `deploy/demo/.env.supabase-demo` is untracked and was not touched |

\* Locally, every `api_client` test errors with `no such table: tenants`, on clean `HEAD` too. The `TestClient` lifespan runs `ensure_schema` and bootstrap on the app's own `sqlite:///:memory:` engine, which has no Alembic tables. The numbers above came from running with a throwaway pytest plugin that swaps in a no-op lifespan. The plugin is not committed; see ENV-F08.

## Follow-ups

| ID | Item | Owner |
|----|------|-------|
| ENV-F01 | Add GitHub secrets `PILOT_*` and `vars.PILOT_URL`, create branch `pilot/live`, retire `demo/live` and the `DEMO_*` secrets | Ops |
| ENV-F02 | After cutover, remove the aliases in the table above, including the `/demo/reset` route and the `app/pitch_seed.py` shim | BE |
| ENV-F03 | Login page pre-fills seed credentials and uses `login_demo_*` i18n keys in every env. Gate this to dev and pilot only, and rename the keys | FE |
| ENV-F04 | Seed data still uses `@demo.com` emails and the "Demo Facility Co" tenant. Renaming them touches e2e fixtures and shared logins, so do it in one coordinated PR | BE + QA |
| ENV-F05 | Rename `E2E_DEMO_PASSWORD_SUFFIX` and `VITE_DEMO_PASSWORD_SUFFIX` to `*_SEED_PASSWORD_SUFFIX` | FE + QA |
| ENV-F06 | DNS: `demo.orbittech.co` stays for now. Optionally add `pilot.orbittech.co` | Ops |
| ENV-F07 | Operators: move local `deploy/demo/.env.supabase-demo` to `deploy/pilot/.env.supabase`, then delete `deploy/demo/` | Each dev |
| ENV-F08 | Fix the test lifespan so `api_client` doesn't hit the app engine (override `SessionLocal`/`engine` in `conftest.py` or skip bootstrap under test) | BE |
| ENV-F09 | Drop the old `fms_demo_pgdata` volume on the VM once the pilot is confirmed healthy | Ops |
