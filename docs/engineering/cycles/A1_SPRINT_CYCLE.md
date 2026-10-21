# A1 sprint cycle — Verticals and Asset Types

**Program:** Orbit Program A, slice A1  
**Date opened:** 2026-10-22  
**Status:** Implementation in progress — BE unit suite green (41/41); FE wired  
**Tickets:** [#28](https://github.com/AAbdulghany/fms/issues/28) BE · [#29](https://github.com/AAbdulghany/fms/issues/29) FE · [#30](https://github.com/AAbdulghany/fms/issues/30) QA  
**Tech Lead:** Hisham  
**Design:** [A1_ASSET_TYPES_TECH_DESIGN.md](../designs/A1_ASSET_TYPES_TECH_DESIGN.md)  
**PRD:** [PRD_A1_VERTICALS_ASSET_TYPES.md](../../product/PRD_A1_VERTICALS_ASSET_TYPES.md)  
**UX:** [UX_A1_ASSET_TYPE_FLOWS.md](../../product/UX_A1_ASSET_TYPE_FLOWS.md)  
**Decision:** [AgDR-A1-asset-type-copy-on-adopt.md](../AgDR-A1-asset-type-copy-on-adopt.md)  
**Schema policy:** [AgDR-SCHEMA-ENSURE](../../decisions/AgDR-SCHEMA-ENSURE.md) (Alembic only)

---

## 1. Description

The cycle replaces free-text asset `category` and client `activity_type` with structured data:

- A platform **vertical** catalog (hospital, hotel, office, retail, industrial, education, other).
- A platform **asset type catalog**, tagged by vertical, that carries lifecycle, criticality, and schedule defaults.
- A tenant **asset type library**. Tenants adopt catalog entries by copy and can add custom types. The backfill creates legacy types from existing categories.
- `assets.asset_type_id` and `clients.vertical_id`, linked by an expand → backfill → dual-write migration. `assets.category` stays as a mirror of the type code, so report observations, labels, and filters keep working.
- The register modal gets an asset type picker. The picker recommends types for the client's vertical and pre-fills defaults.

**Out of scope:** contract migration, catalog CRUD UI, "refresh from catalog", per-type custom attributes, legacy-to-catalog merge tool.

### PR packing

| # | PR | Depends on | Ticket |
|---|----|-----------|--------|
| 1 | BE: models, Alembic expand migration, catalog seed, `/verticals`, `/asset-type-catalog`, `/asset-types`, asset and client endpoint changes | — | A1-BE |
| 2 | BE: backfill CLI and `docker_migrate` wiring | 1 | A1-BE (same ticket, second PR) or the migration ticket |
| 3 | FE: register and edit modals, company modals, `AssetTypesPage`, i18n, nav | 1 | A1-FE |
| 4 | Tests: Playwright e2e and the seed extension for e2e | 1, 3 | A1-TEST |

---

## 2. Unit tests (backend, pytest, SQLite in-memory)

New folder: `backend/tests/domains/asset_types/`. Existing suites are extended where noted.

### 2.1 Catalog seed — `test_asset_type_catalog.py`

| ID | Test |
|----|------|
| U-CAT-01 | `ensure_vertical_catalog` creates 7 verticals and every seed template with vertical tags. |
| U-CAT-02 | A second run is a no-op: same row counts, `version` unchanged. |
| U-CAT-03 | A changed seed field increments the template `version` and updates the field. |
| U-CAT-04 | A template removed from the seed becomes `is_active=false` and is not deleted. |
| U-CAT-05 | Every template's `default_frequency` is a key of `FREQUENCY_DAYS`, and every `default_criticality` is a valid `AssetCriticality`. |
| U-CAT-06 | Every template has non-empty `name_en` and `name_ar`. |

### 2.2 Adoption service — `test_asset_type_adopt.py`

| ID | Test |
|----|------|
| U-ADP-01 | Adopting N templates creates N `asset_types` rows with `origin=catalog`, the copied defaults, the copied vertical tags, and `source_template_id`/`source_version` set. |
| U-ADP-02 | Adopting the same template again returns `skipped[reason=already_adopted]` and creates no new row (I3). |
| U-ADP-03 | Duplicate IDs in one request are de-duplicated. |
| U-ADP-04 | An existing legacy type whose code matches the template code case-insensitively is merged: provenance is set, only the NULL defaults are filled, the tenant names are unchanged, and the response says `skipped[reason=merged_with_existing_code]`. |
| U-ADP-05 | `default_report_template_id` resolves to the tenant's `STD-INSP`. Another tenant's `STD-INSP` is never selected. |
| U-ADP-06 | An inactive or unknown template ID returns `400 INVALID_TEMPLATE`, and the whole request rolls back. |
| U-ADP-07 | Adoption writes one audit row (`adopt_asset_types`) with created and skipped counts. |
| U-ADP-08 | A later catalog edit does not change an adopted tenant row (copy semantics; AgDR). |

### 2.3 Asset type CRUD — `test_asset_types_api.py`

| ID | Test |
|----|------|
| U-AT-01 | `POST /asset-types` creates a custom type (`origin=custom`) with its vertical tags. |
| U-AT-02 | A duplicate code, including a case-insensitive duplicate, returns `400 ASSET_TYPE_CODE_CONFLICT`. |
| U-AT-03 | A code that fails the pattern (leading space, `/`, longer than 64 characters) returns 422. |
| U-AT-04 | `PATCH` with `code` returns `400 ASSET_TYPE_CODE_IMMUTABLE`. |
| U-AT-05 | `PATCH` updates the names, defaults, and vertical tags, and writes an audit row. |
| U-AT-06 | `PATCH is_active=false` archives the type. `GET /asset-types` hides it. `include_inactive=true` shows it. |
| U-AT-07 | `GET /asset-types?client_id=X`: types tagged with X's vertical, plus untagged (universal) types, have `recommended=true` and sort first. |
| U-AT-08 | A `client_admin` who passes another client's `client_id` gets 403. |
| U-AT-09 | The `technician` and `site_manager` roles get 403 on POST, PATCH, and adopt, and 200 on GET. |
| U-AT-10 | A `default_report_template_id` from another tenant returns `400 INVALID_REPORT_TEMPLATE`. |
| U-AT-11 | `GET /asset-types/{id}` returns an accurate `asset_count`. |

### 2.4 Asset endpoints — extend `tests/domains/assets/test_assets_module.py`

| ID | Test |
|----|------|
| U-AS-01 | `POST /assets` with `asset_type_id` sets `category = type.code` (I1) and returns the `asset_type` reference. |
| U-AS-02 | Type defaults fill the `None` body fields (`max_age_years`, `max_repair_count`, `criticality`). Explicit body values win. |
| U-AS-03 | A type from another tenant returns `400 INVALID_ASSET_TYPE`. |
| U-AS-04 | An archived type returns `400 ASSET_TYPE_ARCHIVED`. |
| U-AS-05 | `asset_type_id` together with a different non-default `category` returns `400 ASSET_TYPE_CATEGORY_MISMATCH`. |
| U-AS-06 | A legacy payload (`category` only) whose code matches an existing type gets linked. With no match, `asset_type_id` stays NULL and the endpoint creates no type. |
| U-AS-07 | The label code still uses the category slug (`SITE-HVAC-001` format unchanged). |
| U-AS-08 | The server never creates a schedule from the type defaults. A schedule exists only when `schedule` is in the body. |
| U-AS-09 | `PATCH asset_type_id` updates `category` and leaves `label_code` unchanged. The audit row holds the before and after values. |
| U-AS-10 | `PATCH category` alone on a typed asset with a different value returns `400 ASSET_TYPE_CATEGORY_MISMATCH`. |
| U-AS-11 | `GET /assets?asset_type_id=` filters. `?category=` still filters. |
| U-AS-12 | The `GET /assets` query count is constant for 1 and for 50 assets (no N+1 from `asset_type`). |

### 2.5 Clients and verticals — extend `tests/domains/clients/test_provisioning.py`

| ID | Test |
|----|------|
| U-CL-01 | `GET /verticals` returns the 7 active verticals in `sort_order`, for any authenticated role. |
| U-CL-02 | Provisioning with `vertical_code=hospital` sets `vertical_id` and `activity_type="hospital"` (dual-write). |
| U-CL-03 | Provisioning with legacy `activity_type="commercial"` only resolves to `office` through the alias map. |
| U-CL-04 | When both fields are sent and they disagree, `vertical_code` wins. |
| U-CL-05 | An unknown `vertical_code` returns `400 INVALID_VERTICAL`. |
| U-CL-06 | `PATCH /clients/{id}` with `vertical_code` updates both columns. |
| U-CL-07 | `ClientOut` includes `vertical_code`. |

### 2.6 Backfill — `test_backfill_asset_types.py`

| ID | Test |
|----|------|
| U-BF-01 | Clients with a mappable `activity_type` get `vertical_id`. Unmapped values become `other` and appear in the report. |
| U-BF-02 | One legacy type is created per distinct category per tenant. The code is verbatim: `Fire Safety` keeps its space and case. |
| U-BF-03 | All assets are linked. The report shows `unlinked=0`. |
| U-BF-04 | A re-run is a no-op (idempotent counts). |
| U-BF-05 | `--dry-run` writes nothing and reports the same counts. |
| U-BF-06 | `--tenant` limits the scope to one tenant. |
| U-BF-07 | Case variants (`HVAC`, `hvac`) produce two legacy types and appear in `case_variant_groups`. |
| U-BF-08 | Tenant isolation: tenant A's categories never create types in tenant B. |
| U-BF-09 | **Report regression:** `resolve_effective_schema(schema, asset.category)` returns identical observation fields before and after the backfill for every seeded asset (protects R1). |

### 2.7 Cross-cutting

| ID | Test | Suite |
|----|------|-------|
| U-X-01 | `GET /report-templates/asset-categories` includes an adopted type code that no asset uses yet. | `tests/domains/reports/` |
| U-X-02 | CSV import with `asset_type_code` links the type. An unknown code produces a preview row error. | `tests/domains/assets/` |
| U-X-03 | Tenant B cannot read, patch, or adopt into tenant A's `asset_types` (404 on cross-tenant ID). | `tests/domains/security/test_isolation.py` |
| U-X-04 | The `/asset-types` routes are denied when the tenant package lacks the `assets` feature. | `tests/domains/security/test_rbac.py` |
| U-X-05 | Alembic: `upgrade head` then `downgrade -1` then `upgrade head` succeeds on a scratch DB. This is a manual Postgres check until CI has a PG service (risk R6). | `tests/domains/platform/` and a manual step |

### 2.8 Frontend unit tests

The repo has no FE unit-test runner yet (only Playwright). FE behaviour is covered by e2e (§3). The cycle does not add Vitest. If a runner is added later, `assetTypeLabel` is the first candidate.

---

## 3. E2E scenarios (Playwright, `tests/e2e/domains/asset-types/a1-asset-types.spec.ts`)

Precondition: the pilot seed is extended to run `ensure_vertical_catalog`. One client has `vertical=hospital`, one has `vertical=retail`. Tenant A has 0 adopted types before AT-E01.

| ID | Role | Scenario | Expected |
|----|------|----------|----------|
| AT-E01 | company_admin | Open the Asset types page, then Browse catalog, filter Hospital, select `medical_gas` + `hvac_chiller`, then Adopt. | Both appear in the library with the catalog badge. The catalog drawer marks them as adopted. |
| AT-E02 | company_admin | Adopt the same two again. | Toast shows "already adopted". No duplicate rows. |
| AT-E03 | company_admin | Create custom type `Kitchen Fryer` with the Hotel tag. | It appears with the custom badge. |
| AT-E04 | company_admin | Register an asset for the hospital client. | The picker shows "Recommended for Hospital" with `medical_gas` and `hvac_chiller` first. |
| AT-E05 | company_admin | Pick `hvac_chiller`. | Max age changes to 20. Criticality changes to critical. The schedule section turns on with Quarterly and the STD-INSP template. |
| AT-E06 | company_admin | Edit max age to 12, then switch the type to `medical_gas`. | Max age stays 12 (touched). Criticality updates. |
| AT-E07 | company_admin | Submit. | The asset detail page shows the type name. The label code contains the type code slug. The schedule exists. |
| AT-E08 | company_admin | Register for the retail client. | `medical_gas` is under "All types", not under Recommended. |
| AT-E09 | company_admin | Archive `Kitchen Fryer`. | It is gone from the register picker. An asset that already uses it still shows the name. |
| AT-E10 | company_admin | Edit an asset and change its type. | The label-warning text is visible. After save, the type changes and the label code is unchanged. |
| AT-E11 | technician | Navigate to `/asset-types`. | Redirect or no nav entry. Asset detail still shows the type name. |
| AT-E12 | client_admin | Register an asset (if permitted) or view assets. | Type names are visible. Only their own client's recommendations appear. |
| AT-E13 | super_admin | Create a company and pick Hotel in the vertical select (loaded from the API). | The company detail shows Hotel. A register for that client recommends the hotel types. |
| AT-E14 | company_admin | Switch the UI to AR. | The picker, library, and badges show Arabic names. Layout is RTL-correct. |
| AT-E15 | company_admin, phone viewport (390×844) | Register flow on mobile. | The picker is usable. The catalog drawer is full-screen. No horizontal scroll. |
| AT-E16 | company_admin | Open a WO on the new asset, then the report. | The observation fields match the category-specific set for the type code (report integration). |

---

## 4. Backend checklist

- [ ] Migration ticket filed via `/migration`, and a migration AgDR entry recorded (ApexYard gate).
- [ ] `backend/app/models/asset_types.py` holds `Vertical`, `AssetTypeTemplate`, `AssetType`, and the join tables. Exported in `models/__init__.py`.
- [ ] `Asset.asset_type_id` and `Asset.asset_type` relationship; `Client.vertical_id` and `Client.vertical` relationship.
- [ ] Alembic `c4d5e6f7a8b9_a1_verticals_asset_types.py`: `down_revision="extend_user_role_enum"`, inspector-guarded, no data, full `downgrade()`.
- [ ] Postgres concurrent index on `assets (tenant_id, asset_type_id)`, dialect-guarded.
- [ ] **No** change to `schema_ensure.py`.
- [ ] `services/asset_type_catalog.py::ensure_vertical_catalog`, wired into `run_wave0_platform_bootstrap`.
- [ ] `services/asset_types.py`: `adopt_templates`, `resolve_asset_type_for_write`, `apply_type_defaults`, and case-insensitive code checks via `func.lower()`.
- [ ] Schemas in `schemas/asset_types.py`. `AssetCreate`/`AssetUpdate`/`AssetOut` extended. `ClientCreate`/`ClientProvisionRequest`/`ClientUpdate`/`ClientOut` extended.
- [ ] Routers: `/verticals`, `/asset-type-catalog`, `/asset-types` registered, with role guards and the `require_feature("assets")` guard.
- [ ] `create_asset` and `update_asset` enforce I1. `label_code` is never regenerated on a type change.
- [ ] `list_assets` and `get_asset`: `joinedload(Asset.asset_type)` and the `asset_type_id` filter.
- [ ] `/report-templates/asset-categories` returns the union of type codes and distinct categories.
- [ ] `asset_import`: optional `asset_type_code` column and the link-by-code fallback.
- [ ] Platform provisioning router (`domains/platform/router.py`) and clients router both write `vertical_id` and `activity_type`.
- [ ] `write_audit` on adopt, create type, patch type, and asset type change.
- [ ] `app/cli/backfill_asset_types.py`: `--dry-run`, `--tenant`, JSON report, batched updates. `docker_migrate` runs it when `A1_BACKFILL=1`.
- [ ] `pilot_seed.py` / `pitch_seed.py`: `activity_type="commercial"` replaced with `vertical_code` (pending Q1). The seeds adopt a starter set for e2e.
- [ ] All error `detail` codes added to the FE error map (`src/shared/lib/errors.ts`).
- [ ] `pytest` green. New tests from §2 present.
- [ ] Manual Postgres `upgrade` / `downgrade -1` / `upgrade` on a pilot dump, recorded in the PR.

## 5. UI checklist

- [ ] `types.ts`: `Vertical`, `AssetType`, `AssetTypeTemplate`, `AssetTypeRef`.
- [ ] `assetTypeLabel(row, lang)` helper with a fallback to `category`.
- [ ] `AssetRegisterModal`: type picker with Recommended and All groups, reloaded on client change.
- [ ] Defaults pre-fill only untouched fields. The hard-coded `maxAgeYears=5` is removed when a type is selected.
- [ ] Schedule pre-fill (frequency and template) turns on the schedule section. The user can turn it off.
- [ ] The payload sends `asset_type_id` and no longer sends `category`.
- [ ] Free-text fallback when the tenant has 0 active types.
- [ ] Empty state: admin link to the library, hint for non-admins.
- [ ] `AssetEditModal`: picker and label-code warning.
- [ ] `AssetsPage` / `FilterBar`: asset type filter. Old `?category=` URLs still work.
- [ ] `AssetDetailPage`, `SiteDetailPage`, and WO pages render the localized type name.
- [ ] `CompanyCreateModal`: vertical options from `GET /verticals`, sends `vertical_code`.
- [ ] `CompanyEditModal`: vertical select added.
- [ ] `AssetTypesPage` at `/asset-types`: library list, origin badges, vertical chips, asset count, archive toggle, catalog drawer with adopt, custom type form.
- [ ] Route guarded by `FeatureRoute` `assets` and admin roles. Nav entry in `navItems.ts` (desktop sidebar and mobile More).
- [ ] i18n keys added to **both** `en.json` and `ar.json`. No hard-coded strings.
- [ ] `data-testid` on the picker, the optgroups, the catalog items, the adopt button, and the library rows (e2e §3).
- [ ] RTL checked. Mobile at 390px checked (no horizontal scroll, full-screen drawer).
- [ ] Keyboard and screen reader: the picker has a `<label>`, and the drawer traps focus and closes on Esc.
- [ ] Tokens only (`src/styles/tokens.css`). No new hex values.
- [ ] `npm run build` and `npm run check:imports` green. No `@/components` or `@/pages` imports.

## 6. PR review checklist

**Correctness**

- [ ] I1 is upheld on every write path (create, patch, CSV import, backfill): `category == asset_type.code` when the type is set.
- [ ] I2: no code path changes `asset_types.code`.
- [ ] I3: adoption is idempotent. The unique constraint `(tenant_id, source_template_id)` is present.
- [ ] Copy semantics: no runtime read of `asset_type_templates` outside the catalog browse endpoint and the adoption service (AgDR rule).
- [ ] Explicit request values always override type defaults. The server never auto-creates schedules or types.

**Security and tenancy**

- [ ] Every `asset_types` query filters on `tenant_id`. A cross-tenant ID returns 404.
- [ ] `default_report_template_id` is tenant-validated on create, patch, and adopt.
- [ ] `client_id` scope is enforced for `client_admin` on `GET /asset-types`.
- [ ] Role guards match the design table §5.1.

**Migration**

- [ ] Alembic only. `schema_ensure.py` is untouched.
- [ ] The migration is additive and nullable, with no data. The downgrade works.
- [ ] The backfill is idempotent and has a dry run. The PR includes a sample report.
- [ ] Contract steps are **not** in this PR.

**Performance**

- [ ] No N+1 on the asset list (query-count test present).
- [ ] Index on `assets (tenant_id, asset_type_id)`.

**Frontend**

- [ ] No hard-coded user-facing strings. AR and EN parity.
- [ ] The touched-field logic does not overwrite user input.
- [ ] Old URLs and payloads (`category`) still work during dual-write.
- [ ] Mobile and RTL screenshots attached to the PR.

**Process**

- [ ] The PR links its ticket and this cycle doc. The diff stays inside the ticket scope.
- [ ] Tests from §2 and §3 for the PR scope are present and green.
- [ ] Open questions Q1–Q4 in the design are resolved or explicitly defaulted in the PR body.

---

## 7. Proposed GitHub issues

### Issue 1 — `[Feature] A1-BE: Verticals and asset type library — models, migration, API`

**Acceptance criteria**

- [ ] Given the migration runs on a DB at `extend_user_role_enum`, when `alembic upgrade head` completes, then the five new tables exist, `clients.vertical_id` and `assets.asset_type_id` are nullable FKs, and `alembic downgrade -1` reverses the change cleanly.
- [ ] Given bootstrap runs twice, when the catalog is queried, then the 7 verticals and all seed templates exist exactly once.
- [ ] Given a company_admin, when they `POST /asset-types/adopt` with template IDs, then tenant-owned copies are created with provenance. A repeat call creates no duplicates and reports `already_adopted`.
- [ ] Given a later catalog change, when the tenant type is read, then it is unchanged (copy-on-adopt).
- [ ] Given `GET /asset-types?client_id=X`, then the types for X's vertical (plus universal types) are flagged `recommended` and sorted first.
- [ ] Given `POST /assets` with `asset_type_id`, then `category` equals the type code, the type defaults fill the omitted fields, and the response includes `asset_type`.
- [ ] Given a legacy `POST /assets` with `category` only, then the asset links to a type with the same code if one exists, and no type is auto-created.
- [ ] Given a `PATCH` that changes the asset type, then `category` follows and `label_code` is unchanged.
- [ ] Given `POST /clients/provision` with `vertical_code` or a legacy `activity_type`, then both `vertical_id` and `activity_type` are stored. `PATCH /clients/{id}` can change the vertical.
- [ ] Given the backfill CLI with `--dry-run` and then for real, then every asset is linked (`unlinked=0`), re-runs are no-ops, and the report observation fields for every existing asset are unchanged.
- [ ] Cross-tenant access to any asset type returns 404. Non-admin roles get 403 on writes.
- [ ] `schema_ensure.py` is unchanged. A migration ticket and a migration AgDR are linked.

### Issue 2 — `[Feature] A1-FE: Asset type picker in register flow and asset type library`

**Acceptance criteria**

- [ ] Given a client with a vertical, when the register modal opens, then the asset type picker shows the "Recommended for {vertical}" group first, then "All types", in the active language.
- [ ] Given a selected type, then max age, criticality, and the schedule (frequency and template) pre-fill. Fields the user already edited are not overwritten.
- [ ] On submit, the payload sends `asset_type_id`. The created asset shows the type name on the list, detail, and site pages.
- [ ] Given a tenant with 0 active types, then the free-text category input is shown. Admins see a link to adopt types.
- [ ] The edit modal allows a type change and shows a warning that the label code does not change.
- [ ] The company create and edit modals load verticals from `GET /verticals` and send `vertical_code`.
- [ ] `/asset-types` (admin only): list with origin badges and vertical chips, archive toggle, catalog drawer with vertical filter and multi-select adopt, custom type form.
- [ ] All strings exist in `en.json` and `ar.json`. RTL is correct. Usable at 390px width with no horizontal scroll.
- [ ] `npm run build` and `npm run check:imports` pass.

### Issue 3 — `[Task] A1-TEST: Unit and e2e coverage for verticals and asset types`

**Acceptance criteria**

- [ ] The backend tests U-CAT, U-ADP, U-AT, U-AS, U-CL, U-BF, and U-X (cycle doc §2) are implemented and green in CI.
- [ ] U-BF-09 proves that the report observation fields are identical before and after the backfill for every seeded asset.
- [ ] The tenant isolation and RBAC suites include the asset type routes.
- [ ] The asset list query-count test proves no N+1.
- [ ] The pilot seed creates two clients with distinct verticals and runs the catalog bootstrap, so e2e has deterministic data.
- [ ] Playwright `a1-asset-types.spec.ts` covers AT-E01 to AT-E16, including the AR/RTL and phone-viewport scenarios, and passes against the local stack.
- [ ] The manual Postgres upgrade/downgrade check is recorded in the PR (until CI has a Postgres service).
