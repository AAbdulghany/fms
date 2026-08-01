# FMS Knowledge Hub

> Learning resources for the **Orbit (FMS)** codebase. For operational runbooks, see **[docs/guides/](../guides/)** and **[docs/README.md](../README.md)**.

---

## Overview

The Knowledge Hub contains hands-on tutorials based on the actual FMS codebase. Each topic includes:
- **Concepts** - What you need to understand
- **Code Examples** - Real code from FMS
- **Practice** - Exercises to reinforce learning

---

## Learning Paths

### Path 1: Backend Developer

| Order | Topic | File | Purpose |
|-------|-------|------|---------|
| 1 | FastAPI Basics | `backend/01_fastapi_basics.md` | REST APIs, routing, dependencies |
| 2 | SQLAlchemy Models | `backend/02_sqlalchemy_models.md` | Database models, relationships |
| 3 | JWT Authentication | `backend/03_jwt_auth.md` | Auth flow, token handling |
| 4 | RBAC | `backend/04_rbac.md` | Role-based access control |

### Path 2: Database Developer

| Order | Topic | File | Purpose |
|-------|-------|------|---------|
| 1 | PostgreSQL | `database/01_postgresql.md` | Types, queries, indexes |
| 2 | Alembic | `database/02_alembic.md` | Database migrations |

### Path 3: Frontend Developer

| Order | Topic | File | Purpose |
|-------|-------|------|---------|
| 1 | React Basics | `frontend/01_react_basics.md` | Components, hooks, routing |
| 2 | TypeScript | `frontend/02_typescript.md` | Types, generics |
| 3 | Tailwind CSS | `frontend/03_tailwind.md` | Styling, responsive design |
| 4 | i18n | `frontend/04_i18n.md` | Internationalization |

### Path 4: Architect

| Order | Topic | File | Purpose |
|-------|-------|------|---------|
| 1 | Multi-Tenancy | `architecture/01_multi_tenancy.md` | Tenant isolation |
| 2 | Testing | `architecture/02_testing.md` | pytest, RBAC tests |

---

## Getting Started

1. **Pick a path** based on your role/interest
2. **Read the topics** in order
3. **Study the code** in `FMS/` directory
4. **Complete exercises** to practice
5. **Run tests** to verify understanding

---

## Prerequisites

| Skill | Resource |
|-------|----------|
| Python | [Python Docs](https://docs.python.org/) |
| JavaScript | [MDN Web Docs](https://developer.mozilla.org/) |
| SQL | [PostgreSQL Tutorial](https://www.postgresql.org/docs/) |

---

## Development Environment

See **[guides/local-development.md](../guides/local-development.md)** for the current setup.

```powershell
# Backend tests (from repo root)
uv run pytest backend/tests/ -q

# Frontend dev
npm run dev

# Docker demo stack
docker compose -f docker-compose-local.yml -f docker-compose-demo.yml up --build
```

---

## Key Files Reference

| Purpose | Location |
|---------|----------|
| Models | `backend/app/models/` (domain package) |
| Routes | `backend/app/api/routes/` |
| Schemas | `backend/app/schemas.py` |
| Tests | `backend/tests/` |
| Frontend Pages | `src/pages/` |
| Components | `src/components/` |
| Types | `src/lib/types.ts` |
| i18n | `src/i18n/index.ts` |

---

## Topics Summary

### Backend (4 topics)
- FastAPI routing, dependencies, error handling
- SQLAlchemy ORM, relationships, migrations
- JWT tokens, password hashing
- Role-based access control

### Database (2 topics)
- PostgreSQL types, queries, indexes
- Alembic migrations

### Frontend (4 topics)
- React hooks, routing, context
- TypeScript types, generics
- Tailwind CSS, responsive design
- i18n, RTL support

### Architecture (2 topics)
- Multi-tenancy, tenant isolation
- Testing, RBAC tests

---

### Path 5: Product & UAT

| Order | Topic | File | Purpose |
|-------|-------|------|---------|
| 1 | Wave 3 UAT observations | `product/01_wave3_uat_observations.md` | Tester feedback, gaps vs code, ticket IDs |
| 1b | Wave 3 observation closure | `../phase3-restructure/WAVE3_OBSERVATIONS.md` | 18 OBS-* items — sign-off matrix |
| 2 | Post-UAT Phase 1 & 2 implementation | `product/02_post_uat_implementation.md` | WO state machine, asset schema, API changes |
| 3 | Wave 4 mega prompt & task registry | `product/03_wave4_mega_prompt.md` | Verification gaps, architect decisions, NT-P* tasks |

---

## Phase 3 Topics to Learn

Active delivery track: **[phase3-restructure/SPRINT_BACKLOG_NT.md](../phase3-restructure/SPRINT_BACKLOG_NT.md)**

| Topic | Helps With |
|-------|------------|
| ReportLab PDFs | Branded invoice & maintenance report exports (Wave 4) |
| Feature gates | Subscription `assets` / `invoices` modules |
| Playwright E2E | [guides/testing.md](../guides/testing.md) |
| Bilingual API errors | `backend/app/core/errors.py` + `src/lib/errors.ts` |

Historical progress (pre-restructure): [archive/phase3/PHASE3_PROGRESS.md](../archive/phase3/PHASE3_PROGRESS.md)

---

## Contributing

To add new topics:

1. Create file in appropriate folder
2. Use existing format
3. Add to this README index
4. Reference real FMS code

---

## Questions?

- Check existing tests in `backend/tests/`
- Review APIs in `backend/app/api/routes/`
- Ask in project discussions

---

**Last Updated:** June 2026 — Wave 6 cleanup / Wave 4 delivery