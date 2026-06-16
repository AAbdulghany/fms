# Environment Matrix — Wave 0 (NT-104)

| Variable | Values | Purpose |
|----------|--------|---------|
| `APP_ENV` | `development` \| `demo` \| `production` | License freeze bypass in dev/demo |
| `DATABASE_URL` | per environment | Separate DB per env (see AgDR) |

## Behavior matrix

| APP_ENV | License freeze | Feature gates | Typical database |
|---------|----------------|---------------|------------------|
| `development` | **Bypassed** | All open | `fms_dev` |
| `demo` | **Bypassed** | All open (pitch) | `fms_demo` |
| `production` | **Enforced** | Package-driven | `fms_prod` |

## Local defaults

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:5432/fms
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
uv run pytest tests/test_wave0_app_env.py -q
```

## Wave 2 follow-up

- `docker-compose.demo.yml` with `APP_ENV=demo` + `fms_demo` URL (NT-112)
