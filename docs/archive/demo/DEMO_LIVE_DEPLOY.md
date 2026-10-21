# Demo live deployment — step-by-step (free tier)

Deploy the **pitch demo** so external users can try FMS without installing Docker locally.

| Goal | Value |
|------|--------|
| Branch | `demo/live` (see [deploy/demo/BRANCH_MANIFEST.md](../../deploy/demo/BRANCH_MANIFEST.md)) |
| Profile | `APP_ENV=demo`, database `fms_demo`, seed `pitch_seed` |
| Stack | PostgreSQL + FastAPI + Nginx/React (same as local demo) |
| Public URL (free) | **https://demo.orbittech.co** via Cloudflare Tunnel + Oracle Always Free VM |

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

docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
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

**Recommendation:** **Option A** — one Ubuntu VM running the same compose files as local demo. Simplest ops, nginx proxies `/api` to backend (no CORS split-brain). Put **Cloudflare Tunnel** in front for free HTTPS at **`https://demo.orbittech.co`** (subdomain, not `orbittech.co/demo`).

---

## Phase 2 — Option A: Oracle Cloud VM (recommended)

### Step 2.1 Create VM

1. Sign up at [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/).
2. Create **Compute → Instance** — Ubuntu 22.04 or 24.04, **Ampere A1** (ARM) shape if available (1 OCPU, 6 GB RAM is enough).
3. Download SSH private key; note **public IP**.
4. Security list / NSG: allow inbound **22** (SSH). With Cloudflare Tunnel you do **not** need to open 80/443 on the VM (tunnel is outbound-only).

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

Set at minimum (free showcase on Cloudflare):

```env
SECRET_KEY=<64-char hex from: python3 -c "import secrets; print(secrets.token_hex(32))">
PUBLIC_APP_URL=https://demo.orbittech.co
CORS_ORIGINS=https://demo.orbittech.co
WEB_PORT=8080
```

### Step 2.5 Start demo stack

```bash
docker compose \
  -f docker-compose-local.yml \
  -f docker-compose-demo.yml \
  -f deploy/demo/docker-compose.live.yml \
  --env-file deploy/demo/.env \
  up -d --build
```

Wait for healthy API:

```bash
docker compose logs migrate api --tail 50
curl -s http://127.0.0.1:8080/api/v1/health
```

Smoke-test on the VM: **http://127.0.0.1:8080** (or the public IP only if you opened the port). Public evaluators use **https://demo.orbittech.co** after Step 2.6.

### Step 2.6 HTTPS — Cloudflare Tunnel → demo.orbittech.co (free, recommended)

Uses your existing Cloudflare zone **`orbittech.co`**. No Workers, no paid plan required for a named tunnel.

#### A. Create the tunnel (Cloudflare Zero Trust dashboard)

1. Log in to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) → **Networks** → **Tunnels** → **Create a tunnel**.
2. Name: `orbit-demo`. Choose **Cloudflared**.
3. Copy the install token / command for Linux and run it on the **VM** (installs `cloudflared` and a systemd unit so the tunnel survives reboot).
4. **Public Hostname** tab:
   - Subdomain: `demo`
   - Domain: `orbittech.co`
   - Service: `http://localhost:8080` (matches `WEB_PORT` in live compose)
5. Save. Cloudflare creates the DNS CNAME for `demo.orbittech.co` automatically.

#### B. CLI alternative

```bash
# On a machine with cloudflared + browser login to the orbittech.co account
cloudflared tunnel login
cloudflared tunnel create orbit-demo
# Add ingress: demo.orbittech.co → http://localhost:8080
# Then on the VM: install credentials + systemd, or:
cloudflared tunnel run orbit-demo
```

See [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) and local notes in [demo-stack.md](../guides/demo-stack.md).

#### C. Verify

1. Open **https://demo.orbittech.co** → Orbit login.
2. `curl -fsS https://demo.orbittech.co/api/v1/health`
3. Confirm `CORS_ORIGINS` / `PUBLIC_APP_URL` are exactly `https://demo.orbittech.co` (no trailing slash).

#### Alternative: Caddy + DNS A record

If you prefer TLS on the VM instead of a tunnel, open 80/443, point an A record at the VM IP, and reverse-proxy with Caddy:

```caddy
demo.orbittech.co {
    reverse_proxy localhost:8080
}
```

Tunnel is preferred on Always Free VMs (no inbound 80/443, works behind restrictive NSGs).

### Step 2.7 Share logins with evaluators

From [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md):

| Email | Password | Role |
|-------|----------|------|
| super@demo.com | super123 | Platform super_user |
| admin@demo.com | admin123 | Maintenance company admin |
| client@demo.com | client123 | End client admin |

Share **https://demo.orbittech.co** plus a **“Demo only — do not use real data”** note.

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
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml -f deploy/demo/docker-compose.live.yml --env-file deploy/demo/.env up -d --build
```

Rollback to tag:

```bash
git checkout demo-live-v1.0.0
docker compose ... up -d --build
```

---

## Phase 5.1 — CI deploy (GitHub Actions)

Workflow: [`.github/workflows/deploy-orbit-demo.yml`](../../.github/workflows/deploy-orbit-demo.yml) (**Deploy Orbit Demo Showcase**).

On every push to **`demo/live`** (and on **workflow_dispatch**), CI SSHs into the demo VM, pulls the branch, and runs the same live compose `up -d --build` as above. Pitch seed runs via the existing migrate service — there is no separate `/api/setup` step.

Cloudflare Tunnel to **`https://demo.orbittech.co`** (Step 2.6) is **one-time host setup**. The Action does not call Wrangler or Workers; it only health-checks the optional public URL after deploy.

### Prerequisites (once)

1. Complete Phase 2 (Oracle Always Free VM + Docker + clone at `/opt/fms` + `deploy/demo/.env`).
2. Cloudflare Tunnel live for **`demo.orbittech.co`** → `http://localhost:8080`.
3. Ensure the SSH deploy user can `git pull` and run `docker compose` in the clone path.
4. Configure GitHub **Secrets** and **Variables** on the repo:

| Name | Kind | Required | Purpose |
|------|------|----------|---------|
| `DEMO_HOST` | secret | yes | VM hostname or IP |
| `DEMO_USER` | secret | yes | SSH user |
| `DEMO_SSH_PRIVATE_KEY` | secret | yes | Private key for that user |
| `DEMO_PATH` | secret | no | Clone path (default `/opt/fms`) |
| `DEMO_URL` | variable | recommended | `https://demo.orbittech.co` — post-deploy `GET /api/v1/health` |

Keep `deploy/demo/.env` **on the server only** — never commit it or overwrite it from CI.

### Manual run

Actions → **Deploy Orbit Demo Showcase** → Run workflow.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Blank page / 502 | `docker compose logs web api`; wait for migrate complete |
| CORS errors | `CORS_ORIGINS` must exactly match browser URL (scheme + host + port) — for showcase: `https://demo.orbittech.co` |
| Login works locally not on server | Rebuild web+api; check `PUBLIC_APP_URL` |
| Empty database | `docker compose logs migrate`; re-run migrate service |
| Platform nav missing | User must be `super_user` + `is_platform_admin`; re-seed pitch |
| `demo.orbittech.co` 502 / timeout | `systemctl status cloudflared`; tunnel must target `http://localhost:8080`; stack must be up |
| GH Action SSH fails | Secrets `DEMO_HOST` / `DEMO_USER` / `DEMO_SSH_PRIVATE_KEY`; user in `docker` group |

See also: `.claude/skills/docker-debug/SKILL.md`, `.claude/skills/frontend-build/SKILL.md`

---

## Security notes for public demo

- Passwords in pitch seed are **intentionally weak** — demo only.
- Do not put real customer data on demo.
- Rotate `SECRET_KEY` if VM is compromised.
- Consider IP allowlist or Cloudflare Access for private pilots.
