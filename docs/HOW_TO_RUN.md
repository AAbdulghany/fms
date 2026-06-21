# How to run Orbit (local development)

**For the up-to-date runbook** (uv, migrations, super-user-only seed), see **[USER_GUIDE.md](./USER_GUIDE.md)**.

---

## Prerequisites

- **Node.js** 18+ (for the web app)
- **Python** 3.11+ (for the API)
- **Docker Desktop** (optional but recommended for PostgreSQL)

---

## 1. Start PostgreSQL

From the repository root:

```powershell
docker compose -f docker-compose.yml up -d
```

This starts Postgres **16** on port **5432** with:

- User: `fms`
- Password: `fms`
- Database: `fms`

If Docker is not available, install PostgreSQL yourself and create a database + user that match `DATABASE_URL` in `backend/.env`.

---

## 2. Backend (FastAPI)

```powershell
cd backend
python -m pip install -r requirements.txt
```

Optional: copy environment defaults and adjust if needed:

```powershell
copy .env.example .env
```

Default `DATABASE_URL` matches the bundled `docker-compose.yml`:

`postgresql+psycopg2://fms:fms@localhost:5432/fms`

**Create tables and demo data** (safe to run once; it skips if the demo tenant already exists):

```powershell
python -m app.seed
```

**Run the API** (with auto-reload):

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API base: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

---

## 3. Frontend (Vite + React)

In a **second** terminal, from the repository root:

```powershell
npm install
npm run dev
```

- App: `http://localhost:5173`
- The dev server **proxies** `/api` to `http://127.0.0.1:8000`, so the UI talks to `/api/v1/...` without extra CORS setup.

**Production build** (optional):

```powershell
npm run build
npm run preview
```

---

## 4. Demo logins (after `python -m app.seed`)

| Role           | Email            | Password   |
|----------------|------------------|------------|
| Company admin  | `admin@demo.com` | `admin123` |
| Technician     | `tech@demo.com`  | `tech123`  |

---

## 5. Quick billing smoke test

1. Log in as **technician**, open the sample work order, fill the report (checklist, labor hours, parts JSON), **Save**, then **Submit**.
2. Log in as **admin**, open the same work order, **Approve** the report.
3. Transition the work order: **completed** → **verified** (use the status controls on the detail page).
4. Click **Generate invoice** (allowed when the report is approved and the work order is **verified** or **closed**).

---

## 6. Troubleshooting

| Issue | What to try |
|-------|-------------|
| `failed to connect to ... docker` | Start **Docker Desktop**, then run `docker compose up -d` again. |
| DB connection refused | Ensure Postgres is listening on `localhost:5432` and credentials match `DATABASE_URL`. |
| `Seed already applied` | Normal if you ran `app.seed` before; data is already there. |
| Frontend API errors | Confirm the backend is on port **8000** and `npm run dev` is using the default Vite proxy. |
| CORS errors when not using Vite proxy | Set `CORS_ORIGINS` in `backend/.env` to include your frontend origin (e.g. `http://localhost:5173`). |

---

## 7. Related docs

- Architecture and design: [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)
