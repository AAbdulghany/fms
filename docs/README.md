# Orbit (FMS) — Documentation

**Facility Management System** — multi-tenant SaaS for maintenance, assets, reports, and billing.

| | |
|--|--|
| **Stack** | FastAPI · PostgreSQL · React 18 · TypeScript · Vite · Tailwind |
| **i18n** | Arabic (default) + English, full RTL |
| **Tests** | 219+ backend pytest · Playwright E2E · CI on every PR |
| **Active delivery** | Phase 3 restructure — Waves 0–5 ([backlog](./phase3-restructure/SPRINT_BACKLOG_NT.md)) |

---

## Start here

| I want to… | Read |
|------------|------|
| Run locally (Vite + uvicorn) | [guides/local-development.md](./guides/local-development.md) |
| Run the pitch demo (Docker) | [guides/demo-stack.md](./guides/demo-stack.md) |
| Share demo via Cloudflare Tunnel | [guides/demo-stack.md](./guides/demo-stack.md#part-2--share-the-demo-with-cloudflare-tunnel) |
| Understand Docker seed profiles | [guides/docker-seed-profiles.md](./guides/docker-seed-profiles.md) |
| Run tests (pytest & Playwright) | [guides/testing.md](./guides/testing.md) |
| Deploy demo to a server | [guides/deployment.md](./guides/deployment.md) |
| Understand architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| See current wave tickets | [phase3-restructure/SPRINT_BACKLOG_NT.md](./phase3-restructure/SPRINT_BACKLOG_NT.md) |

---

## Run modes (quick reference)

| Mode | Command | UI | API | Database | Seed |
|------|---------|-----|-----|----------|------|
| **Local hybrid DEV** | hybrid compose + Vite + uvicorn | `:5173` | `:8000` | `fms_local` **:9432** | `test_seed` |
| **Docker DEV** | `docker compose -f docker-compose-local.yml up --build` | `:9080` | `:9000` | `fms_local` **:9432** | `test_seed` |
| **Docker DEMO** | `docker compose -f docker-compose-demo.yml up --build` | `:9081` | `:9001` | `fms_demo` **:9543** | `pitch_seed` |

Compose projects are isolated: **`fms-local`** vs **`fms-demo`** (separate `name:` in each file). Do not mix `.env` ports.

---

## Product & delivery docs

| Area | Path |
|------|------|
| Wave governance | [phase3-restructure/WAVE_GOVERNANCE.md](./phase3-restructure/WAVE_GOVERNANCE.md) |
| Test strategy (4 tiers) | [phase3-restructure/TEST_STRATEGY.md](./phase3-restructure/TEST_STRATEGY.md) |
| RBAC (canonical) | [architecture/RBAC.md](./architecture/RBAC.md) |
| Environment matrix | [phase3-restructure/ENV_MATRIX.md](./phase3-restructure/ENV_MATRIX.md) |
| PRD | [phase3-restructure/PRD_PHASE3_MULTI_TENANT.md](./phase3-restructure/PRD_PHASE3_MULTI_TENANT.md) |
| Wave 6 cleanup | [phase3-restructure/WAVE6_PROGRESS.md](./phase3-restructure/WAVE6_PROGRESS.md) |

---

## Onboarding tutorials

Structured learning path (not operational runbooks):

- [knowledge-hub/](./knowledge-hub/README.md) — FastAPI, React, Alembic, multi-tenancy tutorials

---

## Historical archive

Pre-restructure delivery records:

- [archive/](archive/) — phase1, phase2, phase3, phase3.1 (read-only)

---

## Repo hygiene

Planning doc for folder restructure, dead-code removal, and doc consolidation:

- [CLEANUP_STAGE.md](./CLEANUP_STAGE.md)
