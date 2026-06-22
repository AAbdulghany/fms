# Demo Deployment Guide

**Target:** Railway or Render (first external demo)  
**Stack:** FastAPI + React/Vite + PostgreSQL

---

## Local full stack

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Services:

| Service | Port | Description |
|---------|------|-------------|
| web | 8080 | Nginx serving Vite build + API proxy |
| api | 8000 | FastAPI (internal) |
| db | 5432 | PostgreSQL |
| migrate | — | Runs seed on first start |

Demo logins (after seed):

| Email | Password | Role |
|-------|----------|------|
| admin@demo.com | admin123 | company_admin |
| client@demo.com | client123 | client_admin |

---

## Railway deployment

1. Create project → add **PostgreSQL** plugin
2. Add service from repo → set **Dockerfile** `deploy/Dockerfile.api`
3. Set env vars: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS=https://your-app.up.railway.app`
4. Add static service or use combined nginx image from `deploy/Dockerfile.web`
5. Run migrate: `docker compose run migrate` or Railway one-off command:
   `python -m app.test_seed`

---

## Render deployment

1. **Web Service** → Docker, `deploy/Dockerfile.api`, health check `/health`
2. **PostgreSQL** → link `DATABASE_URL`
3. **Static Site** or nginx container for frontend
4. Set `PUBLIC_APP_URL` for asset QR labels

---

## Environment reference

See `backend/.env.example` for full list.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors | Set `CORS_ORIGINS` to exact frontend URL |
| WS notifications fail | Ensure proxy passes `/api/v1/notifications/ws` |
| Empty DB | Run seed script after migrate |
