# Demo Deployment — Wave 2 (NT-112, NT-115)

> **Canonical guide:** [guides/deployment.md](../guides/deployment.md) · **Local demo:** [guides/demo-stack.md](../guides/demo-stack.md)

> **Quick reference:** [DEMO_QUICKSTART.md](DEMO_QUICKSTART.md) — Docker commands, logins, troubleshooting.

**Profile:** `demo` — isolated pitch database, resettable seed  
**Stack:** FastAPI + React/Vite + PostgreSQL

---

## Local demo stack

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

Open http://localhost:8080 — logins in [DEMO_QUICKSTART.md](DEMO_QUICKSTART.md).
| Service | Port | Notes |
|---------|------|-------|
| web | 8080 | Nginx + API proxy |
| api | 8000 | `APP_ENV=demo` |
| db | 5432 | Database `fms_demo` |
| migrate | — | Runs `python -m app.docker_migrate` (alembic + pitch seed) |

### Demo vs development

| Profile | Command | DB | Seed |
|---------|---------|-----|------|
| Development | `docker compose up` | `fms` | `app.test_seed` |
| Demo | `docker compose -f docker-compose.yml -f docker-compose.demo.yml up` | `fms_demo` | `app.pitch_seed` |

---

## Pitch demo logins

| Email | Password | Role |
|-------|----------|------|
| **super@demo.com** | `super123` | super_user | Platform — maintenance companies, packages, demo reset |
| **swdev@demo.com** | `swdev123` | sw_dev | Platform support (cannot remove members) |
| admin@demo.com | `admin123` | company_admin | Maintenance company admin |
| client@demo.com | client123 | client_admin (Global Enterprises) |
| client2@demo.com | client223 | client_admin (Riyadh Retail) |
| site@demo.com | site123 | site_manager |
| tech@demo.com | tech123 | technician |

**Seed contents:** 1 maintenance tenant, 2 end clients, 4+ assets, 3 work orders, 2 draft invoices.

---

## Reset demo data

Platform admin only, `APP_ENV=demo`:

```bash
curl -X POST http://localhost:8000/api/v1/platform/demo/reset \
  -H "Authorization: Bearer <platform_admin_token>"
```

Returns `403` in `development` or `production`.

---

## Railway demo instance

1. Create project → PostgreSQL plugin
2. API service: `deploy/Dockerfile.api`
3. Env vars:
   - `DATABASE_URL` → point to `fms_demo` schema or dedicated DB
   - `APP_ENV=demo`
   - `SECRET_KEY`, `CORS_ORIGINS`, `PUBLIC_APP_URL`
4. One-off seed: `python -m app.pitch_seed`
5. Optional cron/one-off for nightly reset via `POST /platform/demo/reset`

See also [DEMO_LIVE_DEPLOY.md](DEMO_LIVE_DEPLOY.md) for **public demo on a free VM** (step-by-step).
See also [archive/phase3.1/DEMO_DEPLOY.md](../archive/phase3.1/DEMO_DEPLOY.md) for general hosting notes (historical).

---

## Troubleshooting

- **403 on platform routes:** user needs `is_platform_admin=true` (super@demo.com in pitch seed).
- **Demo reset 403:** confirm `APP_ENV=demo` on API container.
- **Empty tenant list in license UI:** run pitch seed or assign platform admin to your user.
