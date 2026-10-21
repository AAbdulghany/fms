# deploy/pilot

Server-side files for the **pilot** environment (sales, UAT, field pilot). This folder replaces `deploy/demo/`.

| File | Purpose |
|------|---------|
| `.env.example` | Template for `deploy/pilot/.env` on the server. The real `.env` is gitignored. |
| `.env.supabase.example` | Template for `deploy/pilot/.env.supabase`, used with `docker-compose-pilot-supabase.yml`. |
| `docker-compose.live.yml` | Live overlay. It publishes only the web container on `WEB_PORT` and requires real secrets. |
| `setup-ubuntu.sh` | One-time Docker install and firewall setup on a fresh Ubuntu VM. |

## Run on the server

```bash
cp deploy/pilot/.env.example deploy/pilot/.env && chmod 600 deploy/pilot/.env
docker compose -f docker-compose-pilot.yml -f deploy/pilot/docker-compose.live.yml \
  --env-file deploy/pilot/.env up -d --build
```

The `Deploy Orbit Pilot` workflow (`.github/workflows/deploy-orbit-pilot.yml`) runs these commands on every push to `pilot/live`.

## More information

- Environment matrix: [docs/guides/environments.md](../../docs/guides/environments.md)
- Pilot runbook: [docs/guides/pilot-stack.md](../../docs/guides/pilot-stack.md)
- Cutover from demo: [docs/engineering/ENV_REORG_PLAN.md](../../docs/engineering/ENV_REORG_PLAN.md)
