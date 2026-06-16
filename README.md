# FMS (Facility Management System)

> **Production-ready facility management system with comprehensive RBAC, multi-tenant isolation, and automated testing.**

[![Tests](https://img.shields.io/badge/tests-76%20passing-brightgreen)](backend/tests/)
[![Phase](https://img.shields.io/badge/phase-2%20complete-blue)](docs/phase2/PHASE2_COMPLETE.md)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18-blue)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5-blue)](https://www.typescriptlang.org/)

---

## Overview

FMS is a comprehensive facility management system designed for multi-tenant environments with advanced role-based access control. Phase 2 delivers a production-ready system with:

- ✅ **6 Role Types** — Super Admin, Company Admin, Client Admin, Site Manager, Manager, Technician
- ✅ **Tenant Isolation** — Multi-tenant with strict data separation (76 automated tests)
- ✅ **Hierarchical Locations** — Building → Floor → Zone → Room
- ✅ **Asset Lifecycle** — Automatic replacement work orders at end-of-life
- ✅ **Labor Management** — Technician profiles, time tracking, scheduling
- ✅ **Advanced Filtering** — Search, status, date range, role-aware
- ✅ **RTL Support** — Full Arabic language support
- ✅ **Production Ready** — Zero known security issues, 100% test pass rate

---

## Quick Start

See **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** for detailed setup instructions.

### Docker demo (pitch stack)

Full command reference and logins: **[docs/phase3-restructure/DEMO_QUICKSTART.md](docs/phase3-restructure/DEMO_QUICKSTART.md)**

```powershell
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build
```

Open http://localhost:8080 — login `super@demo.com` / `super123`

**Public demo on a free server:** **[docs/phase3-restructure/DEMO_LIVE_DEPLOY.md](docs/phase3-restructure/DEMO_LIVE_DEPLOY.md)** — Oracle Cloud VM + Docker.

**Vercel / Netlify (free `*.vercel.app` domain):** **[docs/phase3-restructure/DEMO_VERCEL_NETLIFY.md](docs/phase3-restructure/DEMO_VERCEL_NETLIFY.md)** — UI on Vercel or Netlify + API on Render.

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- `uv` package manager

### Installation

```powershell
# 1. Clone repository
git clone <repo-url>
cd FMS

# 2. Backend setup
cd backend
uv sync
uv run alembic -c backend/alembic.ini upgrade head

# 3. Seed super user (minimal)
$env:PYTHONPATH="backend"
uv run python -m app.seed_super

# 4. Frontend setup
cd ..
npm install

# 5. Run backend (terminal 1)
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Run frontend (terminal 2)
npm run dev
```

### Default Credentials

**Super Admin:**
- Email: `super@example.com`
- Password: `supersecret`

---

## Documentation

### Phase 2 Documentation
- **[Phase 2 Complete Overview](docs/phase2/PHASE2_COMPLETE.md)** — Executive summary, features, deployment
- **[API Reference](docs/phase2/API_REFERENCE.md)** — Complete endpoint documentation
- **[Implementation Guide](docs/phase2/IMPLEMENTATION_GUIDE.md)** — Developer guide for extending the system
- **[Milestone 4 & 5 Summary](docs/phase2/Milestone_4_and_5_Summary.md)** — Latest milestone runbook
- **[RBAC Matrix](docs/phase2/RBAC_Matrix.md)** — Role permission matrix
- **[QA Quick Start Guide](docs/phase2/QA_Quick_Start_Guide.md)** — Testing guide

### General Documentation
- **[User Guide](docs/USER_GUIDE.md)** — Setup and usage instructions
- **[Phase 2 Implementation Plan](docs/claude_phase2_implementation.md)** — Original implementation plan

---

## Features

### Phase 2 Highlights

#### 🔐 Role-Based Access Control
- **6 user roles** with granular permissions
- **76 automated tests** covering all role scenarios
- Tenant isolation verified and tested

#### 📍 Hierarchical Locations (P2-F5)
- Tree structure: Building → Floor → Zone → Room
- Optional location assignment for assets and work orders
- Site-scoped with role-aware access

#### ⏱️ Labor Management (P2-F4)
- Technician profiles with hourly rates
- Labor entry tracking (regular + overtime)
- Weekly scheduling (day/time)
- Technicians limited to assigned work orders

#### 🔧 Asset Lifecycle (P2-F2)
- Automatic status transitions: active → warning → end-of-life
- Auto-creates replacement work order at EOL
- Tracks repair count and asset age
- Dashboard alerts for warning/EOL assets

#### 🏷️ Maintenance Tags (P2-F3)
- Tags: preventive, corrective, protective
- Filterable in work order lists
- Visual tag badges

#### 🔍 Advanced Filtering (P2-F1)
- Status, urgency, date range, full-text search
- Client, site, assignee filters
- URL query param persistence
- Role-aware visibility

#### 📊 Role-Based Dashboards (P2-F6)
- Super Admin: All companies, total WOs, revenue
- Client Admin: Sites overview, billing summary
- Site Manager: Site-specific WOs, asset status
- Technician: My assigned WOs, completed this week

---

## Technology Stack

### Backend
- **FastAPI** — REST API framework
- **SQLAlchemy** — ORM with async support
- **Alembic** — Database migrations
- **PostgreSQL** — Primary database
- **Pydantic** — Schema validation
- **pytest** — Testing framework (76 tests, 100% pass rate)

### Frontend
- **React 18** — UI framework
- **TypeScript** — Type safety
- **Vite** — Build tool
- **Tailwind CSS** — Styling
- **i18next** — Internationalization (Arabic + English)
- **React Router** — Navigation

---

## Testing

### Run All Tests

```powershell
# Backend tests (76 tests)
uv run pytest backend/tests/ -v

# Quick run
uv run pytest backend/tests/ -q

# With coverage
uv run pytest backend/tests/ --cov=app --cov-report=html
```

### Test Coverage

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| RBAC | 46+ | All roles, all endpoints |
| Tenant Isolation | 24 | Cross-tenant access prevention |
| Asset Lifecycle | 4 | Automatic status updates, replacement WOs |
| Tenancy | 2 | Basic tenant scoping |
| **Total** | **76** | **100% pass rate** |

---

## Project Structure

```
FMS/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── main.py          # FastAPI app
│   ├── migrations/          # Alembic migrations
│   └── tests/               # pytest test suite
├── src/
│   ├── components/          # React components
│   ├── pages/               # Page components
│   ├── lib/                 # API client, types
│   ├── i18n/                # Translations (AR/EN)
│   └── App.tsx              # Main app + routing
└── docs/
    ├── phase2/              # Phase 2 documentation
    └── USER_GUIDE.md        # Setup guide
```

---

## Database Schema

### Key Tables (Phase 2)

- **tenants** — Multi-tenant root
- **users** — Authentication + RBAC
- **clients** — Companies/organizations
- **sites** — Physical locations
- **locations** — Hierarchical (building/floor/zone/room)
- **assets** — Equipment with lifecycle tracking
- **work_orders** — Service requests with tags
- **labor_entries** — Time tracking per WO
- **technician_profiles** — Hourly rates, skills
- **technician_schedules** — Weekly availability
- **invoices** — Billing records

---

## API Endpoints

### Core Endpoints

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/dashboard/summary` | GET | Role-aware dashboard stats |
| `/locations` | GET, POST, PATCH, DELETE | Hierarchical locations |
| `/locations/tree` | GET | Tree structure for site |
| `/labor/profiles` | GET, POST, PATCH | Technician profiles |
| `/labor/entries` | GET, POST | Time tracking |
| `/labor/schedules` | GET, POST, DELETE | Weekly schedules |
| `/work-orders` | GET, POST, PATCH, DELETE | Work orders (with filters) |
| `/assets` | GET, POST, PATCH, DELETE | Assets (with lifecycle) |
| `/invoices` | GET, POST, PATCH, DELETE | Billing records |

See **[API Reference](docs/phase2/API_REFERENCE.md)** for complete documentation.

---

## Deployment

### Production Checklist

- [ ] Set `DATABASE_URL` to production PostgreSQL
- [ ] Generate secure `SECRET_KEY` (32+ characters)
- [ ] Apply migrations: `uv run alembic upgrade head`
- [ ] Seed super user: `uv run python -m app.seed_super`
- [ ] Configure CORS in `backend/app/main.py`
- [ ] Enable HTTPS (SSL certificates)
- [ ] Set up error tracking (Sentry)
- [ ] Configure log rotation
- [ ] Schedule database backups (daily)

### Environment Variables

**Backend** (`.env`):
```
DATABASE_URL=postgresql://user:pass@localhost/fms_prod
SECRET_KEY=<secure-random-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**Frontend** (`.env.production`):
```
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## Contributing

### Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests
3. Run test suite: `uv run pytest backend/tests/`
4. Type check frontend: `npm run type-check`
5. Build frontend: `npm run build`
6. Commit with conventional commits: `feat:`, `fix:`, `docs:`, etc.
7. Push and create PR

### Commit Convention

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `test:` — Test changes
- `refactor:` — Code refactoring
- `chore:` — Tooling, dependencies

---

## Support & Troubleshooting

### Common Issues

**Problem:** Tests fail with database errors  
**Solution:** Ensure test database exists: `createdb test_db`

**Problem:** Frontend build fails  
**Solution:** Run `npm run type-check` for detailed errors

**Problem:** 401 Unauthorized on all requests  
**Solution:** Check JWT token in `Authorization: Bearer <token>` header

**Problem:** Alembic can't import app modules  
**Solution:** Set `PYTHONPATH=backend` or `$env:PYTHONPATH="backend"`

See **[Implementation Guide](docs/phase2/IMPLEMENTATION_GUIDE.md)** for more troubleshooting tips.

---

## Roadmap

### Phase 3 Candidates

- **Map Integration** — Visual floor plans for locations
- **Mobile App** — React Native or PWA
- **Advanced Reporting** — Export to PDF, Excel
- **Email Notifications** — SendGrid integration
- **File Attachments** — S3 integration for work order photos
- **Calendar View** — FullCalendar for scheduling
- **Real-time Updates** — WebSocket for live notifications
- **Barcode/QR Scanning** — Asset identification
- **Performance Optimization** — Query caching, lazy loading
- **Advanced Analytics** — Power BI / Tableau integration

---

## License

Proprietary — All rights reserved

---

## Contact

For questions or support, please contact the FMS development team.

---

**Status:** ✅ Phase 2 Complete (76/76 tests passing)  
**Last Updated:** April 18, 2026