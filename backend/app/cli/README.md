# CLI entrypoints

Operational scripts invoked via `python -m app.<module>` or Docker migrate.

| Module | Location | Purpose | Invoked by |
|--------|----------|---------|------------|
| `docker_migrate.py` | `app/cli/` | Schema + seed on container start | Docker `migrate` service |
| `pitch_seed.py` | `app/cli/` | Pitch demo dataset | `SEED_MODULE=pitch` |
| `test_seed.py` | `app/cli/` | Dev/test dataset | default seed in dev compose |
| `seed_super.py` | `app/cli/` | Minimal super user | local dev |
| `seed.py` | `app/cli/` | Role-hierarchy users only | local dev |

Backward-compatible shims remain at `app/seed*.py` and `app/pitch_seed.py` for one release cycle.

Demo passwords are composed via `_demo_passwords.demo_password()` — suffix from `DEMO_PASSWORD_SUFFIX` (default `123`), not hardcoded literals.

| Module | Status |
|--------|--------|
| `report_template_sync_cli.py` | `app/cli/` | STD-INSP template sync | manual |
