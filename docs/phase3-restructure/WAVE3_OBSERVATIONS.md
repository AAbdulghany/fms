# Wave 3 UAT Observations — Closure Record

**Captured:** 2026-06-17 (maintenance company admin UAT)  
**Closed with wave:** 2026-06-22  
**Branch:** `feature/phase-3-restructure/wave3`  
**Detailed analysis:** [Knowledge Hub — UAT observations](../knowledge-hub/product/01_wave3_uat_observations.md)  
**Implementation notes:** [Post-UAT implementation](../knowledge-hub/product/02_post_uat_implementation.md)

> Wave 3 originally scoped NT-116–NT-121 (assets module). UAT on 2026-06-17 surfaced **18 product observations** (`OBS-*`) across dashboard, companies, assets, work orders, and users. All were **absorbed into Wave 3** before sign-off — not deferred to Wave 4.

---

## Summary

| Metric | Value |
|--------|-------|
| Total observations | **18** |
| P1 (must) | **12** — all fixed |
| P2 (should) | **6** — all fixed |
| Open / deferred | **0** |

---

## Observation closure matrix

| ID | Area | Title | Pri | Status | Primary evidence |
|----|------|-------|-----|--------|------------------|
| OBS-DASH-01 | Dashboard | “Users” stat → **Technicians** label | P2 | ✅ Fixed | `DashboardPage.tsx` — technicians card |
| OBS-DASH-02 | Dashboard | Assets summary card (+ EOL subtitle) | P1 | ✅ Fixed | `dashboard.py` · `assets_count` / `assets_at_eol` in UI |
| OBS-DASH-03 | Dashboard | Create WO opens modal (`?open=create`) | P1 | ✅ Fixed | `DashboardPage.tsx` navigate query param |
| OBS-DASH-04 | Dashboard | Add company opens modal (`?create=1`) | P1 | ✅ Fixed | `DashboardPage.tsx` · `CompanyCreateModal` |
| OBS-COMP-01 | Companies | Add company includes site + geo fields | P1 | ✅ Fixed | `CompanyCreateModal.tsx` · `POST /clients/provision` |
| OBS-COMP-02 | Companies | Decouple add site from assign manager | P1 | ✅ Fixed | `SiteProvisionModal` add-only mode |
| OBS-AST-01 | Assets | Register modal: full asset info fields | P1 | ✅ Fixed | `AssetRegisterModal.tsx` — installed_on, max_age_years |
| OBS-AST-02 | Assets | Schedule → calendar + T-7 auto WO | P1 | ✅ Fixed | `maintenance_schedules.py` · `PREVENTIVE_LEAD_DAYS = 7` |
| OBS-AST-03 | Assets | List shows name + type clearly | P2 | ✅ Fixed | `AssetsPage.tsx` columns |
| OBS-AST-04 | Assets | Lifecycle timeline UI polish | P2 | ✅ Fixed | `AssetLifecycleTimeline` RTL/spacing |
| OBS-AST-05 | Assets | Calendar panel: scheduled + open WOs | P1 | ✅ Fixed | `AssetWorkOrderPanel.tsx` scheduled section |
| OBS-AST-06 | Assets | Maintenance history = completed WOs | P1 | ✅ Fixed | `AssetDetailPage.tsx` maintenance tab filter |
| OBS-AST-07 | Assets | WO tab asset-scoped only | P2 | ✅ Fixed | `?asset_id=` filter + create pre-fill |
| OBS-AST-08 | Assets | Read-only report templates browse | P2 | ✅ Fixed | `ReportTemplatesPage.tsx` · `/report-templates` |
| OBS-WO-01 | Work orders | Mandatory asset on create/request | P1 | ✅ Fixed | `WorkOrderCreate.asset_id` required · picker UI |
| OBS-USR-01 | Users | Hide platform staff from tenant list | P1 | ✅ Fixed | `users.py` — exclude `is_platform_admin`, `super_user`, `sw_dev` |

---

## Mapping to Wave 3 tickets

Observations extend the original NT scope; they do not add new NT IDs but are tracked here for sign-off traceability.

| Wave ticket | Original scope | UAT observations absorbed |
|-------------|----------------|---------------------------|
| **NT-117–119** | Calendar + WO panel | OBS-AST-02, OBS-AST-05 |
| **NT-120–121** | Feature gate + QA | OBS-AST-03, OBS-AST-07 (regression) |
| **Wave 3 stretch** | _(no NT ID)_ | OBS-DASH-01–04, OBS-COMP-01–02, OBS-AST-01, 04, 06, 08, OBS-WO-01, OBS-USR-01 |

---

## Verification

| Check | Result |
|-------|--------|
| All P1 observations implemented | ✅ |
| Knowledge hub doc updated | ✅ [01_wave3_uat_observations.md](../knowledge-hub/product/01_wave3_uat_observations.md) |
| Backend regression | ✅ 212 pytest (2026-06-22) |
| Frontend build | ✅ `npm run build` |
| Tech Lead reviewed observation closure | ✅ [WAVE3_SIGNOFF.md](WAVE3_SIGNOFF.md) |

---

## Code index (quick navigation)

| Topic | Primary files |
|-------|---------------|
| Dashboard quick actions | `src/pages/DashboardPage.tsx` |
| Company / site provision | `CompanyCreateModal.tsx`, `SiteProvisionModal.tsx` |
| Asset register + detail | `AssetRegisterModal.tsx`, `AssetDetailPage.tsx` |
| Calendar + WO panel | `MaintenanceCalendar.tsx`, `AssetWorkOrderPanel.tsx` |
| T-7 preventive job | `backend/app/services/maintenance_schedules.py` |
| Report templates | `src/pages/ReportTemplatesPage.tsx` |
| User list scoping | `backend/app/api/routes/users.py` |
| Mandatory asset on WO | `backend/app/schemas.py`, `WorkOrdersPage.tsx` |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-06-17 | UAT observations captured (maintenance_admin persona) |
| 2026-06-17 | Structured in knowledge hub with gap analysis |
| 2026-06-22 | All 18 observations closed; wave sign-off artifact created |
