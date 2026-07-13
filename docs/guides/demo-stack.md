# Demo stack (Docker) + Cloudflare tunnel

Isolated **pitch demo** — database `fms_demo`, seed `pitch_seed`, `APP_ENV=demo`.

Use for sales demos, E2E, and sharing a public URL via Cloudflare Tunnel.

**Local coding** (Vite + host API): [local-development.md](./local-development.md).  
**Seed profiles:** [docker-seed-profiles.md](./docker-seed-profiles.md).

---

## Ports (memorize this table)

| Service | Host port | Notes |
|---------|-----------|--------|
| **Web (UI)** | **9081** | Open this in the browser |
| **API** | **9001** | Also reached via nginx `/api` on 9081 |
| **Postgres** | **9543** | Was 5433 — changed to avoid native Windows Postgres clashes |

Windows often reserves **8001–8100**; demo intentionally uses **9001 / 9081**.

---

## Part 1 — Run the demo on your machine

### Step 1 — Start from the **repo root**

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-demo.yml up -d --build
```

Wait for migrate:

```text
migrate-1  | Migrate complete.
```

Check:

```powershell
docker compose -f docker-compose-demo.yml ps
curl http://localhost:9001/health
```

### Step 2 — Open the UI

**http://localhost:9081**

### Step 3 — Demo logins

Password = `{email-local-part}123` (default suffix).

| Email | Password | Role |
|-------|----------|------|
| super@demo.com | super123 | super_user — platform + demo reset |
| swdev@demo.com | swdev123 | sw_dev |
| admin@demo.com | admin123 | company_admin |
| client@demo.com | client123 | client_admin (Global Enterprises) |
| client2@demo.com | client2123 | client_admin (Riyadh Retail) |
| site@demo.com | site123 | site_manager |
| tech@demo.com | tech123 | technician |

**Seeded data:** 2 clients, 3 sites, ~15 assets, ~50 work orders across statuses, 2 draft invoices.

### Everyday commands

```powershell
cd E:\03Workset\FMS

docker compose -f docker-compose-demo.yml up -d
docker compose -f docker-compose-demo.yml logs -f api
docker compose -f docker-compose-demo.yml down

# Full wipe + re-seed
docker compose -f docker-compose-demo.yml down -v
docker compose -f docker-compose-demo.yml up -d --build
```

### Demo reset (API, no volume wipe)

```powershell
# After login as super@demo.com, use access_token:
curl -X POST http://localhost:9001/api/v1/platform/demo/reset `
  -H "Authorization: Bearer <access_token>"
```

Only when `APP_ENV=demo`.

---

## Part 2 — Share the demo with Cloudflare Tunnel

### What to tunnel

Tunnel the **web** container (**9081**), not Vite preview and not API-only:

```text
Internet → trycloudflare.com → cloudflared → localhost:9081 (nginx)
                                              ├─ /           → React
                                              └─ /api/v1/... → FastAPI
```

Same-origin `/api` means login works through the public URL (no CORS fight).

### Prerequisites

1. Demo stack healthy on **9081** / **9001** (Part 1).
2. [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/) installed (`cloudflared --version`).

### Step-by-step (quick tunnel — no Cloudflare account required)

```powershell
# Terminal 1 — keep demo running
cd E:\03Workset\FMS
docker compose -f docker-compose-demo.yml up -d

# Terminal 2 — public URL
cloudflared tunnel --url http://localhost:9081
```

Cloudflare prints a URL like:

```text
https://something-random.trycloudflare.com
```

Share that link. Keep **both** terminals/processes running.

### Verify

1. Open the trycloudflare URL → Orbit login page.
2. Sign in with `admin@demo.com` / `admin123`.
3. Dashboard / work orders should show seeded demo data.

### Caveats

| Topic | Detail |
|-------|--------|
| URL changes | Quick tunnels get a **new** hostname every run |
| Not production | No SLA; subject to Cloudflare ToS |
| Credentials | Demo passwords are public knowledge — fine for pitch only |
| Named tunnels | For a stable hostname, create a Cloudflare-account named tunnel |

### Optional — named tunnel (stable URL)

Requires a Cloudflare account + zone. High level:

```powershell
cloudflared tunnel login
cloudflared tunnel create orbit-demo
# Configure ingress: hostname → http://localhost:9081
cloudflared tunnel run orbit-demo
```

See [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/).

---

## Part 3 — Dev vs demo (do not mix)

| Profile | Command | UI | API | DB port | Seed |
|---------|---------|-----|-----|---------|------|
| **DEV hybrid** | `docker-compose-local.yml` + hybrid + host uvicorn | `:5173` | `:8000` | **9432** `fms_local` | `test_seed` |
| **DEV Docker** | `docker-compose-local.yml` | `:9080` | `:9000` | **9432** | `test_seed` |
| **DEMO Docker** | `docker-compose-demo.yml` | `:9081` | `:9001` | **9543** | `pitch_seed` |

Host uvicorn against demo DB (uncommon):

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-demo.yml up -d
copy backend\.env.demo.example backend\.env
# DATABASE_URL ... localhost:9543/fms_demo
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Prefer **http://localhost:9081** instead.

---

## Troubleshooting

### `password authentication failed for user "fms"`

Host hit the wrong Postgres (often native Windows on **5432/5433**).

```powershell
# Confirm Docker demo port
docker compose -f docker-compose-demo.yml port db 5432
# Expect 0.0.0.0:9543

# Inside container (always works if image is healthy):
docker exec fms-db-1 psql -U fms -d fms_demo -c "SELECT 1"
```

Fix host `.env` to use **9543** (`backend\.env.demo.example`) or switch to hybrid DEV **9432**.

### Compose file not found from `backend/`

```powershell
cd E:\03Workset\FMS
docker compose -f docker-compose-demo.yml up -d
```

### Tunnel up, blank / login `{}`

- Demo stack must be **up** on 9081 before cloudflared.
- Tunnel **9081**, not 4173/4174 (Vite preview) and not 9001 alone.

### Port bind forbidden (8001–8100)

Already avoided. Check reserved ranges if you change ports:

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

---

## Related

- [local-development.md](./local-development.md)
- [docker-seed-profiles.md](./docker-seed-profiles.md)
- [deployment.md](./deployment.md) — server deploy (not quick tunnel)
- `.claude/skills/docker-debug/SKILL.md`
