---
name: docker-debug
description: >-
  Debug FMS Docker Compose failures — migrate exit 1, DB name mismatch (fms vs
  fms_demo), API hostname "db", local uvicorn vs container API. Use when compose
  errors, migrate fails, or backend cannot connect to Postgres.
disable-model-invocation: false
argument-hint: "[symptom or service name]"
effort: medium
---

# /docker-debug — FMS Docker Compose debugging

Use this skill **before** guessing at fixes when Docker or database connectivity fails.

**Canonical docs:** `docs/phase3-restructure/DEMO_QUICKSTART.md`

## Architecture map (two profiles)

| Profile | Compose command | Postgres DB | Migrate seed | API in Docker |
|---------|-----------------|-------------|--------------|---------------|
| **Development** | `docker compose up` | `fms` | `docker_migrate` → test_seed | port 8000 |
| **Demo** | `docker compose -f docker-compose.yml -f docker-compose.demo.yml up` | `fms_demo` | `docker_migrate` → pitch_seed | port 8000 |

**Critical:** Demo and dev use **different database names** on the same host port `5432`. Mixing them causes `FATAL: database "fms" does not exist` or empty/wrong data.

## Decision tree (read first)

```
Symptom?
├─ migrate exit 1 / audit_logs does not exist
│  └─ Rebuild migrate: uses `python -m app.docker_migrate` (alembic → seed)?
│     ├─ NO → fix compose command + rebuild migrate image
│     └─ YES → check migrate logs for alembic errors
├─ database "fms" does not exist (local uvicorn OR db logs)
│  ├─ Running demo compose? → DB is fms_demo only
│  │  └─ Point DATABASE_URL at fms_demo OR use docker API not local uvicorn
│  └─ Running dev compose? → need `docker compose up` (creates fms)
├─ could not translate host name "db"
│  └─ API started before db on network → `docker compose ... down` then `up`
└─ local uvicorn fails but docker api works
   └─ DATABASE_URL mismatch — see "Local backend + Docker DB" below
```

## Step 1 — Capture evidence

Run from repo root:

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml ps
docker compose -f docker-compose.yml -f docker-compose.demo.yml logs migrate --tail 30
docker compose -f docker-compose.yml -f docker-compose.demo.yml logs api --tail 30
docker exec fms-db-1 psql -U fms -d fms_demo -c "\l"
```

For **local uvicorn** (not in Docker):

```powershell
cd backend
# What DB does the app think it uses?
python -c "from app.config import get_settings; print(get_settings().database_url)"
```

## Step 2 — Known failure patterns

### A. Migrate: `relation "audit_logs" does not exist`

- **Cause:** Seed ran before Alembic (`python -m app.pitch_seed` alone on empty DB).
- **Fix:** Migrate must be `python -m app.docker_migrate`.
- **Verify:** `docker compose ... logs migrate` ends with `Migrate complete.`

### B. `database "fms" does not exist`

| Context | Cause | Fix |
|---------|-------|-----|
| **Local uvicorn** + demo Docker DB | Default URL uses `/fms`; Docker only has `fms_demo` | Copy `backend/.env.demo.example` → `backend/.env` |
| **db container logs** (demo) | Old healthcheck probed `fms` | Use current `docker-compose.demo.yml` (`-d fms_demo`) |
| **Fresh dev** | Never ran dev compose | `docker compose up --build` (creates `fms`) |

### C. API: `could not translate host name "db"`

- **Cause:** Stale `api` container started before `db` joined the network.
- **Fix:**
  ```powershell
  docker compose -f docker-compose.yml -f docker-compose.demo.yml down
  docker compose -f docker-compose.yml -f docker-compose.demo.yml up
  ```
- **Prevention:** `api` depends_on `db` (healthy) + `migrate` (completed).

### D. Local uvicorn vs Docker API (port conflict)

- Docker API binds `localhost:8000`.
- Local `uvicorn` also wants `8000`.
- **Pick one:**
  1. **Docker only** — use http://localhost:8080 (web) or :8000 (api); stop local uvicorn.
  2. **Local API + Docker DB only** — stop `fms-api-1`, set `.env` to `fms_demo`, run uvicorn on 8000.
  3. **Local API on alt port** — `uvicorn ... --port 8001` and point Vite proxy accordingly.

## Step 3 — Local backend + Docker demo DB

When developing the API on the host against the demo database:

```powershell
cd backend
copy .env.demo.example .env
python -m alembic upgrade head   # only if tables missing
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Required `.env` values:

```env
DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:5432/fms_demo
APP_ENV=demo
```

**Do not** use `/fms` in the URL while demo compose is running unless you also start the dev stack.

## Step 4 — Nuclear reset

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml down -v
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

Wait for `Migrate complete.` and `Application startup complete.`

## Step 5 — Verify end-to-end

```powershell
curl http://localhost:8000/health
# Login (demo)
curl -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"identifier\":\"super@demo.com\",\"password\":\"super123\"}"
```

## Agent checklist (do not skip)

1. Identify profile: **dev** (`fms`) vs **demo** (`fms_demo`).
2. Check whether user runs **local uvicorn** or **Docker API** — different `DATABASE_URL` host (`localhost` vs `db`).
3. Read migrate logs before editing seed scripts.
4. After compose file changes, **`build migrate`** (cached images hide fixes).
5. Document fix in `DEMO_QUICKSTART.md` if new pattern discovered.

## Demo logins (pitch seed)

| Email | Password |
|-------|----------|
| super@demo.com | super123 |
| admin@demo.com | admin123 |

Full table: `docs/phase3-restructure/DEMO_QUICKSTART.md`
