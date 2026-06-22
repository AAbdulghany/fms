# Demo stack (Docker)

Isolated **pitch demo** — database `fms_demo`, seed `pitch_seed`, `APP_ENV=demo`.  
Use for sales demos, E2E tests, and smoke testing the full nginx + API stack.

**Local feature dev** (Vite hot reload): [local-development.md](./local-development.md).

---

## Quick start

From the repository root:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

Wait for:

```text
migrate-1  | Migrate complete.
api-1      | Application startup complete.
```

Open **http://localhost:8080**

| Service | Host port | Role |
|---------|-----------|------|
| web | **8080** | React build + nginx (`/api` → api:8000) |
| api | **8000** | FastAPI (`APP_ENV=demo`) |
| db | 5432 | PostgreSQL `fms_demo` |
| migrate | — | One-shot: Alembic + pitch seed + role migration |

---

## Demo logins

Local demo only — do not reuse in production.

| Email | Password | Role |
|-------|----------|------|
| **super@demo.com** | super123 | super_user — platform, packages, demo reset |
| **swdev@demo.com** | swdev123 | sw_dev — platform support |
| admin@demo.com | admin123 | company_admin |
| client@demo.com | client123 | client_admin (Global Enterprises) |
| client2@demo.com | client223 | client_admin (Riyadh Retail) |
| site@demo.com | site123 | site_manager |
| tech@demo.com | tech123 | technician |

**Pitch seed includes:** 1 maintenance tenant, 2 end clients, 4 assets, 3 work orders, 2 draft invoices.

---

## Everyday commands

```powershell
# Start (after first build)
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up

# Detached
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d

# Stop
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down

# Rebuild after code changes
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build

# Logs
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs -f api
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml logs migrate

# Full reset (wipe DB volume + re-seed)
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down -v
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

---

## Dev stack vs demo stack

| Profile | Command | DB | Seed module |
|---------|---------|-----|-------------|
| **Development** | `docker compose up --build` | `fms` | `test_seed` |
| **Demo** | `docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build` | `fms_demo` | `pitch_seed` |

Dev stack URLs: same ports (**8080** web, **8000** API).

---

## Hybrid: host API + Docker demo DB

When editing Python on the host but Postgres runs in Docker demo:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up -d db
# Stop docker api if port 8000 is needed: docker compose ... stop api

cd backend
copy .env.demo.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend: `npm run dev` at http://localhost:5173 (proxy to :8000).

| Mode | DATABASE_URL DB | API runner |
|------|-----------------|------------|
| Full Docker demo | `fms_demo` (in container) | `api` service |
| Hybrid | `fms_demo` on localhost | host uvicorn |
| Docker dev | `fms` | `api` service |

---

## Reset demo data (no volume wipe)

Log in as **super@demo.com**, then:

```powershell
curl -X POST http://localhost:8000/api/v1/platform/demo/reset `
  -H "Authorization: Bearer <token>"
```

Session token is invalidated; log in again afterward. Returns **403** outside `APP_ENV=demo`.

---

## Migrate pipeline

`migrate` service runs `python -m app.docker_migrate`:

1. Alembic `upgrade head`
2. `schema_ensure` + platform bootstrap
3. Seed: `pitch_seed` (demo) or `test_seed` (dev)
4. `scripts/migrate_roles.py`

---

## Troubleshooting

### `migrate` exit 1 — missing tables

Old images may have seeded before Alembic. Rebuild:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml build migrate
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

### `database "fms" does not exist`

Demo uses **`fms_demo`**. Use current `docker-compose-demo.yml` (healthcheck targets `fms_demo`).

### API — `could not translate host name "db"`

Network race after Ctrl+C. Full cycle:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml down
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

### Blank login / API down

1. `docker compose ... logs api`
2. Confirm migrate finished: `logs migrate`
3. Full reset: `down -v` then `up --build`

### Platform menus missing

Log in as **super@demo.com** (`is_platform_admin`). Tenant company_admin without platform flag won't see platform nav.

### Local uvicorn + demo DB

Copy `backend/.env.demo.example` → `.env` so `DATABASE_URL` ends with `/fms_demo`.

---

## Related

- [deployment.md](./deployment.md) — public demo on a VM
- [testing.md](./testing.md) — Playwright against this stack
- [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md) — `APP_ENV` behavior
