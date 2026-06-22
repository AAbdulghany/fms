# How to run Orbit (local development)

> **Superseded by:** [guides/local-development.md](./guides/local-development.md)  
> This file remains as a short redirect. The guide above is kept in sync with the current toolchain (uv, Alembic, seeds, ports).

---

## Quick links

| Task | Guide |
|------|-------|
| Local dev (Vite + uvicorn) | [guides/local-development.md](./guides/local-development.md) |
| Docker pitch demo | [guides/demo-stack.md](./guides/demo-stack.md) |
| Tests | [guides/testing.md](./guides/testing.md) |
| Deploy demo / production | [guides/deployment.md](./guides/deployment.md) |
| All documentation | [README.md](./README.md) |

---

## Minimal local start

```powershell
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
uv sync
uv run alembic -c backend/alembic.ini upgrade head
$env:PYTHONPATH = "backend"; uv run python -m app.seed_super
cd backend; $env:PYTHONPATH = "."; uv run uvicorn app.main:app --reload --port 8000
# second terminal: npm install && npm run dev  →  http://localhost:5173
```

Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
