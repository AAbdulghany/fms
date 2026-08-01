# CLI entrypoints

Operational scripts invoked via `python -m app.<module>` or Docker migrate.

| Module | Location | Purpose | Invoked by |
|--------|----------|---------|------------|
| `docker_migrate.py` | `app/cli/` | Schema + seed on container start | Docker `migrate` service |
| `pitch_seed.py` | `app/cli/` | Rich pitch demo dataset (users + clients + assets + ~50 WOs) | `SEED_MODULE=pitch` |
| `test_seed.py` | `app/cli/` | Dev/CI dataset — users only, comprehensive role coverage | default seed in dev compose |
| `seed_super.py` | `app/cli/` | Minimal super user | local dev |
| `seed.py` | `app/cli/` | Role-hierarchy users only | local dev |
| `_seed_lib.py` | `app/cli/` | Shared seed utilities (`truncate_tenant_data`, `UserSeedSpec`, `create_seed_user`) | imported by pitch_seed + test_seed |

Backward-compatible shims remain at `app/seed*.py` and `app/pitch_seed.py` for one release cycle.

Demo passwords are composed via `_demo_passwords.demo_password()` — suffix from `DEMO_PASSWORD_SUFFIX` (default `123`), not hardcoded literals.

## Seed profiles

| `SEED_MODULE` | Dataset | Use case |
|--------------|---------|----------|
| `test` (default) | 1 tenant, 8 users (all roles), no clients/assets/WOs | CI, unit tests, local dev |
| `pitch` | 1 tenant, 7 users, 2 clients, 3 sites, ~15 assets, ~50 WOs, 2 draft invoices | Sales demos, E2E tests |

## Shared library (`_seed_lib.py`)

- `truncate_tenant_data(db)` — PostgreSQL TRUNCATE CASCADE or SQLite ordered DELETE; safe to call before every seed run.
- `UserSeedSpec` — typed dataclass for user seed definitions.
- `create_seed_user(db, tenant_id, spec)` — insert a user from a spec; caller must flush/commit.

| Module | Status |
|--------|--------|
| `report_template_sync_cli.py` | `app/cli/` | STD-INSP template sync | manual |
