# [Task] CLEAN-010: Split `WorkOrderDetailPage` (1474 → ≤400 lines)

**Labels:** `type:task` `area:frontend` `refactor` `wave:2D` · **Estimate:** L · **Depends on:** CLEAN-001, CLEAN-005 · **PR:** own PR (PR4), after the shell  
**Tests:** [TC-CLEAN-010-*](../CLEANUP_TEST_CASES.md)

## Driver

`features/work-orders/pages/WorkOrderDetailPage.tsx` is the technician's primary screen and the hardest file in the repo to change safely:

- 1474 lines and 26 `useState` hooks
- about 15 inline `apiFetch` calls
- 3 inline modals (report, hold, cancel)
- inline status rules (`ALLOWED_TRANSITIONS`, `REPORT_UNLOCKED_STATUSES`, `statusAllowsReport`)
- 6 unrelated sections in one component

Mobile layout work on this page is blocked until it's decomposed.

## Approach (extract only, no logic edits in this PR)

1. **Characterize first:** snapshot tests for `ALLOWED_TRANSITIONS` and `statusAllowsReport` against the current module.
2. **Pure rules:** move the constants and `statusAllowsReport` into `features/work-orders/lib/workOrderRules.ts`.
3. **Data hooks** in `features/work-orders/hooks/`:
   - `useWorkOrderDetail(id)`: load, parallel fetches, and `reload`
   - `useWorkOrderReport(wo)`: template resolution, draft save/submit/approve
   - `useWorkOrderDocuments(id)`: upload/complete/list/download
4. **Sections** in `features/work-orders/components/detail/`: `WorkOrderContextPanel`, `WorkOrderStatusActions`, `WorkOrderReportSection`, `WorkOrderReportModal`, `WorkOrderCommentsDocuments`, `WorkOrderHistory`, `HoldReasonModal`, `CancelReasonModal`, `InvoiceAction`.
5. The page becomes composition: route param → hooks → sections, plus role gating.

## Acceptance criteria

- [ ] Page ≤400 lines; no extracted file >300 lines; `useState` in the page ≤8
- [ ] Unit tests: TC-CLEAN-010-01, 02. Component tests: TC-CLEAN-010-03…07
- [ ] `wave4-workflows.spec.ts` and `wave4-golden-path.spec.ts` pass **without selector changes** (adding `data-testid` is allowed)
- [ ] Manual AR + EN walk of the full lifecycle (TC-CLEAN-010-10) matches `main`
- [ ] No new API calls and no changed request payloads (reviewer compares the Network tab on one WO)

## Mentor note

Recognize a god component. Extract in this order: pure logic, then data hooks, then presentational sections. Write characterization tests before moving code. Incremental extraction, never a rewrite.
