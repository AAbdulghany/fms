# Local development (step by step)

Day-to-day coding: **host API + Vite**, Postgres in Docker.

**Pilot stack** (sales / UAT, full Docker + Cloudflare): [pilot-stack.md](./pilot-stack.md) · [environments.md](./environments.md) · [docker-seed-profiles.md](./docker-seed-profiles.md)

---

## Choose a profile (do not mix)

| Profile | When to use | UI | API | Postgres host port | Database |
|---------|-------------|-----|-----|--------------------|----------|
| **A — Hybrid DEV** (this guide) | Feature work with hot reload | `:5173` Vite | host `:8000` | **9432** | `fms_local` |
| **B — Full Docker DEV** | Run without installing Python/Node API | `:9080` | Docker `:9000` | **9432** | `fms_local` |
| **C — Docker PILOT** | Sales, UAT, E2E, Cloudflare tunnel | `:9081` | Docker `:9001` | **9543** | `fms_pilot` |

**Rule:** `backend/.env` `DATABASE_URL` must match the Postgres you actually started. Wrong port → `connection refused` or `password authentication failed` (often a **native Windows Postgres** on 5432/5433, not Docker).

```powershell
# See who owns a port (PowerShell)
netstat -ano | findstr ":9432"
netstat -ano | findstr ":9543"
netstat -ano | findstr ":5433"
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | current | Postgres (and optional full stack) |
| Python | 3.11+ | Host API |
| Node.js | 18+ | Vite |
| uv | recommended | Python deps from repo root |

---

## Profile A — Hybrid DEV (recommended)

### 1. Start Postgres (+ migrate)

From the **repository root** (not `backend/`):

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
```

Wait until `db` is healthy. Migrate runs once and exits.

| | |
|--|--|
| Host | `localhost:9432` |
| DB | `fms_local` |
| User / password | `fms` / `fms` |

### 2. Backend `.env`

```powershell
copy backend\.env.example backend\.env
```

Must contain:

```env
DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:9432/fms_local
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:9080
```

**Do not** use `.env.pilot.example` for hybrid coding.

### 3. Install & migrate (if needed)

```powershell
uv sync
uv run alembic -c backend/alembic.ini upgrade head
```

### 4. Seed (users only via Docker migrate, or manual)

Docker hybrid migrate already runs `test_seed` (users only). To add a single super user manually:

```powershell
$env:PYTHONPATH = "backend"
uv run python -m app.seed_super
```

### 5. Run API (host)

```powershell
cd backend
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/health | Health |
| http://127.0.0.1:8000/docs | OpenAPI |

### 6. Run frontend

Second terminal, **repo root**:

```powershell
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` → `http://127.0.0.1:8000`.

### 7. Dev logins (after seed)

Password pattern: `{local-part}123` (e.g. `admin123`).

| Email | Role |
|-------|------|
| super@demo.com | super_user |
| admin@demo.com | company_admin |
| tech@demo.com | technician |

Full roster: [docker-seed-profiles.md](./docker-seed-profiles.md).

---

## Profile B — Full Docker DEV

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-local.yml up -d --build
```

Open **http://localhost:9080**. No host uvicorn needed.

---

## Feature flags

Subscription gates (`assets`, `invoices`) are **bypassed** when `APP_ENV=development` or `pilot`. See [environments.md](./environments.md).

---

## Troubleshooting (once and for all)

### `password authentication failed for user "fms"` on 5433

**Cause:** Host traffic hit **native Windows Postgres** (or an old volume), not the Orbit Docker DB. The pilot Docker stack uses **9543**, not 5433.

**Fix for coding:**

```powershell
copy backend\.env.example backend\.env
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
# Restart uvicorn
```

**Fix for pilot host API:**

```powershell
copy backend\.env.pilot.example backend\.env
# DATABASE_URL must use :9543/fms_pilot
docker compose -f docker-compose-pilot.yml up -d
```

### `connection refused` on 9432

Postgres container not running:

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d db
docker compose -f docker-compose-local.yml ps
```

### `open ...\backend\docker-compose-*.yml: not found`

Compose files live in the **repo root**. Always:

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-pilot.yml up -d
```

### `ModuleNotFoundError: app`

```powershell
cd backend
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Preview shows `{}` on login

`npm run preview` needs an API. Use Vite `npm run dev` (proxies to :8000) or Docker UI **http://localhost:9081**.

### Confirm which DB the API uses

```powershell
cd backend
python -c "from app.config import get_settings; print(get_settings().database_url)"
```

---

## Related

- [pilot-stack.md](./pilot-stack.md) — Docker pilot + Cloudflare tunnel
- [environments.md](./environments.md) — dev / pilot / production matrix
- [docker-seed-profiles.md](./docker-seed-profiles.md) — `test_seed` vs `pilot_seed`
- [testing.md](./testing.md) — pytest & Playwright
- `/docker-debug` skill — compose failure tree
