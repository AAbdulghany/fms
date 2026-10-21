# Demo Quickstart — Docker commands & logins

> **Canonical guide:** [guides/demo-stack.md](../guides/demo-stack.md)  
> This file is kept for wave-doc cross-links; prefer the guide above.

**Keep this file.** Single reference for running the pitch demo locally.

| Item | Value |
|------|-------|
| App URL | http://localhost:8080 |
| API (direct) | http://localhost:8000 |
| Database | `fms_demo` on port 5432 |
| Compose files | `docker-compose-local.yml` + `docker-compose-demo.yml` |

---

## First-time start (recommended)

From the repo root (`FMS/`):

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

Wait until you see:

```text
migrate-1  | Migrate complete.
api-1      | Application startup complete.
```

Then open http://localhost:8080

---

## Demo logins

All passwords are for **local demo only**.

| Email | Password | Role | Notes |
|-------|----------|------|-------|
| **super@demo.com** | `super123` | super_user | Platform super user — maintenance companies, packages, licenses, demo reset |
| **swdev@demo.com** | `swdev123` | sw_dev | Platform support/dev — same platform access except cannot remove members |
| admin@demo.com | `admin123` | company_admin | Maintenance company admin |
| client@demo.com | `client123` | client_admin | Global Enterprises Ltd |
| client2@demo.com | `client223` | client_admin | Riyadh Retail Group |
| site@demo.com | `site123` | site_manager | Scoped to first site |
| tech@demo.com | `tech123` | technician | Field technician |

**Pitch seed includes:** 1 maintenance tenant, 2 end clients, 4 assets, 3 work orders, 2 draft invoices.

---

## Everyday commands

### Start (after first build)

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up
```

### Start detached (background)

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d
```

### Stop

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down
```

### Rebuild after code changes

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

### View logs

```powershell
# All services
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs -f

# Migrate only
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs migrate

# API only
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs api
```

### Full reset (wipe DB volume + re-seed)

Use when migrate/schema is stuck or you want a clean pitch database:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down -v
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

---

## Development stack (not demo)

Standard dev database `fms` with `test_seed`:

```powershell
docker compose up --build
```

Logins: `admin@demo.com` / `admin123`, `client@demo.com` / `client123` (see `docs/phase3.1/DEMO_DEPLOY.md`).

---

## Local uvicorn + Docker demo DB (hybrid dev)

Use when editing Python on the host but Postgres runs in Docker demo.

**Your error if misconfigured:** `FATAL: database "fms" does not exist` — local app points at `fms` but Docker only created `fms_demo`.

```powershell
# 1. Start demo DB (and optionally web); stop docker API if you want port 8000 locally
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d db
# optional: docker compose -f docker-compose-local.yml -f docker-compose-demo.yml stop api

# 2. Point backend at fms_demo
cd backend
copy .env.demo.example .env

# 3. Run API on host
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the **Docker API** at http://localhost:8000 and skip local uvicorn entirely.

| Mode | DATABASE_URL database | Who runs API |
|------|----------------------|--------------|
| Full Docker demo | (inside container) `fms_demo` | `fms-api-1` |
| Local uvicorn + Docker demo DB | `fms_demo` on `localhost` | your terminal |
| Dev compose | `fms` | `fms-api-1` or local with `.env` → `/fms` |

Agent skill for debugging: `.claude/skills/docker-debug/SKILL.md` (`/docker-debug`).

---

## Reset demo data without wiping volume

Log in as **super@demo.com**, then call (replace `<token>`):

```powershell
curl -X POST http://localhost:8000/api/v1/platform/demo/reset `
  -H "Authorization: Bearer <token>"
```

Your session token is invalidated after reset; log in again as `super@demo.com`.

---

## Troubleshooting

### `migrate` exit 1 — `relation "audit_logs" does not exist`

**Cause:** Old image ran `python -m app.pitch_seed` before Alembic created tables.

**Fix:**

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml build migrate
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

Migrate must run `python -m app.docker_migrate` (schema → seed).

---

### `database "fms" does not exist` in db logs (demo mode)

**Cause:** Postgres healthcheck probed default DB `fms` while demo uses `fms_demo`.

**Fix:** Use current `docker-compose-demo.yml` (healthcheck uses `-d fms_demo`). Harmless if migrate already succeeded.

---

### API — `could not translate host name "db"`

**Cause:** API container started before the `db` service was on the Docker network (common after `Ctrl+C` then `up` without full down).

**Fix:**

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up
```

API now waits for `db` healthy + `migrate` complete. If it still fails, `docker compose ... up --build`.

---

### API exits immediately / blank login page

1. Check API: `docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs api`
2. Confirm migrate finished: `docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs migrate`
3. Full reset: `down -v` then `up --build`

---

### Platform menus missing (packages / subscription)

Log in as **super@demo.com** (`super_user`, `is_platform_admin`). Tenant `company_admin` without platform flag will not see platform nav.

---

### Local uvicorn: `database "fms" does not exist`

**Cause:** Demo Docker created `fms_demo` only; `backend/.env` or defaults still use `/fms`.

**Fix:**

```powershell
cd backend
copy .env.demo.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or stop local uvicorn and use Docker API at http://localhost:8000.

---

## Service map

| Service | Port | Role |
|---------|------|------|
| web | 8080 | React UI + nginx API proxy |
| api | 8000 | FastAPI (`APP_ENV=demo`) |
| db | 5432 | PostgreSQL `fms_demo` |
| migrate | — | One-shot: Alembic + pitch seed |

---

## Related docs

- **Canonical guide:** [guides/demo-stack.md](../guides/demo-stack.md)
- [guides/deployment.md](../guides/deployment.md) — Railway / hosting
- [ENV_MATRIX.md](ENV_MATRIX.md) — `APP_ENV` behavior
- [WAVE1_WAVE2_SIGNOFF.md](WAVE1_WAVE2_SIGNOFF.md) — delivery sign-off
