# How to run Orbit (local development)

> **Superseded by:** [guides/local-development.md](./guides/local-development.md)  
> This file remains as a short redirect. The guide above is kept in sync with the current toolchain (uv, Alembic, seeds, ports).

---

## Quick links

| Task | Guide |
|------|-------|
| Local dev (Vite + uvicorn) | [guides/local-development.md](./guides/local-development.md) |
| Environments (dev / pilot / production) | [guides/environments.md](./guides/environments.md) |
| Docker pilot stack | [guides/pilot-stack.md](./guides/pilot-stack.md) |
| Tests | [guides/testing.md](./guides/testing.md) |
| Deploy pilot / production | [guides/deployment.md](./guides/deployment.md) |
| All documentation | [README.md](./README.md) |

---

## Minimal local start

```powershell
cd E:\03Workset\fms
docker compose -f docker-compose-local.yml -f docker-compose-hybrid.yml up -d
uv sync
uv run alembic -c backend/alembic.ini upgrade head
# Clean Program A seed (1 hospital client + roles):
cd backend; $env:PYTHONPATH = "."; ..\.venv\Scripts\python.exe -m app.cli.clean_dev_seed
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# second terminal (repo root): npm install && npm run dev  →  http://127.0.0.1:5173
# Login: admin@demo.com / admin123
```

Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
