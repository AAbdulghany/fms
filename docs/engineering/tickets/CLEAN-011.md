# [Task] CLEAN-011: Split `WorkOrdersPage` (756 → ≤350 lines)

**Labels:** `type:task` `area:frontend` `refactor` `wave:2D` · **Estimate:** M · **Depends on:** CLEAN-005, CLEAN-010 (reuses `features/work-orders/lib` + hooks folders) · **PR:** own PR (PR5)  
**Tests:** [TC-CLEAN-011-*](../CLEANUP_TEST_CASES.md)

## Driver

The WO list mixes filtering, list rendering, create, and request-review flows in 756 lines. The list is the second most-used phone screen after detail.

## Approach

1. Characterize: snapshot the query string the current code builds for a matrix of filter inputs.
2. Extract a pure `buildWorkOrderQuery(filters)` into `features/work-orders/lib/workOrderQuery.ts`. Make the URL search params the single source of truth for filters.
3. Extract a `useWorkOrderList(filters)` hook (fetch, pagination, reload).
4. Components in `features/work-orders/components/list/`: `WorkOrderListFilters` (wraps shared `FilterBar`), `WorkOrderTable` (desktop), `WorkOrderCardList` (stub for mobile; real mobile styling is a follow-up), `WorkOrderCreateDialog`. The request-review modal stays in `features/work-orders/components/`.

## Acceptance criteria

- [ ] Page ≤350 lines; no extracted file >300
- [ ] TC-CLEAN-011-01…04 pass
- [ ] Filters survive reload and back-navigation via the URL
- [ ] Work-order e2e specs green on desktop + mobile projects

## Mentor note

URL state as the single source of truth for filters. Pure mapping functions are the cheapest code to test. Each small refactor makes the next feature cheaper.
