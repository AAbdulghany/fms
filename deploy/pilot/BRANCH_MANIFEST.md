# Pilot deploy file manifest

`deploy/pilot/` holds pilot-specific overlays (was `deploy/demo/`).

| Path | Purpose |
|------|---------|
| `docker-compose-pilot.yml` | Pilot DB `fms_pilot`, `APP_ENV=pilot`, pitch seed |
| `deploy/pilot/` | Live overlay, env templates, Ubuntu setup |
| `backend/app/pitch_seed.py` | Pitch/pilot seed data + logins |
| `docs/guides/environments.md` | How to run dev / pilot / production |

See [ENV_REORG_PLAN.md](../../docs/engineering/ENV_REORG_PLAN.md).
