# deploy/pilot

Server-side files for the **pilot** environment (sales, UAT, field pilot). This folder replaces `deploy/demo/`.

| File | Purpose |
|------|---------|
| `.env.example` | Template for `deploy/pilot/.env` on the live VM (Supabase URLs + secrets). Gitignored real `.env`. |
| `.env.supabase.example` | Same fields for local `docker-compose-pilot-supabase.yml` via `.env.supabase`. |
| `docker-compose.live.yml` | Overlay for **embedded** Postgres pilot (`docker-compose-pilot.yml`) — local/dev only. |
| `docker-compose.live-supabase.yml` | **Canonical live overlay** — publishes only web on `WEB_PORT`; no local db. |
| `setup-ubuntu.sh` | One-time Docker install and firewall setup on a fresh Ubuntu VM. |
| `smoke-pilot.sh` | Health → platform login → provision company → company login. |

## Run on the server (always-on + Supabase)

```bash
cp deploy/pilot/.env.example deploy/pilot/.env && chmod 600 deploy/pilot/.env
# Set SECRET_KEY, DATABASE_URL (pooler), DATABASE_URL_MIGRATE (session/direct),
# PUBLIC_APP_URL, CORS_ORIGINS, WEB_PORT

docker compose -f docker-compose-pilot-supabase.yml \
  -f deploy/pilot/docker-compose.live-supabase.yml \
  --env-file deploy/pilot/.env up -d --build

# Stop any leftover embedded-Postgres pilot stack
docker compose -p fms-pilot down --remove-orphans || true
```

Point the Cloudflare Tunnel at `http://localhost:${WEB_PORT}` (default `8080`).

The `Deploy Orbit Pilot` workflow (`.github/workflows/deploy-orbit-pilot.yml`) runs these commands on every push to `pilot/live`.

### Smoke after deploy

```bash
BASE_URL=https://demo.orbittech.co bash deploy/pilot/smoke-pilot.sh
# or on the VM:
BASE_URL=http://127.0.0.1:8080 bash deploy/pilot/smoke-pilot.sh
```

## More information

- Environment matrix: [docs/guides/environments.md](../../docs/guides/environments.md)
- Pilot runbook: [docs/guides/pilot-stack.md](../../docs/guides/pilot-stack.md)
- Cutover from demo: [docs/engineering/ENV_REORG_PLAN.md](../../docs/engineering/ENV_REORG_PLAN.md)
