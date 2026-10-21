# PRD — Program A1: Verticals · AssetType Catalog · Asset Register Create-if-Missing

**Document type:** Product Requirements Document  
**Program:** A1 — Verticals + AssetType Catalog + Asset Register Create-if-Missing  
**Product:** Orbit AM  
**Version:** 1.0  
**Date:** 2026-10-22  
**Author:** Mariam (PM)  
**Status:** Draft — awaiting engineering sign-off and AgDR for schema decisions  
**Dependencies:** Wave 6 cleanup complete (branch `feature/phase-3-restructure/cleanup` ✅)

---

## Table of contents

1. [Problem statement](#1-problem-statement)
2. [Goals and success](#2-goals-and-success)
3. [Non-goals](#3-non-goals)
4. [Personas](#4-personas)
5. [Locked decisions](#5-locked-decisions)
6. [User stories and acceptance criteria](#6-user-stories-and-acceptance-criteria)
   - 6.1 [Verticals — client classification](#61-verticals--client-classification)
   - 6.2 [Platform AssetType catalog](#62-platform-assettype-catalog)
   - 6.3 [Tenant AssetType copy-on-adopt](#63-tenant-assettype-copy-on-adopt)
   - 6.4 [VerticalAssetPolicy override config](#64-verticalassetpolicy-override-config)
   - 6.5 [Asset register — create-if-missing flow](#65-asset-register--create-if-missing-flow)
   - 6.6 [Type-version freeze on registration](#66-type-version-freeze-on-registration)
7. [Data model (logical)](#7-data-model-logical)
8. [Out of scope](#8-out-of-scope)
9. [Success metrics](#9-success-metrics)
10. [Open questions](#10-open-questions)
11. [Traceability](#11-traceability)

---

## 1. Problem statement

### 1.1 Current state

Orbit AM's asset register stores `category` and `type` as unconstrained free-text strings (see `src/shared/lib/types.ts`, `AssetRegisterModal.tsx`). Client classification is stored in `Client.activity_type` — also free text. This creates four concrete failures:

| Failure | Impact |
|---------|--------|
| Every tenant invents their own category taxonomy | Cross-tenant analytics and platform-managed PM templates are impossible |
| No vertical context on a client | Cannot pre-populate sensible asset types, PM frequencies, or SLA classes when onboarding a new hospital vs a warehouse |
| Registering an asset requires knowing the exact category string | Field staff either leave it as "general" or invent inconsistent labels; reports and WO filters break |
| No type-version tracking | If a platform admin updates lifecycle rules for "Chiller Unit", existing assets silently inherit the new rule — or don't, with no audit trail of which rule applied at registration time |

### 1.2 The gap

The system needs a **curated, platform-owned asset-type catalog** that carries default lifecycle aging, PM schedule, attribute schema, and SLA class per type — differentiated by the **vertical** the client operates in — while still letting FM companies adapt types for their specific context without modifying shared platform definitions.

---

## 2. Goals and success

| # | Goal | Measurable form |
|---|------|-----------------|
| G1 | Every client has a structured vertical, replacing free-text `activity_type` | 100 % of new clients created with a valid vertical after A1 ships; existing clients migrated via backfill script |
| G2 | Platform ships a curated AssetType catalog with at least 30 types pre-seeded across all verticals | Catalog seeded in prod before first hospital pilot onboarding |
| G3 | FM company technicians can register an asset by picking from their tenant's adopted types, with sensible defaults pre-filled | Time-to-register an asset ≤ 90 seconds in usability test; "general" category usage drops to 0 % after A1 goes live |
| G4 | Registering an asset against a missing type is a one-step inline creation, not a separate admin flow | Zero support tickets about "I can't find my asset type" in the first month post-launch |
| G5 | Frozen type-version on each asset provides a stable audit record | Compliance audit: type rules at registration time retrievable for any asset |

---

## 3. Non-goals

| Non-goal | Rationale |
|----------|-----------|
| QR code scanning to identify assets | QR workflow is Program A2 |
| Inventory / spare parts catalog | Program A3 |
| AI-based asset type suggestion | AI Maintenance is a standalone paid add-on (pitch §3.3); not bundled into core |
| Meter / runtime-hours tracking per asset type | Program TBD (meters module, ManWinWin gap #6) |
| Full FSM fork per vertical | Locked decision: VerticalAssetPolicy is config-layer override, not a separate state machine |
| Tenant-level pricing differentiation by vertical | Commercial packaging decision; out of PM scope for A1 |
| Asset type import from CSV | Asset bulk import (existing `AssetImportModal`) is a separate flow; type catalog has its own management UI |

---

## 4. Personas

### P1 — Platform Admin (SW staff, `is_platform_admin = true`)

Curates the global AssetType catalog and VerticalAssetPolicy config. Seeds new types and vertical overrides. Can see all tenants' adopted type libraries. Cannot see asset-level data of tenants.

### P2 — Company Admin (`company_admin` role)

Manages the FM company's tenant-scoped asset type library. Browses the platform catalog, adopts types into the tenant library, and customises labels or attributes. Creates net-new tenant-scoped types when a client has equipment outside the platform catalog.

### P3 — Site Manager / Manager (`site_manager`, `manager` roles)

Registers assets on site. Picks from the tenant's adopted type library. Triggers the create-if-missing inline flow when the type they need is not already adopted. Does not see platform catalog directly.

### P4 — Technician (`technician` role)

Registers assets during a site visit. Has the same type-picker UI as P3 but narrowed to types relevant to the site's client vertical. Cannot create new types.

### P5 — Client Admin (`client_admin` role)

Views assets registered against their sites. May request new asset types via the site manager. Cannot modify the type library.

---

## 5. Locked decisions

The following decisions are **locked for A1**. Reopening requires a new AgDR.

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Verticals are a fixed enum:** Hospital, Hotel, Warehouse, Schools/Universities, Factories, Other | Replaces free-text `Client.activity_type`. Enum keeps cross-tenant analytics clean; "Other" absorbs edge cases |
| D2 | **Copy-on-adopt:** when a tenant adopts a platform AssetType, a tenant-scoped copy is created; it is not a live reference to the platform record | Prevents platform catalog changes from silently mutating a tenant's operating rules; mirrors the `template_snapshot_json` pattern in `MaintenanceReport` |
| D3 | **VerticalAssetPolicy is a config overlay, not a forked FSM** | One lifecycle FSM (`active → warning → EOL → retired`) applies to all assets; the policy adds vertical-specific defaults (max_age_years, PM frequency class, SLA class) that pre-fill registration, not a separate state machine per vertical |
| D4 | **Asset register create-if-missing:** picking a type in the register modal offers an inline "Create type" sub-flow if the type does not exist in the tenant library; the new type is tenant-scoped (not pushed to platform catalog) | Removes the need for a separate admin pre-flight before registering unusual equipment |
| D5 | **Type-version freeze on registration:** each asset row stores `asset_type_snapshot_json` capturing the full type definition at registration time | Mirrors `MaintenanceReport.template_snapshot_json`; ensures compliance audits reflect the rules in force at the time the asset was registered |

---

## 6. User stories and acceptance criteria

### 6.1 Verticals — client classification

#### US-A1-01 — Assign vertical when creating a client

> As a **Company Admin** (P2), I want to assign a vertical (Hospital / Hotel / Warehouse / Schools & Universities / Factories / Other) when creating or editing a client, so that the system can pre-populate sensible defaults for that client's sites and assets.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-01-01 | I am on the Create Client screen with the vertical field visible | I submit the form without selecting a vertical | The form rejects submission with a required-field validation error in the user's locale |
| AC-01-02 | I am creating a client | I select "Hospital" as the vertical | The client is saved with `vertical = hospital` and all downstream defaults (asset type suggestions, PM frequency class, SLA class) resolve against the Hospital VerticalAssetPolicy |
| AC-01-03 | I am creating a client | I select "Other" as the vertical | The client is saved with `vertical = other`; no vertical-specific defaults are pre-loaded; asset type suggestions show the full tenant library unfiltered |
| AC-01-04 | An existing client has `activity_type` populated (legacy free text) | The backfill migration runs | Each existing client receives the closest matched `vertical` from the mapping table, or `other` where no mapping exists; `activity_type` column is deprecated (nullable, not removed) |
| AC-01-05 | I am editing an existing client | I change the vertical from "Warehouse" to "Hospital" | The client record is updated; assets registered before this change retain their frozen `asset_type_snapshot_json` and are unaffected; future registrations use Hospital vertical defaults |

#### US-A1-02 — Vertical visible in client detail and list

> As a **Company Admin** (P2), I want to see the vertical label on the client detail page and in the clients list, so that I can confirm the correct vertical is assigned at a glance.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-02-01 | A client has vertical = "Hospital" | I open the client detail page | I see "Hospital" (Arabic: مستشفى) displayed next to the client name, using a consistent vertical badge |
| AC-02-02 | The clients list page loads | — | Each row shows the client's vertical badge; rows are filterable by vertical |

---

### 6.2 Platform AssetType catalog

#### US-A1-03 — Platform Admin views and manages the global AssetType catalog

> As a **Platform Admin** (P1), I want to create, edit, and deactivate asset types in the global catalog, so that all tenants have a consistent, well-maintained starting library.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-03-01 | I am authenticated as Platform Admin | I navigate to `/platform/asset-types` | I see the full platform catalog with columns: Name (EN/AR), Vertical(s), PM frequency class, Default max age (years), SLA class, Attribute schema summary, Status (active/inactive), Version number |
| AC-03-02 | I create a new platform AssetType with required fields: name (EN + AR), applicable verticals (multi-select), default max_age_years, PM frequency class | I submit the form | A new platform AssetType record is created at version 1; it is visible in the catalog; it is not yet adopted by any tenant |
| AC-03-03 | I edit an existing platform AssetType (e.g. change default max_age_years from 10 to 12) | I save the edit | The platform record increments its `version` counter; all tenant copies that have not been locally customised are flagged `platform_update_available = true`; tenant copies that have been customised are not auto-updated |
| AC-03-04 | I attempt to delete a platform AssetType that is referenced by one or more tenant copies | I click Delete | The system rejects the deletion with a message indicating the number of tenant copies; I can only deactivate (`is_active = false`), not hard-delete |
| AC-03-05 | I deactivate a platform AssetType | The type is deactivated | Tenants with existing copies retain their copies (unaffected); new tenant adoptions of the deactivated type are blocked; existing assets with frozen snapshots of the type are unaffected |

#### US-A1-04 — Platform catalog is pre-seeded with at least 30 types

> As a **Platform Admin** (P1), I want the catalog to ship with a curated seed of at least 30 common asset types covering all verticals, so that new tenant onboarding does not start from a blank slate.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-04-01 | A fresh production seed or a new environment `POST /platform/demo/reset` runs | — | The platform catalog contains ≥ 30 asset types distributed across Hospital (≥ 10), Hotel (≥ 5), Warehouse (≥ 5), Schools/Universities (≥ 5), Factories (≥ 5) verticals; the "Other" vertical shares a generic subset |
| AC-04-02 | — | I call `GET /platform/asset-types?vertical=hospital` | I receive ≥ 10 hospital-relevant types (e.g. Chiller Unit, Steriliser, Medical Gas System, Elevator — clinical, Generator, Fire Suppression System, HVAC Air Handling Unit, Nurse Call System, Medical Imaging Equipment, UPS System) |

---

### 6.3 Tenant AssetType copy-on-adopt

#### US-A1-05 — Company Admin browses platform catalog and adopts types

> As a **Company Admin** (P2), I want to browse the platform AssetType catalog and adopt types into my tenant's library, so that my team has a curated list of types pre-configured with correct defaults for our clients' verticals.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-05-01 | I navigate to `/settings/asset-types` (Company Admin view) | — | I see two tabs: "Our Library" (tenant-scoped types already adopted or created) and "Platform Catalog" (platform types available to adopt) |
| AC-05-02 | In the Platform Catalog tab, I find "Chiller Unit" and click "Adopt" | — | A tenant-scoped copy of "Chiller Unit" is created with all platform defaults copied; the type is now visible in "Our Library"; the platform record is unchanged |
| AC-05-03 | I adopt a type | — | The tenant copy records: `source_platform_type_id`, `adopted_at`, `adopted_version` (the platform version at time of adoption), and `platform_update_available = false` |
| AC-05-04 | The platform Admin later updates the "Chiller Unit" platform record (version bumps) | — | My tenant copy shows a "Platform update available" notice in "Our Library" but is NOT auto-updated; I must explicitly choose to review and apply or dismiss the update |
| AC-05-05 | I choose "Apply platform update" on a tenant copy | I confirm | The tenant copy's defaults are refreshed to match the latest platform version; if I had locally customised any field, the UI shows a diff and asks me to resolve conflicts field-by-field before applying |

#### US-A1-06 — Company Admin customises a tenant AssetType copy

> As a **Company Admin** (P2), I want to customise the defaults on a tenant copy (e.g. change default max age from 10 to 8 years for chillers in a specific climate), so that registered assets get the right local defaults without modifying the shared platform definition.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-06-01 | I have adopted "Chiller Unit" into my tenant library | I edit the tenant copy to change `default_max_age_years` from 10 to 8 | The tenant copy is updated; the platform record is unchanged; the tenant copy is flagged `locally_customised = true` |
| AC-06-02 | I edit any field on the tenant copy | — | The tenant copy records `last_customised_at` and `last_customised_by_user_id` for audit purposes |
| AC-06-03 | A platform update arrives for "Chiller Unit" | — | Because the tenant copy is `locally_customised = true`, the update notice says "Platform has updates — review carefully; your local customisations may conflict" |

---

### 6.4 VerticalAssetPolicy override config

#### US-A1-07 — Platform Admin configures VerticalAssetPolicy per vertical

> As a **Platform Admin** (P1), I want to define a VerticalAssetPolicy for each vertical (Hospital, Hotel, etc.) that overrides default lifecycle aging, PM frequency class, and SLA class for asset types in that vertical, so that the system pre-fills context-appropriate defaults without forking the lifecycle state machine.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-07-01 | I navigate to `/platform/vertical-policies` | — | I see one policy row per vertical; each row shows: Vertical, Default PM frequency class, Default SLA response class, Default lifecycle aging modifier (e.g. "reduce max age by 20% if criticality = critical"), Last updated at |
| AC-07-02 | I edit the Hospital policy to set default PM frequency class = "monthly-critical" for all types with `criticality = critical` | I save | Assets registered against a Hospital client with criticality = critical will pre-populate with `pm_frequency_class = monthly-critical` at registration time |
| AC-07-03 | An asset is registered | — | The system resolves defaults in this priority order: (1) Tenant AssetType copy overrides, (2) Platform AssetType defaults, (3) VerticalAssetPolicy defaults for the client's vertical; the resolved values are applied to the registration form as pre-filled suggestions, not locked values |
| AC-07-04 | The Company Admin overrides a pre-filled default during registration | — | The override is accepted; the frozen `asset_type_snapshot_json` records both the policy-resolved default and the operator-supplied override for audit |

---

### 6.5 Asset register — create-if-missing flow

#### US-A1-08 — Site Manager / Technician registers an asset from an adopted type

> As a **Site Manager** (P3), I want to pick an asset type from the tenant's library when registering a new asset, so that the registration form is pre-filled with correct defaults (max age, PM schedule, attribute fields) without manually entering every field.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-08-01 | I open the asset register modal | — | I see a searchable "Asset Type" picker that lists types from the tenant library filtered by the selected site's client vertical (Hospital types first if client vertical = Hospital) |
| AC-08-02 | I search for "Chiller" and select "Chiller Unit" | — | The form pre-fills: `max_age_years` (from tenant copy), `pm_frequency_class`, `criticality` (default), and all custom attribute fields defined in the type's attribute schema |
| AC-08-03 | I submit the registration form | — | The asset is created with the type's frozen snapshot stored in `asset_type_snapshot_json`; pre-filled values are editable before submit |
| AC-08-04 | A different site manager registers the same type for a different site one week later (after a platform update was applied to the tenant copy) | — | The second asset's `asset_type_snapshot_json` reflects the updated tenant copy version at the time of the second registration; the two assets may have different frozen snapshots and that is correct by design |

#### US-A1-09 — Inline create-if-missing when type is not in tenant library

> As a **Site Manager** (P3), I want to create a new tenant-scoped asset type inline while registering an asset, so that I am not blocked by a missing type and do not need to abandon the registration workflow.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-09-01 | I search for "Hydraulic Dock Leveller" in the type picker and the type does not exist in the tenant library or the platform catalog | — | The picker shows a "Not found" state with a prominent "+ Create new type" action |
| AC-09-02 | I click "+ Create new type" | — | An inline form expands (or a second step within the modal) asking for: Name (EN + AR), Applicable verticals (pre-selected to match the current client vertical), Default max_age_years, PM frequency class, Criticality default, SLA class; advanced attribute schema is optional (can add later) |
| AC-09-03 | I complete the inline creation and click "Create & Select" | — | The new type is saved as a **tenant-scoped type** (not pushed to platform catalog); it is automatically selected as the type for the current registration; the registration continues with defaults from the new type |
| AC-09-04 | I attempt inline creation with only the name field filled | — | Validation blocks submission with errors on the required fields: max_age_years and PM frequency class |
| AC-09-05 | After the type is created inline | — | The new type appears in the Company Admin's "Our Library" tab under "Custom (not from platform catalog)"; the Platform Admin is not notified automatically (no push to platform catalog) |
| AC-09-06 | I am authenticated as a **Technician** (P4) role | I search for a type and it is not found | I see the "Not found" state but the "+ Create new type" action is NOT shown (read: the create-if-missing inline flow is gated to `site_manager` and `manager` roles and above) |

#### US-A1-10 — Company Admin requests Platform Admin add a type to the catalog (optional uplift)

> As a **Company Admin** (P2), I want to flag a tenant-scoped custom type as a "platform catalog submission", so that the Platform Admin can review it and add it to the shared catalog for other tenants to benefit from.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-10-01 | I am viewing a custom tenant type in "Our Library" | I click "Submit to platform catalog" | The type is flagged `catalog_submission_pending = true`; a notification is sent to Platform Admins in-app |
| AC-10-02 | Platform Admin reviews the submission | They click "Accept and add to catalog" | A new platform AssetType is created from the submitted type; the tenant copy is linked via `source_platform_type_id`; the flag is cleared |
| AC-10-03 | Platform Admin rejects the submission | They click "Reject" with an optional comment | The flag is cleared; the type remains as a tenant-scoped custom type; the Company Admin sees the rejection and optional comment in their type's detail view |

---

### 6.6 Type-version freeze on registration

#### US-A1-11 — Frozen snapshot is stored on registration and is auditable

> As a **Platform Admin** (P1) or **Company Admin** (P2), I want every registered asset to carry a frozen snapshot of the AssetType definition that was in effect at registration time, so that compliance audits can reconstruct exactly what rules applied to each asset when it was registered.

**Acceptance criteria:**

| ID | Given | When | Then |
|----|-------|------|------|
| AC-11-01 | I register an asset with type "Steriliser" (tenant copy at version 3) | The registration is submitted | The asset row's `asset_type_snapshot_json` contains the full type definition at version 3: name (EN/AR), max_age_years, pm_frequency_class, sla_class, attribute schema, vertical policy applied, and the timestamp of adoption |
| AC-11-02 | The Company Admin later updates the "Steriliser" tenant copy (bumps to version 4) | — | All previously registered assets retain their version 3 snapshot; they are not updated retroactively |
| AC-11-03 | I view the asset detail page for an asset registered under version 3 of "Steriliser" | — | I see a "Type at registration" panel showing the frozen snapshot; if the current type definition has since changed, I see a notice: "Type has been updated since this asset was registered (v3 → v4)" |
| AC-11-04 | The asset detail API response includes `asset_type_snapshot_json` | — | The field is always present for assets registered after A1 ships; assets registered before A1 have `asset_type_snapshot_json = null` (graceful null handling required in UI) |

---

## 7. Data model (logical)

> This section describes the logical entities and their key fields. The concrete SQL schema and migration plan will be specified in the companion AgDR. Field names here are proposals, not final column names.

### 7.1 Vertical enum

```
vertical: 'hospital' | 'hotel' | 'warehouse' | 'schools_universities' | 'factories' | 'other'
```

- Added as an enum column on the `clients` table (replaces `activity_type`).
- `activity_type` column is kept as deprecated-nullable for one release cycle (backfill migration maps existing values).

### 7.2 platform_asset_types (platform-owned)

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid PK | |
| `code` | string UNIQUE | Stable machine slug e.g. `chiller_unit`, `steriliser` |
| `name_en` | string | English display name |
| `name_ar` | string | Arabic display name |
| `applicable_verticals` | array(vertical enum) | Verticals for which this type is relevant (multi-select; empty = all) |
| `default_max_age_years` | integer | Default asset lifespan |
| `pm_frequency_class` | string | e.g. `monthly`, `quarterly`, `annual`, `monthly-critical` |
| `sla_class` | string | e.g. `critical-2h`, `standard-24h`, `routine-72h` |
| `criticality_default` | string | `low` / `medium` / `high` / `critical` |
| `attribute_schema_json` | jsonb | Custom attribute definitions (name, type, required) |
| `version` | integer | Incremented on every edit |
| `is_active` | boolean | Soft-delete; deactivated types not adoptable |
| `created_at`, `updated_at` | timestamptz | |

### 7.3 tenant_asset_types (tenant-scoped copies + custom types)

| Field | Type | Notes |
|-------|------|-------|
| `id` | uuid PK | |
| `tenant_id` | uuid FK → tenants | Tenant isolation |
| `source_platform_type_id` | uuid FK → platform_asset_types, nullable | null if pure custom (not adopted from platform) |
| `adopted_version` | integer, nullable | Platform version at time of adoption; null for custom |
| `platform_update_available` | boolean | True when platform version > adopted_version AND not locally customised beyond threshold |
| `locally_customised` | boolean | True if any field was overridden after adoption |
| `catalog_submission_pending` | boolean | True when Company Admin has submitted for platform catalog review |
| `name_en` | string | Copied from platform or operator-entered |
| `name_ar` | string | |
| `applicable_verticals` | array(vertical enum) | Copied or operator-entered |
| `default_max_age_years` | integer | |
| `pm_frequency_class` | string | |
| `sla_class` | string | |
| `criticality_default` | string | |
| `attribute_schema_json` | jsonb | |
| `version` | integer | Tenant-copy version (independent of platform version) |
| `is_active` | boolean | |
| `adopted_at` | timestamptz, nullable | |
| `last_customised_at` | timestamptz, nullable | |
| `last_customised_by_user_id` | uuid, nullable | |
| `created_at`, `updated_at` | timestamptz | |

### 7.4 vertical_asset_policies (platform-owned, one row per vertical)

| Field | Type | Notes |
|-------|------|-------|
| `vertical` | vertical enum PK | One row per vertical |
| `default_pm_frequency_class` | string | Fallback PM class if type does not override |
| `default_sla_class` | string | Fallback SLA class |
| `criticality_age_modifier_json` | jsonb | e.g. `{"critical": 0.8}` → max_age * 0.8 when criticality = critical |
| `notes` | text | Internal rationale |
| `updated_at` | timestamptz | |
| `updated_by_user_id` | uuid | |

### 7.5 Asset row additions

Added to the existing `assets` table:

| Field | Type | Notes |
|-------|------|-------|
| `tenant_asset_type_id` | uuid FK → tenant_asset_types, nullable | Replaces free-text `category` as the structured reference; nullable for legacy rows |
| `asset_type_snapshot_json` | jsonb, nullable | Frozen copy of the full `tenant_asset_types` row at registration time; null for legacy assets |
| `category` | string | Kept for backward compatibility; populated from `tenant_asset_type.name_en` on registration going forward |

### 7.6 Default resolution order at registration

```
Priority 1 (highest): Operator override entered in the registration form
Priority 2:           Tenant AssetType copy field (if locally customised)
Priority 3:           Platform AssetType field (via adopted_version snapshot)
Priority 4 (lowest):  VerticalAssetPolicy default for the client's vertical
```

---

## 8. Out of scope

| Item | Disposition |
|------|-------------|
| QR code scanning linked to asset types | Program A2 |
| Inventory / spare parts linked to asset type (BOM) | Program A3 |
| AI-based type suggestion at registration | AI Maintenance standalone add-on |
| Meter / runtime readings per type | Meters module — separate program |
| Full FSM per vertical (e.g. Hospital assets have a different lifecycle state set) | Locked out: VerticalAssetPolicy is config only (D3) |
| Tenant-to-tenant sharing of custom types | No cross-tenant data access by design (AgDR-PHASE3) |
| Asset type CSV bulk import | Separate engineering task; not in A1 scope |
| Multilingual support beyond EN/AR | English and Arabic only for A1; additional locales deferred |
| Automated platform catalog update push to all tenant copies | Platform updates are pull-based (flag + notice), never auto-applied |

---

## 9. Success metrics

### Leading indicators (measurable within 4 weeks of launch)

| Metric | Target |
|--------|--------|
| % of new client records created with a structured vertical (not null) | 100 % |
| % of new asset registrations using a structured type (not free-text "general") | ≥ 95 % |
| Avg time-to-register an asset in the new flow (usability test, n ≥ 5) | ≤ 90 seconds |
| Rate of inline type creation (create-if-missing triggered per 100 registrations) | < 15 per 100 (high rate = catalog gaps; triggers catalog expansion sprint) |

### Lagging indicators (measurable at pilot review, ~12 weeks)

| Metric | Target |
|--------|--------|
| PM schedule auto-population rate (assets registered with a PM class vs blank) | ≥ 90 % of newly registered assets |
| Support tickets about missing or wrong asset type | 0 in the first month |
| Tenant-submitted types accepted to platform catalog | ≥ 5 types promoted in first quarter (signals catalog quality and adoption) |
| Assets with frozen snapshot (post-A1) that can be retrieved in compliance audit | 100 % |

---

## 10. Open questions

| # | Question | Owner | Target resolution |
|---|----------|-------|-------------------|
| OQ-1 | **Backfill mapping table:** What is the exact mapping from current `activity_type` free-text values in prod data to the vertical enum? Who owns the mapping decision (PM or data analyst)? | Abdullah / Mariam | Before A1 enters build |
| OQ-2 | **`pm_frequency_class` vocabulary:** What is the canonical list of PM frequency class strings? Should this be a platform enum (enforced) or a free-text suggestion? Impact on PM scheduler (Program pre-A1) | Tech Lead | AgDR for PM scheduler must define this before A1 schema is final |
| OQ-3 | **`sla_class` vocabulary:** Same question as OQ-2 for SLA classes. Egypt hospital FM contracts use varied SLA tiers — do we standardise at platform level or defer to contract module (ManWinWin gap #4)? | Mariam / Tech Lead | Before A1 schema |
| OQ-4 | **Attribute schema JSON format:** Should `attribute_schema_json` follow a shared JSON Schema dialect, or an Orbit-custom format? Decision affects the future custom attribute editor UI and validation engine | Tech Lead | AgDR — A1 schema |
| OQ-5 | **Technician inline create gate:** Is the role gate `site_manager` and above correct, or should `technician` be allowed to create types in "light" mode (name only, no schema)? Field pilot context needed | PM + Field pilot lead | Pilot prep |
| OQ-6 | **Platform catalog submission workflow:** Is the platform submission flow (US-A1-10) in scope for A1 MVP or can it ship in A1.1? It's a low-criticality feature that could be replaced by a Slack/email channel initially | Mariam | Before sprint planning |
| OQ-7 | **"Schools/Universities" vertical label:** The locked decision uses a compound name. Should the enum value be `schools_universities` (machine) with display label "Educational" in EN and in AR? Label finalisation needed for i18n | UX / Mariam | Before A1 UI build |
| OQ-8 | **Legacy asset display:** Assets registered before A1 will have `asset_type_snapshot_json = null`. What does the asset detail page show in the "Type at registration" panel for these? Options: hide panel, show "Registered before type catalog was introduced", show the current `category` string | UX / Engineering | Before A1 UI build |

---

## 11. Traceability

| Requirement | Source |
|-------------|--------|
| Vertical enum (Hospital, Hotel, Warehouse, Schools/Universities, Factories, Other) | Locked decision — customer_requirements_roadmap A1 |
| Replace `Client.activity_type` free text with vertical | Locked decision — A1; confirmed gap in `types.ts` (no vertical field on Company/Site/Client) |
| Copy-on-adopt pattern for platform → tenant AssetType | Locked decision — A1; analogous to `MaintenanceReport.template_snapshot_json` (see `types.ts:87`) |
| VerticalAssetPolicy as config overlay, not FSM fork | Locked decision — A1 |
| Create-if-missing inline flow in register modal | Locked decision — A1; current `AssetRegisterModal.tsx` has hard-coded `category = "general"` as the gap |
| Type-version freeze on registration | Locked decision — A1 |
| Asset catalog: ManWinWin gap analysis | `docs/product/MANWINWIN_GAP_MATRIX.md` — Asset Management domain: "Asset register (name, category, location, serial, install date) ✅ Done" + asset hierarchy gap |
| Tenant isolation: `tenant_id` on all tenant rows | `docs/phase3-restructure/AgDR-PHASE3-TENANT-ARCHITECTURE.md` §1 |
| Feature flag: `assets` flag in `tenant_subscriptions.features_json` | `docs/phase3-restructure/ERD_WAVE0.md` — `subscription_packages.features_json` |
| Role RBAC boundaries | `docs/phase3-restructure/RBAC_ROLES.md`, `src/shared/lib/roles.ts` |

---

*Program A1 — Next: A2 (QR asset identification) · A3 (inventory/parts catalog)*  
*Companion AgDR required: schema design, migration plan, API contract.*
