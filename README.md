# Orbit (FMS)

**Facility Management System** — multi-tenant maintenance, assets, template-driven reports, and billing.

[![Tests](https://img.shields.io/badge/pytest-219%2B%20passing-brightgreen)](docs/guides/testing.md)
[![Phase](https://img.shields.io/badge/delivery-Wave%204-blue)](docs/phase3-restructure/SPRINT_BACKLOG_NT.md)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-blue)](https://react.dev/)

---

## Quick start

### Pilot stack (Docker — recommended for first run)

```powershell
docker compose -f docker-compose-pilot.yml up -d --build
```

Open **http://localhost:9081** — login `super@demo.com` / `super123`

Full commands, logins, troubleshooting: **[docs/guides/pilot-stack.md](docs/guides/pilot-stack.md)** · environments: **[docs/guides/environments.md](docs/guides/environments.md)** (dev / pilot / production)

### Local development (hot reload)

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
uv sync
uv run alembic -c backend/alembic.ini upgrade head
$env:PYTHONPATH = "backend"; uv run python -m app.seed_super
# Terminal 1: uvicorn on :8000  |  Terminal 2: npm run dev → :5173
```

**[docs/guides/local-development.md](docs/guides/local-development.md)**

---

## Documentation

| Guide | Description |
|-------|-------------|
| **[docs/README.md](docs/README.md)** | Documentation hub — start here |
| [Local development](docs/guides/local-development.md) | uv, Vite, seeds, troubleshooting |
| [Environments](docs/guides/environments.md) | Dev / pilot / production matrix |
| [Pilot stack](docs/guides/pilot-stack.md) | Docker pilot, logins, reset, tunnel |
| [Testing](docs/guides/testing.md) | pytest, Playwright, CI |
| [Deployment](docs/guides/deployment.md) | pilot/live branch, cloud, production |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Cleanup stage](docs/CLEANUP_STAGE.md) | Wave 6 restructure — **complete** (pending merge) |

**Active delivery:** [Wave backlog](docs/phase3-restructure/SPRINT_BACKLOG_NT.md) · [Test strategy](docs/phase3-restructure/TEST_STRATEGY.md) · [RBAC](docs/architecture/RBAC.md)

---

## Stack

| Layer | Technology |
|-------|------------|
| API | FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| Web | React 18, TypeScript, Vite, Tailwind CSS |
| i18n | react-i18next (Arabic default, English, RTL) |
| Tests | pytest (219+), Playwright E2E, GitHub Actions CI |

---

## Project layout

```
FMS/
├── backend/app/          # FastAPI — routes, services, models
├── backend/tests/domains/  # pytest by domain
├── src/                  # React SPA (app/, features/, shared/)
├── tests/e2e/            # Playwright scenarios
├── docs/                 # Runbooks, architecture, wave trackers
├── deploy/               # Dockerfiles, nginx, dev/ pilot/ production/ env templates
└── docker-compose-*.yml   # local (dev), hybrid, pilot, pilot-supabase, prod
```

---

## Tests

```powershell
uv run pytest backend/tests/ -q    # backend
npm run build                       # frontend regression
# E2E: pilot stack up, then npx playwright test tests/e2e/
```

Details: **[docs/guides/testing.md](docs/guides/testing.md)**

---

## Pilot deployment

Deploy the pilot stack to a VM (Oracle Cloud free tier, etc.) behind Cloudflare Tunnel:

**[docs/guides/deployment.md](docs/guides/deployment.md#pilot-server-pilotlive-branch)** · branch `pilot/live`

---

## License

Proprietary — All rights reserved
