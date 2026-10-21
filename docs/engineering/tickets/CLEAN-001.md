# [Task] CLEAN-001: Repoint feature/shared imports off `@/components/*`

**Labels:** `type:task` `area:frontend` `wave:2B` `cleanup` · **Estimate:** S · **Depends on:** — · **PR:** PR2 (commit 1 of 5)  
**Plan:** [MOBILE_FIRST_CLEANUP_PLAN.md §3.1](../MOBILE_FIRST_CLEANUP_PLAN.md#31-legacy-mirror-layer) · **Tests:** TC-CLEAN-001-* in [CLEANUP_TEST_CASES.md](../CLEANUP_TEST_CASES.md)

## Driver

`src/components/*.tsx` are `@deprecated` re-export shims left over from the Phase 3 restructure. 16 files (36 import lines) still import through them, including `src/shared/components/Sidebar.tsx`, where `shared` reaches back into the legacy layer. Until these move, the shims can't be deleted.

## Scope

**In:** Rewrite each `@/components/<Name>` import to the shim's own target:

| Shim | Canonical path |
|------|----------------|
| EmptyState, FilterBar, LocationTree, OrbitLogo, StatsCard, UserRoleBadge, CategoryObservationsEditor | `@/shared/components/<Name>` |
| AssetEditModal, AssetImportModal, AssetLifecycleBadge, AssetLifecycleTimeline, AssetRegisterModal, AssetWorkOrderPanel, MaintenanceCalendar | `@/features/assets/components/<Name>` |
| CompanyCreateModal, CompanyEditModal, ProvisionCredentialsModal, SiteAssignManagerModal, SiteEditModal, SiteProvisionModal, SiteQrModal | `@/features/companies/components/<Name>` |
| InvoicePreviewModal | `@/features/invoices/components/InvoicePreviewModal` |
| WorkOrderRequestReviewModal | `@/features/work-orders/components/WorkOrderRequestReviewModal` |

Keep the same named/default export form the shim exposed (e.g. `SiteQrModal` file exports `SiteQRModal`).

**Out:** Deleting shims (CLEAN-003/004). Any logic or JSX change.

## Acceptance criteria

- [ ] `rg -n "from ['\"]@/components/" src --glob '!src/components/**'` returns 0 matches
- [ ] `Sidebar.tsx` imports `OrbitLogo` from `@/shared/components/OrbitLogo`
- [ ] `npm run build` green
- [ ] Existing Playwright suite green on the demo stack (desktop project)
- [ ] Diff contains import-line changes only (reviewer can verify with `git diff -U0 | rg '^[+-]' | rg -v import`)

## Mentor note

Learn how Vite/TS path aliases resolve, and why a migration leaves re-export shims behind. The compiler is your proof that a mechanical refactor is safe.
