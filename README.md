# Orbit (FMS)

**Facility Management System** — multi-tenant maintenance, assets, template-driven reports, and billing.

[![Tests](https://img.shields.io/badge/pytest-219%2B%20passing-brightgreen)](docs/guides/testing.md)
[![Phase](https://img.shields.io/badge/delivery-Wave%204-blue)](docs/phase3-restructure/SPRINT_BACKLOG_NT.md)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-blue)](https://react.dev/)

---

## Quick start

### Pitch demo (Docker — recommended for first run)

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

Open **http://localhost:8080** — login `super@demo.com` / `super123`

Full commands, logins, troubleshooting: **[docs/guides/demo-stack.md](docs/guides/demo-stack.md)**

### Local development (hot reload)

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
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
| [Demo stack](docs/guides/demo-stack.md) | Docker demo, logins, reset |
| [Testing](docs/guides/testing.md) | pytest, Playwright, CI |
| [Deployment](docs/guides/deployment.md) | demo/live branch, cloud, production |
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
├── src/                  # React SPA (features/ pilot + pages/)
├── tests/e2e/            # Playwright scenarios
├── docs/                 # Runbooks, architecture, wave trackers
├── deploy/               # Dockerfiles, nginx, live demo overlay
└── docker-compose*.yml   # Dev, demo, local hybrid profiles
```

---

## Tests

```powershell
uv run pytest backend/tests/ -q    # backend
npm run build                       # frontend regression
# E2E: demo stack up, then npx playwright test tests/e2e/
```

Details: **[docs/guides/testing.md](docs/guides/testing.md)**

---

## Public demo deployment

Deploy the pitch stack to a free VM (Oracle Cloud, etc.):

**[docs/phase3-restructure/DEMO_LIVE_DEPLOY.md](docs/phase3-restructure/DEMO_LIVE_DEPLOY.md)** · branch `demo/live`

---

## License

Proprietary — All rights reserved
