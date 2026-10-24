# Local development (step by step)

Day-to-day coding: **host API + Vite**, Postgres in Docker.

**Pilot stack** (sales / UAT, full Docker + Cloudflare): [pilot-stack.md](./pilot-stack.md) · [environments.md](./environments.md) · [docker-seed-profiles.md](./docker-seed-profiles.md)

**Program A clean data:** prefer `clean_dev_seed` (1 tenant · 1 hospital client · all roles) — see §4 below and [PROGRAM_A_COMPLETION_REPORT.md](../redesign/PROGRAM_A_COMPLETION_REPORT.md).

---

## Choose a profile (do not mix)

| Profile | When to use | UI | API | Postgres host port | Database |
|---------|-------------|-----|-----|--------------------|----------|
| **A — Hybrid DEV** (this guide) | Feature work with hot reload | `:5173` Vite | host `:8000` (or `:8001` if 8000 is stuck) | **9432** | `fms_local` |
| **B — Full Docker DEV** | Run without installing Python/Node API | `:9080` | Docker `:9000` | **9432** | `fms_local` |
| **C — Docker PILOT** | Sales, UAT, E2E, Cloudflare tunnel | `:9081` | Docker `:9001` | **9543** | `fms_pilot` |

**Rule:** `backend/.env` `DATABASE_URL` must match the Postgres you actually started. Wrong port → `connection refused` or `password authentication failed` (often a **native Windows Postgres** on 5432/5433, not Docker).

```powershell
# See who owns a port (PowerShell)
netstat -ano | findstr ":9432"
netstat -ano | findstr ":8000"
netstat -ano | findstr ":5173"
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker Desktop | current | Postgres (and optional full stack) |
| Python | 3.11+ | Host API (repo `.venv` OK) |
| Node.js | 18+ | Vite |
| uv | recommended | Python deps from repo root |

---

## Profile A — Hybrid DEV (recommended)

### 1. Start Postgres (+ migrate)

From the **repository root** (not `backend/`):

```powershell
cd E:\03Workset\fms
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
# Required so printed QR matches the in-app preview (absolute /a/{token} URL)
PUBLIC_APP_URL=http://127.0.0.1:5173
```

**Do not** use `.env.pilot.example` for hybrid coding. Without `PUBLIC_APP_URL`, the label API falls back to the browser `Origin` header so preview and print still match.

### 3. Install & migrate

```powershell
# From repo root (uv) — or use .venv
uv sync
uv run alembic -c backend/alembic.ini upgrade head

# Equivalent with repo venv:
cd backend
..\.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```

Current head includes A2 asset tags + A3 tax profiles / WO parts + bilingual parts columns (`f7a8b9c0d1e2`).

### 4. Seed (pick one)

| Seed | Command | What you get |
|------|---------|----------------|
| **Clean DEV (recommended for A1–A4)** | see below | 1 tenant, **Cairo General Hospital**, 1 site, all roles, hospital asset types, sample EN/AR parts, TaxProfile 15% |
| `test_seed` (CI / users only) | Docker hybrid migrate default | Users only — no clients/assets |
| `pilot_seed` | Pilot compose | Rich demo dataset on `fms_pilot` |

**Wipe + clean hospital seed** (idempotent truncate of tenant tables):

```powershell
cd E:\03Workset\fms\backend
$env:PYTHONPATH = "."
# With uv from repo root:
#   uv run python -m app.cli.clean_dev_seed
..\.\.venv\Scripts\python.exe -m app.cli.clean_dev_seed
```

Password pattern: `{local-part}123` (controlled by `SEED_PASSWORD_SUFFIX`, default `123`).

| Email | Role |
|-------|------|
| super@demo.com | super_user |
| swdev@demo.com | sw_dev |
| **admin@demo.com** | **company_admin** |
| engineer@demo.com | company_engineer |
| manager@demo.com | manager |
| client@demo.com | client_admin (bound to hospital) |
| site@demo.com | site_manager |
| tech@demo.com | technician |

Client: **Cairo General Hospital** (`hospital` vertical) · Site: **Main Campus**.

Full roster notes: [docker-seed-profiles.md](./docker-seed-profiles.md). Program A status: [PROGRAM_A_COMPLETION_REPORT.md](../redesign/PROGRAM_A_COMPLETION_REPORT.md).

### 5. Run API (host)

```powershell
cd E:\03Workset\fms\backend
$env:PYTHONPATH = "."
..\.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/health | Health |
| http://127.0.0.1:8000/docs | OpenAPI |

**Windows stuck `:8000`:** if `netstat` shows LISTEN but no real process (ghost PID), start on **8001** and point Vite’s proxy at it (see §6).

```powershell
..\.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### 6. Run frontend

Second terminal, **repo root**:

```powershell
cd E:\03Workset\fms
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open **http://127.0.0.1:5173** — Vite proxies `/api` via `vite.config.ts` (`server.proxy["/api"].target`).

Default in repo is `http://127.0.0.1:8000`. On machines where `:8000` is a stuck ghost listener, set the target to `http://127.0.0.1:8001` to match the API port you started.

#### Useful UI routes (Program A)

| Path | Purpose |
|------|---------|
| `/billing/parts` | Parts catalog (EN/AR + bulk CSV) |
| `/billing/tax` | TaxProfile (VAT %) |
| `/billing/pricing` | Pricing profiles |
| `/billing/contracts` | Contracts |
| `/asset-types` | Tenant library + catalog adopt |
| `/assets` · WO detail | Register (vertical-filtered types) · Parts used panel |
| `/a/:token` | Public asset QR landing |

---

## Profile B — Full Docker DEV

```powershell
cd E:\03Workset\fms
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

### Ghost listener on `:8000` (Windows)

`netstat` shows LISTEN / PID that `Get-Process` cannot find. Use API on **8001** + Vite proxy to 8001, or reboot.

### `open ...\backend\docker-compose-*.yml: not found`

Compose files live in the **repo root**. Always:

```powershell
cd E:\03Workset\fms
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
- [docker-seed-profiles.md](./docker-seed-profiles.md) — `test_seed` vs `pilot_seed` vs clean DEV
- [redesign/PROGRAM_A_COMPLETION_REPORT.md](../redesign/PROGRAM_A_COMPLETION_REPORT.md) — A1–A4 done vs missing
- [testing.md](./testing.md) — pytest & Playwright
- `/docker-debug` skill — compose failure tree
