# [Task] CLEAN-012: Split `CompanyDetailPage` (653) + `AssetDetailPage` (610)

**Labels:** `type:task` `area:frontend` `refactor` `wave:2D` · **Estimate:** L · **Depends on:** CLEAN-001, CLEAN-005 · **PR:** own PR (PR6). It may be split into two PRs, one per page  
**Tests:** [TC-CLEAN-012-*](../CLEANUP_TEST_CASES.md)

## Driver

Both pages repeat the WO-detail anti-pattern: profile, related lists, and several modal flows (provisioning, credentials, lifecycle) in one component. Applying the CLEAN-010 pattern twice more makes it the team convention.

## Approach

**CompanyDetailPage** (`features/companies/`):

- `useCompanyDetail(id)` hook
- sections: `CompanyProfileCard`, `CompanySitesList`, `CompanyActions`
- the existing modals (`CompanyEditModal`, `SiteProvisionModal`, `SiteAssignManagerModal`, `ProvisionCredentialsModal`) stay where they are; the page only wires them

**AssetDetailPage** (`features/assets/`):

- `useAssetDetail(id)` hook
- sections: `AssetProfileCard`, `AssetLifecycleSection` (wraps `AssetLifecycleBadge` + `AssetLifecycleTimeline`), `AssetWorkOrdersSection` (wraps `AssetWorkOrderPanel`)
- `AssetEditModal` is wired from the page

Same rules as CLEAN-010: characterize first, extract only, no logic edits.

## Acceptance criteria

- [ ] Each page ≤350 lines; no extracted file >300
- [ ] TC-CLEAN-012-01…03 component tests pass
- [ ] `wave3-assets.spec.ts` green on desktop + mobile
- [ ] Manual `company_admin` walk (TC-CLEAN-012-06) in AR + EN matches `main`

## Mentor note

Repeat a pattern until it's a convention. Feature folders own their hooks and sections, which lets several people (and agents) work in parallel without collisions.
