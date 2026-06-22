# Local development

Run the **Orbit** web app and API on your machine with hot reload. Use this for day-to-day feature work.

**Docker pitch demo** (isolated `fms_demo`, full stack): see [demo-stack.md](./demo-stack.md).

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ (CI uses 3.12) | FastAPI backend |
| Node.js | 18+ (CI uses 20) | Vite frontend |
| Docker Desktop | optional | PostgreSQL locally |
| uv | recommended | Python deps from repo root (`pyproject.toml`) |

---

## 1. PostgreSQL

### Option A — DB only (recommended for dev)

Starts Postgres + migrate; you run API and UI on the host:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
```

- Database: `fms_local` on `localhost:9432`
- User / password: `fms` / `fms`

### Option B — DB container only (manual)

```powershell
docker compose -f docker-compose-local.yml up -d db migrate
```

Then run migrate yourself if you skipped it (step 3).

---

## 2. Backend configuration

```powershell
copy backend\.env.example backend\.env
```

Default `DATABASE_URL`:

```text
postgresql+psycopg2://fms:fms@localhost:9432/fms_local
```

For hybrid dev against the **demo** database (`fms_demo` on port `5433`):

```powershell
copy backend\.env.demo.example backend\.env
# Requires: docker compose -f docker-compose-demo.yml up -d
```

---

## 3. Install dependencies & migrate

From the **repository root**:

```powershell
uv sync
uv run alembic -c backend/alembic.ini upgrade head
```

On startup, the API also runs `schema_ensure` (runtime DDL patches alongside Alembic).

---

## 4. Seed data

Pick one:

| Seed | Command | Creates |
|------|---------|---------|
| **Super user only** | `uv run python -m app.seed_super` (with `PYTHONPATH=backend`) | `super@demo.com` / `super123`, tenant shell |
| **Dev dataset** | `cd backend` → `python -m app.seed` | Company admin, technician, sample WOs (skips if tenant exists) |
| **Docker dev stack** | automatic via `docker_migrate` + `test_seed` | Used when running full `docker compose up` |

Minimal super-user seed:

```powershell
$env:PYTHONPATH = "backend"
uv run python -m app.seed_super
```

---

## 5. Run the API

```powershell
cd backend
$env:PYTHONPATH = "."
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000 | API root |
| http://127.0.0.1:8000/docs | OpenAPI (Swagger) |
| http://127.0.0.1:8000/health | Health check |

---

## 6. Run the frontend

Second terminal, **repository root**:

```powershell
npm install
npm run dev
```

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | SPA (Arabic default, EN toggle) |

Vite proxies `/api` → `http://127.0.0.1:8000` (see `vite.config.ts`).

Production build check:

```powershell
npm run build
npm run preview
```

---

## 7. Demo logins (after seed)

Password pattern: `{role-prefix}123` (e.g. admin + 123 → admin123).

| Email | Role | Notes |
|-------|------|-------|
| super@demo.com | super_user / super_admin | Platform admin |
| admin@demo.com | company_admin | Maintenance company |
| client@demo.com | client_admin | End client |
| site@demo.com | site_manager | Site-scoped |
| tech@demo.com | technician | Field work |

Full pitch demo roster: [demo-stack.md](./demo-stack.md).

---

## 8. Feature flags (local)

Subscription feature gates (`assets`, `invoices`) are **bypassed** when `APP_ENV=development` or `demo`. See [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md).

---

## 9. Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: app` | Set `PYTHONPATH=backend` or run from `backend/` with `PYTHONPATH=.` |
| DB connection refused | Ensure Postgres container is healthy; check `DATABASE_URL` |
| `database "fms" does not exist` | Wrong profile — dev uses `fms`, demo uses `fms_demo` |
| Frontend API errors | Confirm API on port **8000** and `npm run dev` is running |
| CORS errors | Add your origin to `CORS_ORIGINS` in `backend/.env` |
| Alembic not found | Use `uv run alembic -c backend/alembic.ini` from repo root |

Docker-specific issues: [demo-stack.md](./demo-stack.md) or `/docker-debug` skill.

---

## Related

- [testing.md](./testing.md) — pytest & Playwright
- [ARCHITECTURE.md](../ARCHITECTURE.md) — system design
- [CLAUDE.md](../../CLAUDE.md) — agent-oriented codebase summary
