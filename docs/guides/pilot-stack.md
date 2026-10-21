# Pilot stack (Docker) and public sharing

The **pilot** environment is the sales, UAT, and field-pilot stack. It uses database `fms_pilot`, seed `pilot_seed`, and `APP_ENV=pilot`. It replaces the former "demo" stack.

- Environment matrix: [environments.md](./environments.md)
- Local coding (Vite + host API): [local-development.md](./local-development.md)
- Seed profiles: [docker-seed-profiles.md](./docker-seed-profiles.md)

---

## Ports

| Service | Host port | Notes |
|---------|-----------|-------|
| Web (UI) | **9081** | Open this in the browser. nginx serves `/api` on the same origin. |
| API | **9001** | Direct API access for local tools only |
| Postgres | **9543** | Avoids native Windows Postgres on 5432/5433 |

Windows often reserves ports 8001–8100. The pilot stack uses 9001 and 9081 to avoid that range.

---

## 1. Run the pilot stack locally

Run from the repository root:

```powershell
docker compose -f docker-compose-pilot.yml up -d --build
docker compose -f docker-compose-pilot.yml logs -f migrate   # wait for "Migrate complete."
curl http://localhost:9001/health
```

Open **http://localhost:9081**.

If you ran the old demo stack before, stop it first. Its containers hold the same ports:

```powershell
docker compose -p fms-demo down
```

### Seed accounts

The password is `{email-local-part}{suffix}`. The default suffix is `123`; override it with `SEED_PASSWORD_SUFFIX`.

| Email | Role |
|-------|------|
| super@demo.com | super_user (platform admin, can run pilot reset) |
| swdev@demo.com | sw_dev |
| admin@demo.com | company_admin |
| client@demo.com | client_admin (Global Enterprises) |
| client2@demo.com | client_admin (Riyadh Retail) |
| site@demo.com | site_manager |
| tech@demo.com | technician |

The `@demo.com` addresses are seed data. They are unchanged so that e2e fixtures and shared logins keep working.

Seeded data: 2 clients, 3 sites, about 15 assets, about 50 work orders across all statuses, and 2 draft invoices.

### Everyday commands

```powershell
docker compose -f docker-compose-pilot.yml up -d
docker compose -f docker-compose-pilot.yml logs -f api
docker compose -f docker-compose-pilot.yml down

# Full wipe and re-seed
docker compose -f docker-compose-pilot.yml down -v
docker compose -f docker-compose-pilot.yml up -d --build
```

### Pilot reset (API, no volume wipe)

Log in as `super@demo.com`, then call:

```powershell
curl -X POST http://localhost:9001/api/v1/platform/pilot/reset `
  -H "Authorization: Bearer <access_token>"
```

The endpoint returns `403 PILOT_ENV_ONLY` unless `APP_ENV=pilot`. The old path `/platform/demo/reset` still works for existing cron jobs.

---

## 2. Pilot with managed Postgres (Supabase)

This variant has no local database container.

```powershell
copy deploy\pilot\.env.supabase.example deploy\pilot\.env.supabase
# Fill in DATABASE_URL and SECRET_KEY. The file is gitignored.
docker compose -f docker-compose-pilot-supabase.yml --env-file deploy/pilot/.env.supabase up -d --build
```

UI: http://localhost:9581 · API: http://localhost:9501

If you have a local `deploy/demo/.env.supabase-demo` from before the reorg, move it to `deploy/pilot/.env.supabase`. Both paths are gitignored.

---

## 3. Share a local pilot with Cloudflare Tunnel

Tunnel the **web** port, not the API port and not Vite preview. nginx keeps `/api` on the same origin, so login works without CORS changes.

```text
Internet -> Cloudflare -> cloudflared -> localhost:9081 (nginx)
                                          |- /          -> React
                                          |- /api/v1/... -> FastAPI
```

Quick tunnel (no Cloudflare account; the hostname changes every run):

```powershell
cloudflared tunnel --url http://localhost:9081
```

For a stable hostname, use a named tunnel on a subdomain (currently `demo.orbittech.co`). Don't use a path such as `/pilot`, because SPA routes and `/api` must stay same-origin.

The seed passwords are public knowledge. Use a shared pilot only with seed data, never with customer data.

---

## 4. Pilot server (VM)

The `Deploy Orbit Pilot` workflow deploys on every push to `pilot/live`. During the transition, pushes to `demo/live` also deploy. See [deploy/pilot/README.md](../../deploy/pilot/README.md) for the server files, and [ENV_REORG_PLAN.md](../engineering/ENV_REORG_PLAN.md) for the cutover steps.

Manual equivalent on the server:

```bash
docker compose -f docker-compose-pilot.yml -f deploy/pilot/docker-compose.live.yml \
  --env-file deploy/pilot/.env up -d --build
```

The live overlay publishes only the web container on `WEB_PORT` (default 8080). Point the Cloudflare Tunnel at `http://localhost:${WEB_PORT}`.

---

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| `Bind for 0.0.0.0:9081 failed: port is already allocated` | The old `fms-demo` project is still running. Run `docker compose -p fms-demo down`. |
| `password authentication failed for user "fms"` | The host reached a different Postgres. Check with `docker compose -f docker-compose-pilot.yml port db 5432` (expect `9543`), and use `backend/.env.pilot.example` for host uvicorn. |
| `APP_ENV must be one of development, pilot, production` | An env file sets an unsupported value. `demo` is still accepted and maps to `pilot`. |
| Tunnel up but blank page or login returns `{}` | The stack isn't up on 9081, or the tunnel points at the API port or Vite preview. |
| Port bind forbidden in 8001–8100 | Windows reserved range. Check with `netsh interface ipv4 show excludedportrange protocol=tcp`. |

Pre-reorg instructions are archived in [docs/archive/demo/](../archive/demo/).
