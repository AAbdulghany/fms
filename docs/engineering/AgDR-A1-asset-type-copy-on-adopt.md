# AgDR: A1 — Asset types are copied into the tenant library on adoption

**Status:** Accepted (pending Solution Architect review)  
**Date:** 2026-10-22  
**Program:** Orbit Program A, slice A1  
**Owner:** Tech Lead (Hisham)  
**Design:** [A1_ASSET_TYPES_TECH_DESIGN.md](./designs/A1_ASSET_TYPES_TECH_DESIGN.md)

---

## Context

A1 adds a platform-owned asset type catalog (`asset_type_templates`, tagged by vertical). Each maintenance company (tenant) needs asset types that assets reference. Tenants must be able to change names, lifecycle defaults, criticality, schedule frequency, and the default report template.

The asset type code is load-bearing. `assets.category` mirrors the code, and three things are keyed by that string:

1. Report observation fields. The lookup in `services/report_schema_resolve.py` is exact and case-sensitive.
2. The label code prefix (`services/asset_labels.py`).
3. Existing `?category=` filters and CSV imports.

Assets therefore need a reference that a platform-side edit cannot change.

## Options

| Option | Description |
|--------|-------------|
| **A. Copy on adopt** | Adoption creates a tenant-owned `asset_types` row. The row copies code, names, defaults, and vertical tags. `source_template_id` and `source_version` record the provenance only. Assets reference the tenant row. |
| **B. Live reference** | Assets (or a thin tenant link table) reference `asset_type_templates` directly. Tenant changes are stored as a sparse override layer and merged at read time. |
| **C. Hybrid** | Keep a live reference by default, and copy on the tenant's first edit. |

## Decision

**Option A — copy on adopt.**

## Rationale

| Criterion | A. Copy | B. Live reference | C. Hybrid |
|-----------|---------|-------------------|-----------|
| Tenant isolation: platform edits cannot change a tenant's assets, reports, or labels | Yes | No. A catalog rename or default change reaches every tenant immediately. | Partial. Unedited tenants are exposed. |
| Stable code for observation keys and labels | Yes. Owned by the tenant and immutable. | Depends on the platform never changing codes. | Partial |
| Read path | A single join `assets → asset_types` | Join plus override merge on every list and detail call | Two code paths |
| Custom types share one table and one shape with adopted types | Yes | No. A separate custom table or a nullable FK is needed. | No |
| Legacy backfill (`origin=legacy`) fits naturally | Yes | No | Partial |
| Implementation and test cost for A1 | Low | High | Highest |
| Catalog improvements reach tenants automatically | No | Yes | Partial |

Option B fails on the requirement that matters most for a CMMS. A maintenance record must not change because a platform team edited a catalog row. Option C has the costs of both options and still has the drift problem.

## Consequences

**Positive**

- Each tenant fully owns its asset types. Audit trails, report keys, and labels remain stable.
- One table holds catalog-adopted, custom, and legacy types (`origin` column).
- Adoption is idempotent through `UNIQUE (tenant_id, source_template_id)`.

**Negative (accepted)**

- **Drift.** Catalog fixes do not reach tenants that have already adopted. `source_version` makes the drift detectable. A later slice adds "refresh from catalog": a per-field diff, accepted by the tenant, that never touches `code`.
- **Duplication.** Each tenant stores a copy of the catalog rows it adopted. The volume is small (tens of rows per tenant).
- **Semantic overlap.** A legacy `HVAC` type and an adopted `hvac_ahu` type can coexist. A "map legacy to catalog type" tool is a follow-up. The design records this as risk R3.

**Rules that follow from this decision**

- No runtime code reads `asset_type_templates` to render, validate, or default an asset. Only the catalog browse endpoint and the adoption service read it.
- `asset_types.code` is immutable after creation.
- Adoption never overwrites tenant-edited values. When a tenant already has a type with the same code, adoption fills only the NULL defaults and records the provenance.

## Revisit when

- More than one catalog version bump per month reaches tenants who ask for the change. Build "refresh from catalog" at that point.
- A regulated vertical requires centrally enforced type definitions. Evaluate a locked-field subset at that point, not a full live reference.
