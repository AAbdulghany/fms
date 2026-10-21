# Environment Matrix

| Variable | Values | Purpose |
|----------|--------|---------|
| `APP_ENV` | `development` \| `pilot` \| `production` (`demo` still maps to `pilot`; other values are rejected) | License freeze bypass in non-production |
| `DATABASE_URL` | per environment | Separate DB per env |

Canonical guide: [environments.md](../guides/environments.md) · Reorg plan: [ENV_REORG_PLAN.md](../engineering/ENV_REORG_PLAN.md)

## Behavior matrix

| APP_ENV | License freeze | Feature gates | Typical database | Compose |
|---------|----------------|---------------|------------------|---------|
| `development` | **Bypassed** | All open | `fms_local` | `docker-compose-local.yml` |
| `pilot` | **Bypassed** | All open (pilot seed) | `fms_pilot` | `docker-compose-pilot.yml` |
| `production` | **Enforced** | Package-driven | `fms_prod` | `docker-compose-prod.yml` |

## Local defaults

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:9432/fms_local
```

## Docker Compose

Set on `api` service:

```yaml
environment:
  APP_ENV: ${APP_ENV:-development}
```

## Verification

```bash
cd backend
pytest tests/domains/platform/test_app_env.py -q
```
