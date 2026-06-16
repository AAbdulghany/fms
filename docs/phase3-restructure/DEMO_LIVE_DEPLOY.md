# Demo live deployment — step-by-step (free tier)

Deploy the **pitch demo** so external users can try FMS without installing Docker locally.

| Goal | Value |
|------|--------|
| Branch | `demo/live` (see [deploy/demo/BRANCH_MANIFEST.md](../../deploy/demo/BRANCH_MANIFEST.md)) |
| Profile | `APP_ENV=demo`, database `fms_demo`, seed `pitch_seed` |
| Stack | PostgreSQL + FastAPI + Nginx/React (same as local demo) |

**Local reference:** [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md)

---

## Phase 0 — Prepare the branch (one time)

### Step 0.1 Commit demo-ready work

Ensure these pass locally before cutting `demo/live`:

```powershell
cd backend
python -m pytest -q

cd ..
npm run build

docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
# Open http://localhost:8080 — smoke-test super + client logins
```

### Step 0.2 Create and push `demo/live`

```powershell
git checkout -b demo/live
git push -u origin demo/live
git tag demo-live-v1.0.0
git push origin demo-live-v1.0.0
```

Only merge **demo-stable** changes into `demo/live`. Keep feature development on `feature/phase3` (or `dev`).

---

## Phase 1 — Choose hosting (free options)

| Option | Cost | Best for | Caveat |
|--------|------|----------|--------|
| **A. Oracle Cloud Always Free VM** | $0 | Full Docker Compose (recommended) | Account verification; 1–4 OCPU ARM VM |
| **B. Render** | $0 tier | Managed Postgres + 2 web services | Free DB expires / spins down; split services |
| **C. Fly.io** | Free allowance | Single Dockerfile + Fly Postgres | Credit limits; more manual |
| **D. Your home / office PC + Cloudflare Tunnel** | $0 | Quick pilot | PC must stay on |

**Recommendation:** **Option A** — one Ubuntu VM running the same compose files as local demo. Simplest ops, nginx proxies `/api` to backend (no CORS split-brain).

---

## Phase 2 — Option A: Oracle Cloud VM (recommended)

### Step 2.1 Create VM

1. Sign up at [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Create **Compute → Instance** — Ubuntu 22.04 or 24.04, **Ampere A1** (ARM) shape if available (1 OCPU, 6 GB RAM is enough).
3. Download SSH private key; note **public IP**.
4. Security list / NSG: allow inbound **22** (SSH), **80** (HTTP), **443** (HTTPS).

### Step 2.2 SSH and install Docker

```bash
ssh ubuntu@YOUR_VM_IP
sudo bash deploy/demo/setup-ubuntu.sh
# Or clone first, then run script from repo
```

### Step 2.3 Clone demo branch

```bash
sudo mkdir -p /opt/fms
sudo chown $USER:$USER /opt/fms
cd /opt/fms
git clone -b demo/live https://github.com/YOUR_ORG/fms.git .
```

### Step 2.4 Configure environment

```bash
cp deploy/demo/.env.example deploy/demo/.env
nano deploy/demo/.env
```

Set at minimum:

```env
SECRET_KEY=<64-char hex from: python3 -c "import secrets; print(secrets.token_hex(32))">
PUBLIC_APP_URL=http://YOUR_VM_IP:8080
CORS_ORIGINS=http://YOUR_VM_IP:8080
WEB_PORT=8080
```

### Step 2.5 Start demo stack

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.demo.yml \
  -f deploy/demo/docker-compose.live.yml \
  --env-file deploy/demo/.env \
  up -d --build
```

Wait for healthy API:

```bash
docker compose logs migrate api --tail 50
curl -s http://127.0.0.1:8080/api/v1/health
```

Open **http://YOUR_VM_IP:8080** in a browser.

### Step 2.6 HTTPS (optional but recommended)

**Free domain + TLS with Caddy:**

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

`/etc/caddy/Caddyfile`:

```caddy
demo.yourdomain.com {
    reverse_proxy localhost:8080
}
```

Update `deploy/demo/.env`:

```env
PUBLIC_APP_URL=https://demo.yourdomain.com
CORS_ORIGINS=https://demo.yourdomain.com
```

Restart stack after env change: `docker compose ... up -d`

Point DNS **A record** → VM public IP.

### Step 2.7 Share logins with evaluators

From [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md):

| Email | Password | Role |
|-------|----------|------|
| super@demo.com | super123 | Platform super_user |
| admin@demo.com | admin123 | Maintenance company admin |
| client@demo.com | client123 | End client admin |

Add a **“Demo only — do not use real data”** banner in your invite email.

### Step 2.8 Nightly reset (optional)

Cron on VM (platform token from super@demo.com login):

```bash
crontab -e
# 03:00 UTC daily reset
0 3 * * * curl -sf -X POST http://127.0.0.1:8080/api/v1/platform/demo/reset -H "Authorization: Bearer YOUR_LONG_LIVED_TOKEN" || true
```

Or re-run migrate seed manually after destructive demos:

```bash
docker compose ... run --rm migrate
```

---

## Phase 3 — Option B: Render (alternative)

Render splits services; frontend uses relative `/api/v1` so you need **one public URL** that proxies API — use **only the web service with nginx** pointing to internal API URL, or deploy **web + api** on same custom domain with path routing (advanced).

Simpler Render path:

1. **PostgreSQL** — create database; copy **Internal Database URL**.
2. **Web Service** — Docker, `deploy/Dockerfile.api`, start command migrate then uvicorn (or run migrate as pre-deploy job).
3. Env: `DATABASE_URL`, `APP_ENV=demo`, `SECRET_KEY`, `CORS_ORIGINS`, `PUBLIC_APP_URL`.
4. **Static site** OR second Docker for `Dockerfile.web` — if static, you must change API base URL (not current setup).

Because FMS nginx expects `api` hostname on Docker network, **Render is harder than a single VM**. Prefer Option A unless you refactor for split deploy.

---

## Phase 4 — Post-deploy checklist

- [ ] `GET /api/v1/health` returns OK
- [ ] Login super@demo.com → Maintenance Companies visible
- [ ] Login client@demo.com → Request work order opens modal
- [ ] Arabic toggle persists after logout
- [ ] `POST /platform/demo/reset` works as super_user (403 in non-demo env)
- [ ] Firewall: Postgres **not** exposed publicly (live compose resets db ports)
- [ ] `SECRET_KEY` is unique per environment
- [ ] Document URL + logins for stakeholders

---

## Phase 5 — Updates and rollback

```bash
cd /opt/fms
git fetch origin
git checkout demo/live
git pull origin demo/live
docker compose -f docker-compose.yml -f docker-compose.demo.yml -f deploy/demo/docker-compose.live.yml --env-file deploy/demo/.env up -d --build
```

Rollback to tag:

```bash
git checkout demo-live-v1.0.0
docker compose ... up -d --build
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Blank page / 502 | `docker compose logs web api`; wait for migrate complete |
| CORS errors | `CORS_ORIGINS` must exactly match browser URL (scheme + host + port) |
| Login works locally not on server | Rebuild web+api; check `PUBLIC_APP_URL` |
| Empty database | `docker compose logs migrate`; re-run migrate service |
| Platform nav missing | User must be `super_user` + `is_platform_admin`; re-seed pitch |

See also: `.claude/skills/docker-debug/SKILL.md`, `.claude/skills/frontend-build/SKILL.md`

---

## Security notes for public demo

- Passwords in pitch seed are **intentionally weak** — demo only.
- Do not put real customer data on demo.
- Rotate `SECRET_KEY` if VM is compromised.
- Consider IP allowlist or Cloudflare Access for private pilots.
