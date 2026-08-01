# AgDR: Alembic vs runtime `schema_ensure`

**Status:** Accepted  
**Date:** 2026-06-22  
**Wave:** 6 cleanup (NT-CLEAN-17)  
**Owner:** solution-architect + backend-engineer

---

## Context

The backend uses **two** schema mutation paths:

1. **Alembic** — versioned migrations under `backend/migrations/versions/`
2. **`schema_ensure.py`** — idempotent DDL on every API startup and in `docker_migrate`

This dual path existed to support long-lived Docker volumes and demo deploys without forcing full rebuilds when columns were added outside Alembic.

---

## Decision

| Layer | Responsibility |
|-------|----------------|
| **Alembic** | **Source of truth** for all new schema changes. Every PR that alters tables/columns must include a migration version. |
| **`schema_ensure`** | **Legacy safety net only** — adds columns/tables that pre-date strict Alembic discipline on existing volumes. No new business logic. |
| **New changes** | Must **not** be added to `schema_ensure` without an AgDR amendment. |

---

## Current `schema_ensure` scope (frozen)

- Create missing tables: `notifications`, subscription platform tables
- Add columns if absent: `users.username`, `clients.status`, `maintenance_schedules.ai_meta_json`, `assets.label_code`

When all environments have run Alembic through the migrations that cover these columns, `schema_ensure` entries may be removed in a follow-up migration-only PR.

---

## Consequences

- **Positive:** Existing demo DB volumes keep working; CI uses SQLite in-memory (Alembic + ensure both noop-safe).
- **Negative:** Drift risk if Alembic and ensure diverge — mitigated by this freeze + code review gate.
- **Operational:** `docker_migrate` runs Alembic `upgrade head` **then** `ensure_schema` **then** seed.

---

## Compliance

- Migration gate hook: schema PRs require migration ticket (existing ApexYard workflow).
- Tests: `test_wave0_migration.py`, `test_wave0_schema.py`

---

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Remove `schema_ensure` immediately | Breaks old local/demo volumes without manual DDL |
| Ensure-only (no Alembic) | No version history, poor CI/production discipline |
| Expand ensure for every change | Duplicates Alembic, untraceable drift |

---

## References

- `backend/app/schema_ensure.py`
- `backend/app/cli/docker_migrate.py`
- [ENV_MATRIX.md](../phase3-restructure/ENV_MATRIX.md)
