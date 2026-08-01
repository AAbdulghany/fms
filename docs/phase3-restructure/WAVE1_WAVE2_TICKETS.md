# Wave 1 + Wave 2 Ticket Tracker

**Started:** 2026-06-06  
**Closed:** 2026-06-06  
**Gate:** NT-105–NT-115 tests green ✅ (153 total backend tests)

## Parallel lane assignment


| Lane          | Agent             | Tickets                         | Status |
| ------------- | ----------------- | ------------------------------- | ------ |
| A Platform BE | backend-engineer  | NT-105, NT-106, NT-107, NT-108 | ✅ Done |
| B Platform FE | frontend-engineer | NT-109, NT-110                  | ✅ Done |
| C QA          | qa-engineer       | NT-111                          | ✅ Done |
| D Demo BE     | backend-engineer  | NT-113, NT-114                  | ✅ Done |
| E Demo Infra  | platform-engineer | NT-112, NT-115                  | ✅ Done |


---

## Wave 1 — Platform & licensing


| Ticket | Agent             | Status | Tests                                | GitHub |
| ------ | ----------------- | ------ | ------------------------------------ | ------ |
| NT-105 | backend-engineer  | ✅ Done | `test_wave1_platform.py`             | #7     |
| NT-106 | backend-engineer  | ✅ Done | ↑ license PUT                        | #8     |
| NT-107 | backend-engineer  | ✅ Done | login + refresh freeze               | #10    |
| NT-108 | backend-engineer  | ✅ Done | `require_feature` on assets/invoices | #12    |
| NT-109 | frontend-engineer | ✅ Done | `npm run build`                      | #14    |
| NT-110 | frontend-engineer | ✅ Done | SubscriptionPage → platform APIs     | #16    |
| NT-111 | qa-engineer       | ✅ Done | 7 wave1 tests                        | #9     |


### Backend deliverables (Wave 1)

- `backend/app/api/routes/platform.py` — packages CRUD, tenant license, tenant list, demo reset
- `backend/app/api/deps.py` — `require_platform_admin`, `require_feature`
- `backend/app/services/subscription.py` — `assign_tenant_subscription`, table-first `update_subscription`
- Feature gates on `assets`, `invoices`, `csv_import` routes
- Login + refresh block suspended tenants in production

### Frontend deliverables (Wave 1)

- `src/pages/PlatformPackagesPage.tsx` — package manager (`/platform/packages`)
- `src/pages/SubscriptionPage.tsx` — tenant license panel via `/platform/tenants` + license PUT
- `src/components/Sidebar.tsx` — platform-admin-only nav items
- `UserPublic.is_platform_admin` exposed to UI

---

## Wave 2 — Demo environment


| Ticket | Agent             | Status | Tests                     | GitHub |
| ------ | ----------------- | ------ | ------------------------- | ------ |
| NT-112 | platform-engineer | ✅ Done | `docker-compose-demo.yml` | #11    |
| NT-113 | backend-engineer  | ✅ Done | `test_wave2_demo.py` seed | #13    |
| NT-114 | backend-engineer  | ✅ Done | demo reset endpoint       | #15    |
| NT-115 | platform-engineer | ✅ Done | `DEMO_DEPLOY.md`          | #17    |


### Demo deliverables (Wave 2)

- `docker-compose-demo.yml` — `fms_demo` DB, `APP_ENV=demo`, pitch seed on migrate
- `backend/app/pitch_seed.py` — 1 tenant, 2 clients, 4 assets, 3 WOs, 2 invoices
- `POST /platform/demo/reset` — demo env only
- `docs/phase3-restructure/DEMO_DEPLOY.md`

---

## Test evidence

```text
153 passed (backend)
npm run build — OK
```

Baseline was 142 (Wave 0). Net +11 tests (`test_wave1_platform`, `test_wave2_demo`).

---

## Next wave

Wave 3 (NT-116+) — Assets module. Do not start until Abdullah sign-off on this tracker.