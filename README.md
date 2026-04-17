# FMS (Facility Management System)

## Quick start

See **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** for how to run the backend and frontend, apply migrations, and seed a **super user only** (or the full demo seed).

- **Super user only (minimal):** `PYTHONPATH=backend` then `uv run python -m app.seed_super` (from repo root; see the guide for Windows `PYTHONPATH` syntax).
- **API:** `uvicorn` from the `backend` folder after `uv sync`.
- **UI:** `npm run dev` from the repo root.