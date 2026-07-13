# AgDR: Phase 3.1 Demo Hosting

**Status:** Approved for Build  
**Author:** Hisham (Tech Lead)  
**Reviewer:** Tariq (Solution Architect)  
**Date:** 2026-06-06

## Target topology

```
User → Nginx/Caddy → Vite static + FastAPI API → Postgres
                              ↓
                         SMTP (optional)
```

## Decision

1. Extend `docker-compose-local.yml` with `api`, `web`, `migrate` services.
2. Add `deploy/` with `Dockerfile.api`, `Dockerfile.web`, `nginx.conf`.
3. Document Railway/Render deployment in `DEMO_DEPLOY.md`.
4. Seed demo tenant via existing `test_seed.py` on migrate.

## Environment variables

| Var | Purpose |
|-----|---------|
| DATABASE_URL | Postgres connection |
| JWT_SECRET | Auth signing |
| CORS_ORIGINS | Frontend origin |
| SMTP_* | Optional email |
| PUBLIC_APP_URL | QR label base URL |

## CI

GitHub Action: pytest + docker build (optional gate).

## Recommendation

**Railway** or **Render** for first external demo (Postgres addon, free tier).

## Out of scope

- Production HA, autoscaling, CDN — Phase 4+
