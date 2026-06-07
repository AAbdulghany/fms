# FMS Knowledge Hub

> A learning resource for the NexTask FMS codebase. Study these topics to understand and contribute to Phase 3 development.

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

```bash
# Backend
cd backend
uv sync
uv run pytest backend/tests/ -v

# Frontend
npm run dev

# Run specific test
pytest backend/tests/test_rbac.py -v
```

---

## Key Files Reference

| Purpose | Location |
|---------|----------|
| Models | `backend/app/models.py` |
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

## Phase 3 Topics to Learn

Based on the [Phase 3 Progress](./phase3/PHASE3_PROGRESS.md), these topics help complete Phase 3:

| Topic | Helps With |
|-------|------------|
| S3/Storage | File uploads documentation |
| WebSocket | Real-time notifications |
| Email | SMTP integration |
| Multi-currency | Billing system |

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

**Last Updated:** April 18, 2026