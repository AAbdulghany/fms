# Deployment

Deploy Orbit demo or production stacks. **Local demo commands:** [demo-stack.md](./demo-stack.md).

---

## Deployment profiles

| Profile | `APP_ENV` | Database | Seed | License gates |
|---------|-----------|----------|------|---------------|
| Development | `development` | `fms` | manual / test_seed | Bypassed |
| Pitch demo | `demo` | `fms_demo` | pitch_seed | Bypassed |
| Production | `production` | dedicated | minimal | Enforced |

See [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md).

---

## Docker images

| Service | Dockerfile | Notes |
|---------|------------|-------|
| API | `deploy/Dockerfile.api` | FastAPI, Alembic, app code |
| Web | `deploy/Dockerfile.web` | `npm run build` → nginx |
| Nginx config | `deploy/nginx.conf` | SPA + `/api` proxy to `api:8000` |

### Compose files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base: db, migrate, api, web |
| `docker-compose.demo.yml` | Overlay: `fms_demo`, `APP_ENV=demo`, pitch seed |
| `docker-compose.local.yml` | DB + migrate only (host API/UI) |
| `deploy/demo/docker-compose.live.yml` | Production VM: web on port 80, env from file |

---

## Local demo (reference)

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

→ http://localhost:8080

---

## Public demo (`demo/live` branch)

Step-by-step guide: [DEMO_LIVE_DEPLOY.md](../phase3-restructure/DEMO_LIVE_DEPLOY.md)

Summary:

1. Ensure tests pass locally (pytest, build, demo compose smoke)
2. Maintain branch **`demo/live`** — demo-stable merges only
3. Tag releases: `demo-live-vX.Y.Z`
4. On server (recommended: Oracle Cloud free VM):

```bash
git clone -b demo/live <repo-url> /opt/fms
cd /opt/fms
cp deploy/demo/.env.example deploy/demo/.env   # edit SECRET_KEY, PUBLIC_APP_URL, CORS
docker compose -f docker-compose.yml \
  -f docker-compose.demo.yml \
  -f deploy/demo/docker-compose.live.yml \
  --env-file deploy/demo/.env up -d --build
```

`docker-compose.live.yml` exposes web on `${WEB_PORT:-80}:8080` and requires secrets via env file.

Manifest: [deploy/demo/BRANCH_MANIFEST.md](../../deploy/demo/BRANCH_MANIFEST.md)

---

## Cloud / PaaS (Railway, Render)

High-level steps (see also archived [phase3.1/DEMO_DEPLOY.md](../phase3.1/DEMO_DEPLOY.md)):

1. Managed PostgreSQL → set `DATABASE_URL`
2. API service from `deploy/Dockerfile.api`
3. Web service from `deploy/Dockerfile.web` **or** nginx container serving built static files
4. Required env vars:

```env
DATABASE_URL=postgresql+psycopg2://...
SECRET_KEY=<random-32+-chars>
JWT_SECRET=<random-32+-chars>
APP_ENV=demo                    # or production
CORS_ORIGINS=https://your-domain
PUBLIC_APP_URL=https://your-domain
```

5. One-off migrate + seed:

```bash
python -m app.docker_migrate    # with SEED_MODULE=pitch for demo
# or: alembic upgrade head && python -m app.pitch_seed
```

6. Optional nightly demo reset: cron → `POST /api/v1/platform/demo/reset` (demo env only)

---

## Production checklist

- [ ] `APP_ENV=production`
- [ ] Strong `SECRET_KEY` / `JWT_SECRET` (not dev defaults)
- [ ] Dedicated PostgreSQL (`DATABASE_URL`)
- [ ] Alembic at head: `alembic upgrade head`
- [ ] Minimal seed: `python -m app.seed_super` — change default password
- [ ] `CORS_ORIGINS` matches actual frontend origin(s)
- [ ] HTTPS termination (reverse proxy or platform)
- [ ] SMTP configured if email notifications required
- [ ] Backups scheduled for PostgreSQL
- [ ] Do **not** expose demo reset endpoint in production

---

## Environment variables (API)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `SECRET_KEY` | yes | App secret |
| `JWT_SECRET` | yes | Token signing |
| `APP_ENV` | yes | `development` \| `demo` \| `production` |
| `CORS_ORIGINS` | prod | Comma-separated allowed origins |
| `PUBLIC_APP_URL` | prod | Canonical app URL (links, emails) |
| `SEED_MODULE` | migrate | `pitch` or `test` (docker_migrate only) |
| `SMTP_*` | optional | Outbound email |

Examples: `backend/.env.example`, `backend/.env.demo.example`, `deploy/demo/.env.example`

---

## Related

- [demo-stack.md](./demo-stack.md) — local Docker demo
- [local-development.md](./local-development.md) — host development
- [PIPELINE_ARCHITECTURE.md](../phase3-restructure/PIPELINE_ARCHITECTURE.md) — CI/CD
