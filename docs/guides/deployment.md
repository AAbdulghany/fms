# Deployment

Deploy the Orbit **pilot** or **production** stacks. For the environment matrix, see [environments.md](./environments.md). For local pilot commands, see [pilot-stack.md](./pilot-stack.md).

---

## Deployment profiles

| Profile | `APP_ENV` | Database | Seed | License gates |
|---------|-----------|----------|------|---------------|
| Dev | `development` | `fms_local` | `test` | Bypassed |
| Pilot | `pilot` | `fms_pilot` (or Supabase) | `pilot` | Bypassed |
| Production | `production` | dedicated | none (manual super user) | Enforced |

The backend rejects any other `APP_ENV` value at startup. `demo` is still accepted and maps to `pilot`.

---

## Docker images

| Service | Dockerfile | Notes |
|---------|------------|-------|
| API | `deploy/Dockerfile.api` | FastAPI, Alembic, app code |
| Web | `deploy/Dockerfile.web` | `npm run build` → nginx |
| Nginx config | `deploy/nginx.conf` | SPA + `/api` proxy to `api:8000` |

### Compose files

| File | Environment | Purpose |
|------|-------------|---------|
| `docker-compose-local.yml` | Dev | db, migrate, api, web (`fms-local`) |
| `docker-compose-hybrid.yml` | Dev | Overlay: DB + migrate only, for host API and Vite |
| `docker-compose-pilot.yml` | Pilot | Self-contained stack (`fms-pilot`), `APP_ENV=pilot`, pilot seed |
| `deploy/pilot/docker-compose.live.yml` | Pilot | Server overlay: publishes only web on `WEB_PORT`; secrets from `deploy/pilot/.env` |
| `docker-compose-pilot-supabase.yml` | Pilot | Pilot against managed Postgres; no db container |
| `docker-compose-prod.yml` | Production | Prebuilt images; every secret required from the environment |

---

## Pilot server (`pilot/live` branch)

1. Make sure tests pass (pytest, `npm run build`, a pilot compose smoke test).
2. Merge pilot-ready work into **`pilot/live`**. Tag snapshots as `pilot-live-vX.Y.Z`.
3. First-time server setup (for example, an Oracle Cloud free VM with Cloudflare Tunnel):

```bash
git clone -b pilot/live <repo-url> /opt/fms
cd /opt/fms
sudo bash deploy/pilot/setup-ubuntu.sh
cp deploy/pilot/.env.example deploy/pilot/.env && chmod 600 deploy/pilot/.env
# set SECRET_KEY, PUBLIC_APP_URL, CORS_ORIGINS, WEB_PORT
docker compose -f docker-compose-pilot.yml \
  -f deploy/pilot/docker-compose.live.yml \
  --env-file deploy/pilot/.env up -d --build
```

4. Subsequent deploys run automatically on push to `pilot/live` through [`.github/workflows/deploy-orbit-pilot.yml`](../../.github/workflows/deploy-orbit-pilot.yml).

The live overlay publishes only the web container. nginx proxies `/api`, so the API and database have no host ports. Point the Cloudflare Tunnel at `http://localhost:${WEB_PORT}`.

Server file reference: [deploy/pilot/README.md](../../deploy/pilot/README.md). Cutover from the old demo stack: [ENV_REORG_PLAN.md](../engineering/ENV_REORG_PLAN.md).

---

## Production

```bash
cp deploy/production/.env.example deploy/production/.env   # on the server only
set -a; . deploy/production/.env; set +a
export API_IMAGE=<registry>/fms-api:<tag> WEB_IMAGE=<registry>/fms-web:<tag>
docker compose -f docker-compose-prod.yml up -d
```

`docker_migrate` runs with the default `SEED_MODULE=test` unless you override it. For production, run schema only and create the first super user manually:

```bash
alembic upgrade head
python -m app.seed_super   # then change the password immediately
```

### Production checklist

- [ ] `APP_ENV=production`
- [ ] Strong `SECRET_KEY` (not a dev default). It signs access and refresh tokens.
- [ ] Dedicated PostgreSQL (`DATABASE_URL`)
- [ ] Alembic at head: `alembic upgrade head`
- [ ] No rich seed. Seed passwords are public.
- [ ] `CORS_ORIGINS` matches the real frontend origin(s)
- [ ] HTTPS termination (reverse proxy or platform)
- [ ] SMTP configured if email notifications are required
- [ ] PostgreSQL backups scheduled
- [ ] `POST /platform/pilot/reset` returns 403 (it does whenever `APP_ENV=production`)

---

## Cloud / PaaS (Railway, Render)

1. Managed PostgreSQL → set `DATABASE_URL`
2. API service from `deploy/Dockerfile.api`
3. Web service from `deploy/Dockerfile.web`, or an nginx container serving the built static files
4. Required env vars:

```env
DATABASE_URL=postgresql+psycopg2://...
SECRET_KEY=<random-32+-chars>
APP_ENV=pilot                   # or production
CORS_ORIGINS=https://your-domain
PUBLIC_APP_URL=https://your-domain
```

5. One-off migrate and seed for a pilot:

```bash
SEED_MODULE=pilot python -m app.docker_migrate
```

6. Optional nightly pilot reset: a cron job calls `POST /api/v1/platform/pilot/reset` (pilot only).

---

## Environment variables (API)

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `SECRET_KEY` | yes | App secret; signs JWT access and refresh tokens |
| `APP_ENV` | yes | `development` \| `pilot` \| `production` |
| `CORS_ORIGINS` | pilot, prod | Comma-separated allowed origins |
| `PUBLIC_APP_URL` | pilot, prod | Canonical app URL (links, emails) |
| `SEED_MODULE` | migrate | `test` (default) or `pilot` (docker_migrate only) |
| `SEED_PASSWORD_SUFFIX` | optional | Suffix for seed-account passwords (default `123`) |
| `SMTP_*` | optional | Outbound email |

Templates: `backend/.env.example`, `backend/.env.pilot.example`, `deploy/dev/.env.example`, `deploy/pilot/.env.example`, `deploy/pilot/.env.supabase.example`, `deploy/production/.env.example`.

---

## Related

- [environments.md](./environments.md): dev, pilot, and production matrix
- [pilot-stack.md](./pilot-stack.md): local pilot stack and tunnel
- [local-development.md](./local-development.md): host development
- [PIPELINE_ARCHITECTURE.md](../phase3-restructure/PIPELINE_ARCHITECTURE.md): CI/CD
