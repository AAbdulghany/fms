# Environments: dev, pilot, production

Orbit has three environments. "Demo" is retired as an environment name; the sales and UAT stack is now **pilot**.

## Environment matrix

| | **Dev** | **Pilot** | **Production** |
|---|---|---|---|
| Purpose | Day-to-day coding, CI | Sales, UAT, field pilot | Paying tenants |
| `APP_ENV` | `development` | `pilot` | `production` |
| License freeze | Bypassed | Bypassed | Enforced |
| `POST /platform/pilot/reset` | 403 | Allowed (platform admin) | 403 |
| Compose file | `docker-compose-local.yml` (+ `docker-compose-hybrid.yml` for host API + Vite) | `docker-compose-pilot.yml` (+ `deploy/pilot/docker-compose.live.yml` on the server) or `docker-compose-pilot-supabase.yml` | `docker-compose-prod.yml` |
| Compose project | `fms-local` | `fms-pilot` / `fms-pilot-supabase` | set by operator |
| Database | `fms_local` on host port 9432 | `fms_pilot` on host port 9543 (or Supabase) | External, `DATABASE_URL` required |
| Seed (`SEED_MODULE`) | `test` (users only) | `pilot` (rich dataset) | none (schema only; create the first super user manually) |
| Host ports (web / API) | 9080 / 9000 (Docker) or 5173 / 8000 (hybrid) | 9081 / 9001 locally; only `WEB_PORT` on the server | `WEB_PORT` / `API_PORT` |
| Env templates | `deploy/dev/.env.example`, `backend/.env.example` | `deploy/pilot/.env.example`, `deploy/pilot/.env.supabase.example`, `backend/.env.pilot.example` | `deploy/production/.env.example` |
| Deploy | — | `.github/workflows/deploy-orbit-pilot.yml` on push to `pilot/live` | Manual (see [deployment.md](./deployment.md)) |
| Guide | [local-development.md](./local-development.md) | [pilot-stack.md](./pilot-stack.md) | [deployment.md](./deployment.md) |

## Rules

- Commit only `*.example` env files. Every real `deploy/<env>/.env*` file is gitignored. Never commit secrets.
- `APP_ENV` accepts only `development`, `pilot`, or `production`. The backend rejects any other value at startup. The legacy spellings `demo`, `dev`, and `prod` are mapped to the canonical names.
- Dev and pilot use different compose project names and ports, so both can run at the same time.
- Production never runs a rich seed. Seed passwords are public.

## Deprecated names (still accepted during cutover)

| Old | New | Removed when |
|-----|-----|--------------|
| `APP_ENV=demo` | `APP_ENV=pilot` | After the pilot VM env file is updated (ENV-F02) |
| `SEED_MODULE=pitch` | `SEED_MODULE=pilot` | Same |
| `DEMO_PASSWORD_SUFFIX` | `SEED_PASSWORD_SUFFIX` | Same |
| `POST /platform/demo/reset` | `POST /platform/pilot/reset` | After cron jobs are updated |
| `app.pitch_seed` / `seed_pitch_demo` | `app.cli.pilot_seed` / `seed_pilot` | Next release |
| Branch `demo/live`, secrets `DEMO_*` | Branch `pilot/live`, secrets `PILOT_*` | After the GitHub cutover (ENV-F01) |

Removed files (`docker-compose-demo.yml`, `deploy/demo/`, `backend/.env.demo.example`) and the cutover steps are listed in [ENV_REORG_PLAN.md](../engineering/ENV_REORG_PLAN.md). Pre-reorg docs are in [docs/archive/demo/](../archive/demo/).
