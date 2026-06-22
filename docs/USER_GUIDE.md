# FMS User Guide — Local setup and seeding

> **Superseded by:** [guides/local-development.md](./guides/local-development.md)  
> Content below is retained for reference; prefer the guide for up-to-date commands.

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| **Python** 3.11+ | API |
| **Node.js** 18+ | Web UI |
| **Docker Desktop** (recommended) | PostgreSQL locally |
| **uv** (recommended) | Install Python deps from the repo root |

Install **uv**: see [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/).

---

## 1. Start PostgreSQL

From the **repository root**:

```powershell
docker compose -f docker-compose.yml up -d
```

Default database (matches `backend/.env.example` when present):

- Host: `localhost:5432`
- User / password / database: `fms` / `fms` / `fms`

If you do not use Docker, create a PostgreSQL database and user that match your `DATABASE_URL`.

---

## 2. Backend configuration

From the **repository root**, copy env defaults if you do not have them yet:

```powershell
copy backend\.env.example backend\.env
```

Ensure `DATABASE_URL` points at your database, for example:

`postgresql+psycopg2://fms:fms@localhost:5432/fms`

---

## 3. Install Python dependencies (uv)

From the **repository root** (recommended):

```powershell
uv sync
```

This reads `pyproject.toml` and `uv.lock` and installs into the project `.venv`.

---

## 4. Apply database migrations

Alembic configuration is `backend/alembic.ini` (scripts under `backend/migrations`).  
Milestone 4 adds locations, labor, and dashboard tables (`9a2b3c4d5e6f_milestone4_locations_labor_dashboard`); always run `upgrade head` after pulling.

**From the repository root:**

```powershell
uv run alembic -c backend/alembic.ini upgrade head
```

**Or from the `backend` folder** (paths in `alembic.ini` are relative to that directory):

```powershell
cd backend
uv run alembic -c alembic.ini upgrade head
```

If `alembic` is not found, use the venv executable from the repo root:

```powershell
.venv\Scripts\alembic.exe -c backend\alembic.ini upgrade head
```

---

## 5. Seed **only** a super user (minimal)

Use this when you want a single **super_admin** account and no demo clients, sites, or work orders.

From the **repository root**, with `cwd` including `backend` on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "backend"
uv run python -m app.seed_super
```

Or from the **`backend`** folder:

```powershell
cd backend
$env:PYTHONPATH = "."
uv run python -m app.seed_super
```

**Default credentials** (change after first login in production):

| Field | Value |
|--------|--------|
| Email | `super@demo.com` |
| Password | `super123` |

**Behavior:**

- Creates the tenant **Demo Facility Co** if it does not exist.
- Creates **one** user with role **super_admin** and **platform admin** flag.
- If `super@demo.com` already exists, the script prints a message and **does not** duplicate the user.

---

## 6. Full demo seed (optional)

The standard development seed creates a richer dataset (company admin, technician, clients, sample work orders). It is **skipped** if the demo tenant already exists.

From the **`backend`** folder:

```powershell
cd backend
$env:PYTHONPATH = "."
uv run python -m app.seed
```

See printed credentials after a successful run (e.g. `admin@demo.com` / `admin123`).

**Note:** If you only need a super user, prefer **`seed_super`** (section 5). Do not rely on `app.seed` to create a super user; it creates **company_admin** and **technician** by default.

---

## 7. Run the API

From the **`backend`** folder:

```powershell
cd backend
$env:PYTHONPATH = "."
uv run python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- OpenAPI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

---

## 8. Run the frontend

In a **second** terminal, from the **repository root**:

```powershell
npm install
npm run dev
```

- App: `http://localhost:5173`
- The Vite dev server proxies `/api` to the backend (default `http://127.0.0.1:8000`).

Production build (optional):

```powershell
npm run build
npm run preview
```

---

## 9. Run tests (backend)

From the **repository root**:

```powershell
uv run pytest backend/tests/ -q
```

---

## 10. Troubleshooting

| Issue | What to try |
|--------|-------------|
| `ModuleNotFoundError: No module named 'app'` | Set `PYTHONPATH` to `backend` (see sections 5–7). |
| Database connection errors | Confirm Postgres is up and `DATABASE_URL` in `backend/.env` is correct. |
| `alembic` not found | Use `uv run alembic` or `.venv\Scripts\alembic.exe` from the repo root. |
| Super user already exists | Normal after the first successful `seed_super`; log in with `super@demo.com`. |

---

## Related documentation

- **Canonical runbooks:** [docs/guides/local-development.md](./guides/local-development.md)
- Original runbook (redirect): [HOW_TO_RUN.md](./HOW_TO_RUN.md)
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
