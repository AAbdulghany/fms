# Supabase + Cloudflare demo runbook (fill-in)

Use **Supabase as managed Postgres** only. Run API + web yourself (PC or VPS). Put **Cloudflare Tunnel** in front for **https://demo.orbittech.co**.

Do **not** use Supabase Auth / Realtime for Orbit — the FastAPI app already owns login.

Replace every `«…»` placeholder as you go. Leave values empty until you have them.

---

## 0 — Worksheet (fill later)

| # | Item | Your value |
|---|------|------------|
| W1 | GitHub org/user + repo URL | `https://github.com/AAbdulghany/fms.git` |
| W2 | Branch for demo | `demo/live` *(exists on origin — Phase 0 done)* |
| W3 | Supabase project name | `«SUPABASE_PROJECT_NAME»` |
| W4 | Supabase region | `«SUPABASE_REGION»` |
| W5 | Supabase DB password | `«SUPABASE_DB_PASSWORD»` *(store in a password manager)* |
| W6 | Supabase project ref | `ggunaisqcerahtnldpcn` *(from `.cursor/mcp.json` — confirm in dashboard)* |
| W7 | Database URI from dashboard (raw) | `«SUPABASE_DATABASE_URI_RAW»` |
| W8 | Orbit `DATABASE_URL` (psycopg2) | `«DATABASE_URL»` |
| W9 | App `SECRET_KEY` (32+ bytes hex) | `«SECRET_KEY»` |
| W10 | Public demo URL | `https://demo.orbittech.co` |
| W11 | CORS origin (same as public URL) | `https://demo.orbittech.co` |
| W12 | Where API+web run | `pc` *(recommended until VPS is free/ready)* |
| W13 | Local web port (PC compose) | `9581` (API `9501`; avoid Windows reserved 9015–9383) |
| W14 | Cloudflare account email | `«CLOUDFLARE_ACCOUNT_EMAIL»` |
| W15 | Cloudflare zone | `orbittech.co` |
| W16 | Tunnel name | `orbit-demo` |
| W17 | Tunnel service URL | `http://localhost:9081` |
| W18 | (Optional) VPS SSH host | `«DEMO_HOST»` |
| W19 | (Optional) VPS SSH user | `«DEMO_USER»` |
| W20 | (Optional) Path to SSH private key | `«SSH_KEY_PATH»` |

### Automated compose (repo)

```powershell
# After filling deploy/demo/.env.supabase-demo from the example:
docker compose -f docker-compose-supabase-demo.yml --env-file deploy/demo/.env.supabase-demo up -d --build
```

Files: [`docker-compose-supabase-demo.yml`](../../docker-compose-supabase-demo.yml), [`deploy/demo/.env.supabase-demo.example`](../../deploy/demo/.env.supabase-demo.example)

Generate secrets when ready:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 1 — Prepare the repo branch

- [ ] 1.1 Local smoke (optional): pytest, `npm run build`, demo compose if Docker is up.
- [ ] 1.2 Ensure branch exists and is pushed:

```powershell
cd E:\03Workset\fms
git checkout -b demo/live   # skip if branch already exists
git push -u origin demo/live
```

**Fill:** `«GITHUB_REPO_URL»` = _________________________________

---

## 2 — Create Supabase project

- [ ] 2.1 Open https://supabase.com → sign in → **New project**.
- [ ] 2.2 Set:

| Field | Value |
|-------|--------|
| Name | `«SUPABASE_PROJECT_NAME»` |
| Database password | `«SUPABASE_DB_PASSWORD»` |
| Region | `«SUPABASE_REGION»` |

- [ ] 2.3 Wait until project is **Healthy**.
- [ ] 2.4 **Settings → General** → copy **Reference ID** → `«SUPABASE_PROJECT_REF»`.
- [ ] 2.5 **Settings → Database → Connection string → URI**:
  - Prefer **Transaction** pooler (port **6543**) for the running API.
  - Keep a **Session** / direct (port **5432**) URI handy if Alembic fails on the pooler.

**Fill:**

- Raw URI: `«SUPABASE_DATABASE_URI_RAW»` = _________________________________
- Convert for Orbit (add `+psycopg2` after `postgresql`):

```text
postgresql://...     →  postgresql+psycopg2://...
postgres://...       →  postgresql+psycopg2://...
```

- URL-encode special characters in the password (`@` → `%40`, `#` → `%23`, etc.).
- Final: `«DATABASE_URL»` = _________________________________

---

## 3 — Create local env file (API host)

Do **not** commit this file.

### 3.1 Backend env (migrate + API on host, or for reference)

```powershell
cd E:\03Workset\fms\backend
copy .env.demo.example .env
notepad .env
```

Set at least:

```env
DATABASE_URL=«DATABASE_URL»
SECRET_KEY=«SECRET_KEY»
APP_ENV=demo
CORS_ORIGINS=https://demo.orbittech.co
PUBLIC_APP_URL=https://demo.orbittech.co
```

### 3.2 Optional: root / compose env for Docker API+web without local Postgres

Create `E:\03Workset\fms\.env.supabase-demo` (gitignored if you add the name; otherwise keep outside repo):

```env
DATABASE_URL=«DATABASE_URL»
SECRET_KEY=«SECRET_KEY»
APP_ENV=demo
CORS_ORIGINS=https://demo.orbittech.co
PUBLIC_APP_URL=https://demo.orbittech.co
SEED_MODULE=pitch
```

---

## 4 — Schema + pitch seed on Supabase

Run from a machine that can reach Supabase (your PC). Docker Desktop must be running **only if** you use the migrate container; host Python works too.

### Option A — Host Python (simple)

```powershell
cd E:\03Workset\fms\backend
# Ensure venv active and deps installed
$env:DATABASE_URL = "«DATABASE_URL»"
$env:SECRET_KEY = "«SECRET_KEY»"
$env:APP_ENV = "demo"
$env:SEED_MODULE = "pitch"

alembic upgrade head
python -m app.pitch_seed
```

If `pitch_seed` is only invoked via `docker_migrate`, use:

```powershell
python -m app.docker_migrate
```

(with `SEED_MODULE=pitch` and `APP_ENV=demo` set).

### Option B — One-off migrate container

```powershell
cd E:\03Workset\fms
docker build -f deploy/Dockerfile.api -t fms-api:demo .
docker run --rm `
  -e DATABASE_URL="«DATABASE_URL»" `
  -e SECRET_KEY="«SECRET_KEY»" `
  -e APP_ENV=demo `
  -e SEED_MODULE=pitch `
  fms-api:demo `
  python -m app.docker_migrate
```

- [ ] 4.1 Confirm in Supabase **Table Editor** that tables exist and users were seeded (e.g. `users` / app tables).

**Demo logins (after seed):**

| Email | Password |
|-------|----------|
| super@demo.com | super123 |
| admin@demo.com | admin123 |
| client@demo.com | client123 |

---

## 5 — Run API + web (no local Postgres)

You only need **api** + **web**. Point both at Supabase via `DATABASE_URL`.

### Option A — PC: Docker API + web, DB = Supabase

Minimal approach: run api/web containers with env overrides (adjust compose service names to match your files).

```powershell
cd E:\03Workset\fms

# Build images
docker build -f deploy/Dockerfile.api -t fms-api:demo .
docker build -f deploy/Dockerfile.web -t fms-web:demo .

# API (publish 9001 like demo stack)
docker run -d --name fms-demo-api `
  -p 9001:8000 `
  -e DATABASE_URL="«DATABASE_URL»" `
  -e SECRET_KEY="«SECRET_KEY»" `
  -e APP_ENV=demo `
  -e CORS_ORIGINS="https://demo.orbittech.co" `
  -e PUBLIC_APP_URL="https://demo.orbittech.co" `
  fms-api:demo

# Web/nginx — needs to reach API. On Docker Desktop, host.docker.internal often works:
# If your nginx.conf proxies to hostname "api", use a user-defined network instead (recommended).
```

**Recommended:** create a small network and run both with the existing nginx expecting `api:8000`:

```powershell
docker network create fms-supabase-demo
docker run -d --name fms-demo-api --network fms-supabase-demo `
  -e DATABASE_URL="«DATABASE_URL»" `
  -e SECRET_KEY="«SECRET_KEY»" `
  -e APP_ENV=demo `
  -e CORS_ORIGINS="https://demo.orbittech.co" `
  -e PUBLIC_APP_URL="https://demo.orbittech.co" `
  fms-api:demo

docker run -d --name fms-demo-web --network fms-supabase-demo `
  -p 9081:8080 `
  fms-web:demo
```

- [ ] 5.1 Health: `curl http://127.0.0.1:9001/health` or via nginx `curl http://127.0.0.1:9081/api/v1/health`
- [ ] 5.2 Browser: http://127.0.0.1:9081 → login with demo users

### Option B — PC: hybrid (uvicorn + Vite) against Supabase

```powershell
# Terminal 1
cd E:\03Workset\fms\backend
# .env already has DATABASE_URL=«DATABASE_URL»
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd E:\03Workset\fms
npm run dev
```

Vite must proxy `/api` to `:8000` (existing Vite config). Tunnel must target the **same origin users open** (usually the Vite URL or a local nginx). Prefer Option A for same-origin `/api` like production.

### Option C — Later: VPS

Same as Option A on the server; set `WEB_PORT=8080` and tunnel to `http://localhost:8080`. Fill `«DEMO_HOST»`, `«DEMO_USER»`, `«SSH_KEY_PATH»`.

---

## 6 — Cloudflare Tunnel → demo.orbittech.co

- [ ] 6.1 Log in: https://one.dash.cloudflare.com/ (`«CLOUDFLARE_ACCOUNT_EMAIL»`)
- [ ] 6.2 **Networks → Tunnels → Create** → name `orbit-demo` → Cloudflared
- [ ] 6.3 Install connector on the **same machine** that runs web (PC or VPS) — paste Cloudflare’s Linux/Windows install command
- [ ] 6.4 Public hostname:

| Field | Value |
|-------|--------|
| Subdomain | `demo` |
| Domain | `orbittech.co` |
| Service | `«TUNNEL_SERVICE_URL»` e.g. `http://localhost:9081` |

- [ ] 6.5 Save (DNS CNAME for `demo.orbittech.co` is created automatically)
- [ ] 6.6 Verify:

```powershell
curl -fsS https://demo.orbittech.co/api/v1/health
```

Browser: https://demo.orbittech.co → login.

**Fill:** Tunnel token / install command stored at: `«CLOUDFLARE_TUNNEL_INSTALL_NOTE»` = _________________________________

---

## 7 — Align app URLs with the public hostname

If you started API before the tunnel existed, restart API with:

```env
PUBLIC_APP_URL=https://demo.orbittech.co
CORS_ORIGINS=https://demo.orbittech.co
```

- [ ] 7.1 Login works on the **public** URL (not only localhost)
- [ ] 7.2 Arabic toggle / navigation smoke-test

---

## 8 — (Optional) GitHub Actions CD

Only if API+web run on a **VPS** with SSH (not required for PC+tunnel).

Repo → **Settings → Secrets and variables → Actions**:

| Name | Kind | Value |
|------|------|--------|
| `DEMO_HOST` | secret | `«DEMO_HOST»` |
| `DEMO_USER` | secret | `«DEMO_USER»` |
| `DEMO_SSH_PRIVATE_KEY` | secret | contents of `«SSH_KEY_PATH»` |
| `DEMO_PATH` | secret | e.g. `/opt/fms` |
| `DEMO_URL` | variable | `https://demo.orbittech.co` |

Workflow: [`.github/workflows/deploy-orbit-demo.yml`](../../.github/workflows/deploy-orbit-demo.yml).

**Note:** That workflow currently assumes Docker Compose + local `deploy/demo/.env` on the VM. If the VM uses **Supabase**, put `DATABASE_URL=«DATABASE_URL»` in the server env / compose override and **do not** start a local `db` container. Adjust the remote compose command when you move off all-in-one Docker DB.

---

## 9 — Production later (same Supabase project or a new one)

When leaving “demo”:

- [ ] New Supabase project (or paid plan) — don’t reuse pitch seed passwords
- [ ] `APP_ENV=production`
- [ ] `alembic upgrade head` only — **no** `pitch_seed`; use minimal super-user seed and change password
- [ ] Strong `SECRET_KEY`
- [ ] Always-on API host (not laptop)
- [ ] Cloudflare DNS/proxy to real servers (tunnel optional)
- [ ] Backups enabled on Supabase
- [ ] Disable demo reset endpoint usage

---

## 10 — Troubleshooting

| Symptom | Check |
|---------|--------|
| `password authentication failed` | Password URL-encoded? Correct pooler user (`postgres.«SUPABASE_PROJECT_REF»`)? |
| Alembic / migration errors on pooler | Retry with **direct** port 5432 URI |
| CORS / login fails on public URL | `CORS_ORIGINS` and `PUBLIC_APP_URL` exactly `https://demo.orbittech.co` |
| Tunnel 502 | Web container up? Service URL port matches (`9081` vs `8080`)? |
| Empty DB | Re-run migrate + `SEED_MODULE=pitch` |
| Supabase paused (free) | Open Supabase dashboard to wake project |

---

## Quick order

1. Worksheet §0  
2. Branch §1  
3. Supabase §2 → `«DATABASE_URL»`  
4. Env §3  
5. Migrate + seed §4  
6. API + web §5  
7. Tunnel §6–7  
8. Optional CI §8  

**Related:** [deployment.md](./deployment.md) · [demo-stack.md](./demo-stack.md) · [DEMO_LIVE_DEPLOY.md](../phase3-restructure/DEMO_LIVE_DEPLOY.md)
