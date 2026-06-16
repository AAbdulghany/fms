# RBAC — Phase 3 role model

Three customer tiers map to distinct role sets. Platform staff require `is_platform_admin=true`.

## Software company (platform)

| Role | Capabilities |
|------|----------------|
| **super_user** | Full platform: provision maintenance companies (tenants), assign subscriptions, add end clients and sub-accounts, remove members |
| **sw_dev** | Same platform UI/API as super_user **except** cannot deactivate/remove members (customer support) |

**UI:** Maintenance Companies page (`/platform/maintenance-companies`) lists tenants first with nested end clients, search/filter, and provision form.

## Maintenance companies (tenants)

| Role | Capabilities |
|------|----------------|
| **company_admin** | Add staff: company engineers, technicians, client admins, site managers. Created when platform provisions tenant. |
| **company_engineer** | Same operational access as company_admin (assets, work orders, clients, users list) but **cannot** add peer engineers or company admins |

## End clients (maintenance company's customers)

| Role | Capabilities |
|------|----------------|
| **client_admin** | Assets, locations, workflows per location, tenant-scoped client data |

## Legacy

- **super_admin** — tenant-level god role (pre–multi-tenant). Platform staff should use **super_user**. Migration script maps `is_platform_admin` + `super_admin` → `super_user`.

## Migrate existing databases

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg2://fms:fms@localhost:5432/fms_demo"
python -m scripts.migrate_roles
```

Docker demo migrate runs this automatically after seed.

## Demo logins

See [DEMO_QUICKSTART.md](./DEMO_QUICKSTART.md).
