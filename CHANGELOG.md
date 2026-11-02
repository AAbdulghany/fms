# Changelog

Notable changes to the **Orbit FMS pilot** (`https://pilot.orbittech.co`).

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The pilot
deploys from `main` on every push, so entries are grouped by date rather than by
release tag.

## Severity tags

Every entry starts with a tag. Use it to decide whether an operator needs to act
before or after a deploy.

| Tag | Meaning | Operator action |
|-----|---------|-----------------|
| **Major** | Schema migration, API/behaviour change, or deploy-path change. Can break clients or existing data. | Review the migration and the deploy before merging. |
| **Minor** | New capability or user-visible improvement. Backwards compatible. | None; verify the feature after deploy. |
| **Patch** | Fix, CI, docs, or internal change with no client-visible behaviour change. | None. |

When adding an entry, put it under `## [Unreleased]` in the matching
`Added` / `Changed` / `Fixed` / `Removed` section, then move it into a dated
section when it is deployed.

## [Unreleased]

### Fixed

- **Patch** — Pilot CD: the public health check no longer turns a Cloudflare 403
  into a 60-second timeout (`exit 124`). It now makes at most three short
  attempts, reports `BLOCKED` vs `INCONCLUSIVE` as a warning annotation, and
  always exits 0. The SSH-local health check remains the deploy gate.
  ([deploy-orbit-pilot.yml](.github/workflows/deploy-orbit-pilot.yml))

## [2026-11-02] — Pilot live on `main`

### Added

- **Major** — Always-on pilot stack backed by Supabase Postgres
  (`docker-compose-pilot-supabase.yml` + `deploy/pilot/docker-compose.live-supabase.yml`).
  No local database container on the VM; migrations and seed run against
  `DATABASE_URL_MIGRATE`.
- **Major** — Continuous deployment from `main` to the pilot VM, replacing the
  previous `pilot/live`-only path. Production cutover stays a separate step.
- **Minor** — Platform portal: maintenance-company provisioning with a copyable
  credentials modal, tenant soft-delete, and package/trial edits.
- **Minor** — `SEED_MODULE=super` seed profile for a super-user-only pilot.
- **Minor** — `deploy/pilot/smoke-pilot.sh` smoke test (health, register company,
  company-admin login).
- **Minor** — RBAC: users invited as `sw_dev` / `super_user` now receive
  `is_platform_admin`, so `/platform` routes accept them.

### Changed

- **Major** — Environment reorg: the former "demo" stack becomes "pilot"
  (`fms_pilot`, `APP_ENV=pilot`, `pilot_seed`). `demo` is still accepted and maps
  to `pilot` for backwards compatibility.
- **Minor** — Pilot docs point at `main` as the deploy branch; the Supabase setup
  notes are the canonical always-on path.

### Fixed

- **Patch** — CD checkout fetches all remote heads, so a single-branch clone can
  check out the deploy branch.
- **Patch** — Removed pipe characters from the SSH deploy script; `appleboy/drone-ssh`
  mangled them into a bash syntax error.
- **Patch** — Deploy directory uses the non-secret `PILOT_PATH` variable instead
  of a secret, which GitHub was delivering as a mangled Windows path.

## Earlier history

Before the pilot stack existed, changes are recorded in the git history:
`git log --oneline -- docs/guides/pilot-stack.md`.
