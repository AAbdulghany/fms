# Wave 3 Ticket Tracker — Assets Module

**Started:** 2026-06-06  
**Closed:** 2026-06-22  
**Branch:** `feature/phase-3-restructure/wave3`  
**Gate:** Wave 2 sign-off + Abdullah approval (see [WAVE1_WAVE2_SIGNOFF.md](WAVE1_WAVE2_SIGNOFF.md))  
**UAT observations:** [WAVE3_OBSERVATIONS.md](WAVE3_OBSERVATIONS.md) (18 items, all closed)  
**Baseline tests:** 160 backend pytest (post-RBAC); `npm run build` pass

---

## Parallel lane assignment

| Lane | Agent | Tickets | Status |
|------|-------|---------|--------|
| A Backend / schema | backend-engineer | NT-116, NT-120 | ✅ Done |
| B Frontend calendar | frontend-engineer | NT-117, NT-118, NT-119 | ✅ Done |
| C Feature gates | backend-engineer + frontend-engineer | NT-120 | ✅ Done |
| D QA + E2E | qa-engineer | NT-121 | ✅ Done |
| E UAT observations | frontend + backend + qa | OBS-DASH/COMP/AST/WO/USR (18) | ✅ Done |

---

## UAT observations (Wave 3 stretch)

Captured 2026-06-17 during maintenance-admin UAT. Full closure record: **[WAVE3_OBSERVATIONS.md](WAVE3_OBSERVATIONS.md)** · detailed gaps: [Knowledge Hub](../knowledge-hub/product/01_wave3_uat_observations.md).

| Bucket | OBS IDs | Count | Status |
|--------|---------|-------|--------|
| Dashboard | OBS-DASH-01 – 04 | 4 | ✅ All fixed |
| Companies | OBS-COMP-01 – 02 | 2 | ✅ All fixed |
| Assets | OBS-AST-01 – 08 | 8 | ✅ All fixed |
| Work orders | OBS-WO-01 | 1 | ✅ Fixed |
| Users | OBS-USR-01 | 1 | ✅ Fixed |
| **Total** | | **18** | **0 open** |

---

## Tickets

| Ticket | Title | Agent | Depends | Branch slug | Status | Tests |
|--------|-------|-------|---------|-------------|--------|-------|
| **NT-116** | AI maintenance schema placeholder + feature flag stub | backend-engineer | NT-102 | `NT-116-ai-schema-stub` | ✅ | `test_wave3_assets.py` (AI stub) |
| **NT-117** | Asset dashboard: quarterly maintenance calendar view | frontend-engineer | — | `NT-117-quarterly-calendar` | ✅ | E2E AST-01 |
| **NT-118** | Asset dashboard: yearly maintenance calendar view | frontend-engineer | NT-117 | `NT-118-yearly-calendar` | ✅ | E2E AST-02 |
| **NT-119** | Asset ↔ WO linkage panel on dashboard | frontend-engineer | NT-117 | `NT-119-asset-wo-panel` | ✅ | E2E AST-03 |
| **NT-120** | Enforce `assets` feature gate on routes + UI | BE + FE | NT-108 | `NT-120-assets-feature-gate` | ✅ | `test_wave3_assets.py` + AST-05 |
| **NT-121** | Asset module QA (AST-01–AST-06) | qa-engineer | NT-117–120 | `NT-121-asset-qa` | ✅ | 12/12 `test_wave3_assets.py` + E2E 5/6 |

---

## Acceptance criteria (summary)

### NT-116
- [x] `maintenance_schedules` / AI placeholder fields documented in ERD delta (if schema touch)
- [x] Feature flag key `ai_maintenance` in package matrix (stub, default off except enterprise)
- [x] No production AI calls; stub returns 501 or hidden UI

### NT-117–NT-119
- [x] Client admin sees calendar scoped to own assets/sites only
- [x] Company admin sees all tenant clients (filter by client company)
- [x] WO linkage panel lists open WOs for selected asset

### NT-120
- [x] Package without `assets` → 403 on asset API + nav hidden
- [x] Demo pitch package includes `assets` enabled

### NT-121
- [x] All AST-01–AST-06 in [WAVE3_E2E.md](WAVE3_E2E.md) automated or marked N/A with reason
- [x] Zero regression vs 160-test baseline

---

## Deliverables checklist

| Area | Expected paths | Status |
|------|----------------|--------|
| Backend | `assets.py` gates, schedule stubs, tests | ✅ |
| Frontend | `AssetsPage` calendar views, dashboard panels | ✅ |
| Tests | `backend/tests/test_wave3_assets.py` | ✅ 12/12 |
| E2E | `tests/e2e/wave3-assets.spec.ts` | ✅ 5 pass, 1 skipped (AST-04) |
| Docs | ERD delta if schema changes | ✅ `ERD_WAVE0.md` + AgDR |
| UAT | 18 observations closed | ✅ [WAVE3_OBSERVATIONS.md](WAVE3_OBSERVATIONS.md) |

---

## PR order (suggested)

```
NT-116 ─┬→ NT-120
NT-117 → NT-118 → NT-119 ─→ NT-121
         └──────────────────→ NT-121
```

1. NT-116 + NT-120 can start in parallel  
2. NT-117 before NT-118, NT-119  
3. NT-121 last (QA sweep)

---

## Test evidence (close)

```text
Backend wave3:  12/12 passed (test_wave3_assets.py)
Backend full:   212 passed (2026-06-22, uv run pytest -q)
Frontend:       npm run build — pass
E2E:            5 / 6 AST scenarios (AST-04 skipped — covered by backend test_assets_feature_gate_production)
```

---

## Next wave

Wave 4 (`feature/phase-3-restructure/wave4`) may open after [WAVE3_SIGNOFF.md](WAVE3_SIGNOFF.md) merge approval (Rex + Abdullah).
