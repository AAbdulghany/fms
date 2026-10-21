# Demo branch file manifest

The **`demo/live`** branch is the **deployable demo snapshot** — it contains the **full application** plus demo-specific configuration. You cannot run the pitch demo with config files alone; the API, frontend, and seed code are required.

## Demo-specific files (what makes `demo/live` different from dev)

| Path | Purpose |
|------|---------|
| `docker-compose-demo.yml` | Demo DB `fms_demo`, `APP_ENV=demo`, pitch seed |
| `deploy/demo/` | Live overlay, env template, Ubuntu setup script |
| `backend/app/pitch_seed.py` | Pitch demo data + logins |
| `backend/app/docker_migrate.py` | Migrate + seed entrypoint for containers |
| `backend/.env.demo.example` | Local uvicorn → `fms_demo` |
| `docs/phase3-restructure/DEMO_QUICKSTART.md` | Local Docker commands + logins |
| `docs/phase3-restructure/DEMO_LIVE_DEPLOY.md` | **Public server deployment plan** |
| `docs/phase3-restructure/DEMO_DEPLOY.md` | Demo profile reference |
| `docs/phase3-restructure/RBAC_ROLES.md` | Role model for evaluators |
| `.claude/skills/docker-debug/` | Compose troubleshooting |
| `.claude/skills/frontend-build/` | Frontend build / i18n troubleshooting |

## Shared files (required for demo to run)

| Path | Purpose |
|------|---------|
| `docker-compose-local.yml` | Base stack (db, migrate, api, web) |
| `deploy/Dockerfile.api`, `deploy/Dockerfile.web`, `deploy/nginx.conf` | Container images |
| `backend/` | FastAPI application |
| `src/` | React frontend |
| `package.json`, `vite.config.*` | Frontend build |

## What `demo/live` must **not** include (optional cleanup)

- Local `.env` with secrets
- Developer-only test databases
- Unfinished feature branches without demo seed compatibility

## Branch commands (run after committing demo-ready work)

```powershell
# From repo root, on your integrated branch (e.g. feature/phase3)
git checkout -b demo/live
git push -u origin demo/live

# Tag a frozen snapshot for rollback
git tag demo-live-v1.0.0
git push origin demo-live-v1.0.0
```

## Updating the live server

```powershell
git checkout demo/live
git merge feature/phase3   # or cherry-pick fixes
git push origin demo/live

# On server:
cd /opt/fms
git pull origin demo/live
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml -f deploy/demo/docker-compose.live.yml --env-file deploy/demo/.env up -d --build
```
