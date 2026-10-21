# Environments — dev / pilot / production

Orbit no longer uses **demo** as the primary name. Use:

| Env | When | Command |
|-----|------|---------|
| **Dev** | Day-to-day coding | `docker compose -f docker-compose-local.yml up -d --build` or hybrid + Vite — [local-development.md](./local-development.md) |
| **Pilot** | Sales, UAT, field pilot | `docker compose -f docker-compose-pilot.yml up -d --build` |
| **Production** | Paying tenants | `docker compose -f docker-compose-prod.yml` + [deployment.md](./deployment.md) |

Config templates live under `deploy/dev/`, `deploy/pilot/`, `deploy/production/` (`.env.example` only — never commit secrets).

## Pilot ports (same as former demo)

| Service | Host port |
|---------|-----------|
| Web (UI) | **9081** |
| API | **9001** |
| Postgres | **9543** |

Open **http://localhost:9081**.

## Managed Postgres (Supabase) pilot

```bash
cp deploy/pilot/.env.supabase.example deploy/pilot/.env.supabase
# fill DATABASE_URL + SECRET_KEY
docker compose -f docker-compose-pilot-supabase.yml --env-file deploy/pilot/.env.supabase up -d --build
```

UI: http://localhost:9581 · API: http://localhost:9501

## Deprecated

- `docker-compose-demo.yml` — still works; prefer `docker-compose-pilot.yml`
- `docs/phase3-restructure/DEMO_*.md` — archived under `docs/archive/demo/`
- `APP_ENV=demo` — accepted as alias of `pilot` until wave-2 cutover

Full plan: [ENV_REORG_PLAN.md](../engineering/ENV_REORG_PLAN.md)
