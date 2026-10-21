# UX Specification — A1: Asset Type Catalog & Vertical Flows

**Version:** 1.0  
**Date:** 2026-10-22  
**Author:** Iman (UX Designer)  
**Scope:** Company provisioning → vertical selection → asset-type catalog → asset registration with type inheritance and per-asset overrides.  
**Palette / Shell:** Concept D locked (Harbor Navy P1 + Blueprint grid Pat1). RTL Arabic is the default locale.

---

## 1. Context & Design Principles

| Principle | Application |
|-----------|-------------|
| Type-first | Every asset inherits defaults from its type; technicians override only what differs per machine |
| Vertical-aware | The selected vertical seeds the type catalog with sensible defaults; prevents blank-slate paralysis |
| Progressive disclosure | Inherited fields show read-only unless the user explicitly overrides |
| Mobile-first | All flows must work in 360 px wide portrait (Concept D field shell) |
| RTL parity | Every layout mirrors horizontally in Arabic; icon arrows reverse; date format follows locale |

---

## 2. Flow 1 — Company Create: Vertical Picker

**Who:** `super_admin` / `company_admin` provisioning a new tenant.  
**Entry point:** Companies page → **+ New Company** → `CompanyCreateModal`.

### 2.1 Current vs. A1 Delta

The modal today collects `activity_type` via a plain `<select>`. A1 replaces that field with a **vertical picker** that:

- Uses visual cards instead of a dropdown (5 named verticals + "Other").
- Stores the selected vertical on the tenant record (`vertical` field).
- Seeds the asset-type catalog post-provision with vertical defaults (server side).

### 2.2 Vertical Picker — Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  Create Company                                         │
│  ────────────────────────────────────────────────────   │
│  Company name *       [___________________________]     │
│  Manager name  *      [___________________________]     │
│                                                         │
│  Industry vertical *                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ 🏥       │ │ 🏨       │ │ 📦       │               │
│  │ Hospital │ │ Hotel    │ │Warehouse │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ 🏫       │ │ 🏭       │ │ ···      │               │
│  │ Schools  │ │ Factories│ │  Other   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
│                                                         │
│  ── First site ──────────────────────────────────────   │
│  Site name *          [___________________________]     │
│  City *    [_________]   Country * [_______________]    │
│  Timezone             [Asia/Riyadh ▼]                   │
│                                                         │
│  [Cancel]                          [Create Company →]   │
└─────────────────────────────────────────────────────────┘
```

**Card anatomy (each vertical):**
- Icon (emoji or SVG, 24 px) centered
- Label 12 px medium below icon
- Selected state: navy border `2px solid --color-primary-600`, navy-10% fill background
- Hover: subtle shadow lift
- Unselected: neutral border, white bg

**Verticals and seeded types:**

| Vertical | Default asset types seeded |
|----------|---------------------------|
| Hospital | Medical Equipment, HVAC, Electrical Panel, Elevator, Plumbing, Fire Safety |
| Hotel | HVAC, Elevator, Electrical, Pool Equipment, Kitchen Equipment, Fire Safety |
| Warehouse | Forklift, Conveyor, Racking, Fire Safety, Electrical Panel, HVAC |
| Schools | HVAC, Electrical, Fire Safety, Playground Equipment, Lab Equipment |
| Factories | CNC Machine, Compressor, Conveyor, Electrical Panel, HVAC, Fire Safety |
| Other | (no auto-seed; tenant starts with blank catalog) |

### 2.3 States

| State | Behaviour |
|-------|-----------|
| **None selected** | "Create Company" button disabled; helper text "Select a vertical to continue" in red-500 |
| **Other selected** | Button enabled; no seeding happens; info chip "You can add types manually after creation" |
| **Loading (saving)** | Button shows spinner + "Creating…"; cards are non-interactive |
| **Error** | Banner at top of modal: `⚠ [error message]`; button re-enables |
| **Success** | Transitions to `ProvisionCredentialsModal` (existing pattern) |

### 2.4 RTL Notes (Arabic)

- Card grid reflowed right-to-left (`dir="rtl"` on modal container).
- Cancel/Create buttons swap to left/right respectively.
- Arabic vertical labels: مستشفى · فندق · مستودع · مدارس · مصانع · أخرى.

---

## 3. Flow 2 — Asset Type Catalog (Tenant Admin)

**Who:** `client_admin` / `company_admin`.  
**Route (proposed):** `/asset-types` (new page under company settings).  
**Entry point:** Sidebar → Settings → Asset Types, **or** inline prompt during asset register.

### 3.1 Catalog List Page — Wireframe

```
Asset Types                          [+ New Type]
────────────────────────────────────────────────────────────
Filter: [All verticals ▼]  Search [________________]

┌─────────────────────────────────────────────────────────┐
│ Name              Category    Max age   Max repairs  PM  │
│──────────────────────────────────────────────────────── │
│ ☐ HVAC Unit       HVAC        15 yr     5            ✓  │
│ ☐ Elevator        Vertical    20 yr     8            ✓  │
│ ☐ Medical Device  Medical      8 yr     3            ✓  │
│ ☐ Fire Panel      Safety      10 yr     2            ✓  │
│ ☐ Generator       Electrical  12 yr     6            ✓  │
└─────────────────────────────────────────────────────────┘

Showing 5 of 12 types          [< Prev]  Page 1 of 3  [Next >]
```

**Row actions (on row hover → kebab ···):**
- Edit
- Duplicate
- Archive (soft-delete; archived types no longer appear in asset register picker)

**Bulk action bar (when ≥1 row checked):**
`[Archive selected]  [Delete selected]` — floats above table.

### 3.2 Create / Edit Type Modal — Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  New Asset Type                                         │
│  ─────────────────────────────────────────────────────  │
│  Type name *        [___________________________]       │
│  Category           [HVAC ▼]                            │
│                                                         │
│  ── Lifecycle defaults ──────────────────────────────── │
│  Max age (years) *  [____]   Max repairs *  [____]      │
│  Hint: These become defaults for every new asset        │
│        of this type. Technicians can override per asset.│
│                                                         │
│  ── Preventive Maintenance ──────────────────────────── │
│  [ ] Enable PM schedule for this type                   │
│      └─ (when checked) ───────────────────────────────  │
│         Frequency    [Monthly ▼]                        │
│         Report template  [Select template ▼]            │
│                                                         │
│  ── Custom attributes (optional) ────────────────────── │
│  + Add attribute                                        │
│  ┌────────────────┬────────────────┬──────────────────┐ │
│  │ Attribute name │ Type           │ Required?        │ │
│  │ [____________] │ [Text ▼]       │ [ ]              │ │
│  └────────────────┴────────────────┴──────────────────┘ │
│                                                         │
│  [Cancel]                            [Save Type]        │
└─────────────────────────────────────────────────────────┘
```

**Field definitions:**

| Field | Type | Validation |
|-------|------|------------|
| Type name | Text | Required; 2–80 chars; unique within tenant |
| Category | Select | Matches `asset.category` taxonomy |
| Max age (years) | Integer | 1–99; default from vertical seed |
| Max repairs | Integer | 1–99; default from vertical seed |
| PM enabled | Checkbox | Unlocks frequency + template pickers |
| Frequency | Select | Monthly / Quarterly / Semi-annual / Annual |
| Report template | Select (from existing templates) | Required when PM enabled |
| Custom attributes | Repeating group | Name (text), Type (Text/Number/Date/Boolean), Required flag |

**Attribute types:**
- `Text` → free text field on asset form
- `Number` → numeric input with optional unit label
- `Date` → date picker
- `Boolean` → toggle / checkbox

### 3.3 States

| State | Behaviour |
|-------|-----------|
| **Empty catalog** | Full-page empty state: icon + "No asset types yet" + primary CTA "Add your first type"; secondary link "Import from vertical defaults" |
| **Loading list** | Skeleton rows (3 rows, shimmering) |
| **Saving type** | Modal Save button: spinner + "Saving…"; fields dimmed |
| **Validation error** | Inline field-level red hint under each invalid field; banner at top if server error |
| **Archive confirm** | Inline confirm chip on row: `Archive [Type name]? [Yes, archive] [Cancel]`; no full dialog |

### 3.4 RTL Notes

- Table columns right-aligned headings.
- Kebab menu opens to the left of the trigger.
- + Add attribute button anchored to right edge.
- Modal CTA row: Cancel on right, Save on left.

---

## 4. Flow 3 — Asset Register with Type Inheritance

**Who:** `client_admin` / `site_manager` / `company_admin`.  
**Entry point:** Assets page → **+ Register Asset**, or site detail page → **+ Asset**.

### 4.1 Revised Register Modal — Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  Register Asset                                         │
│  ─────────────────────────────────────────────────────  │
│  Company          [Riyadh Medical Center ░░░░░░░░░░░]   │
│  Site *           [Main Building ▼]                     │
│  Asset name *     [___________________________]         │
│                                                         │
│  ── Asset type ─────────────────────────────────────── │
│  Type *                                                 │
│  [Search or select type…               ▼]               │
│   ┌─ dropdown open ─────────────────────────────────┐   │
│   │ ◎ HVAC Unit                                     │   │
│   │ ◎ Elevator                                      │   │
│   │ ◎ Medical Device                                │   │
│   │ ─────────────────────────────────────────────── │   │
│   │ + Create new type "[typed text]"                │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│  ── Inherited from type: HVAC Unit ─────────────────── │
│  [ℹ Defaults inherited. Override only if this asset    │
│     differs from type defaults.]                        │
│  Max age (years)   [15]  ← from type   [Override ✎]    │
│  Max repairs       [5 ]  ← from type   [Override ✎]    │
│  PM schedule       Monthly · Report: HVAC Checklist     │
│                          [Override ✎]                   │
│  Custom attrs:                                          │
│   Refrigerant type  [___________] *                     │
│   Last gas charge   [date picker]                       │
│                                                         │
│  ── Location ─────────────────────────────────────────  │
│  Floor [____]   Room [____]                             │
│                                                         │
│  ── Lifecycle ────────────────────────────────────────  │
│  Install date   [date picker]                           │
│  Serial         [___________________________]           │
│  Model          [___________________________]           │
│  Criticality    [High ▼]                                │
│  Warranty until [date picker]                           │
│  [ ] Spare device (swap-out maintenance)                │
│                                                         │
│  [Cancel]                         [Register Asset →]    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Type Selector Behaviour

**Search/select combo:**
- Typeahead filtering on type name and category.
- Dropdown shows max 8 results; scrollable.
- Last row always: `+ Create new type "[query]"` — opens inline mini-form.

**Inline "Create new type" mini-form (expands inside modal):**
```
  ┌────────────────────────────────────────────────────┐
  │ New type name   [HVAC Chiller Unit          ]      │
  │ Max age (yr)    [___]   Max repairs  [___]          │
  │                 [Cancel]  [Add type and continue →] │
  └────────────────────────────────────────────────────┘
```
- On save: creates the type (minimal fields), selects it, collapses the mini-form.
- Full type editing is available later via Settings → Asset Types.

### 4.3 Inherited Field Display Rules

| Field source | Display |
|---|---|
| **From type, not overridden** | Read-only input with grey bg; chip "from type"; [Override ✎] link on right |
| **Overridden by user** | Editable input with navy left border; chip "overridden"; [Reset to type default] link |
| **No type selected** | All lifecycle fields show as plain editable inputs (same as current modal) |
| **Type has PM, not overriding** | PM section shows collapsed summary: "Monthly · HVAC Checklist [Override ✎]" |
| **Type has PM, overriding** | PM section expands with frequency + template dropdowns |
| **Type has custom attrs** | Each attr rendered per its type (text/number/date/boolean); required attrs marked * |

### 4.4 Full Field Inventory (Register Modal, Post-A1)

**Section: Context**
- Company (locked read-only for non-super roles)
- Site * (select)
- Asset name *

**Section: Asset type**
- Type * (searchable select + inline create)

**Section: Inherited from type** *(visible only after type selected)*
- Max age (years) — with override
- Max repairs — with override
- PM schedule — with override
- Custom attributes (type-defined)

**Section: Location**
- Floor
- Room

**Section: Lifecycle**
- Install date
- Serial number
- Model
- Criticality (Low / Medium / High / Critical)
- Warranty until
- Last maintenance date
- Smart labels (comma-separated)
- Spare device (checkbox)

### 4.5 Per-Asset Override: max_age / max_repairs

When the user clicks **Override ✎** next to an inherited field:
1. Field transitions from read-only (grey bg) to editable (navy left border).
2. A helper chip appears: `⚠ Overriding type default (15 yr)`.
3. A **Reset to type default** text link appears inline.
4. On save, the asset record stores the override value; the type default is unchanged.
5. If the user resets, the field reverts to the type default value and becomes read-only again.

Overrides are visible in the asset detail view with the same chip notation.

---

## 5. Empty, Error, and Loading States

### 5.1 Asset Type Catalog

| Situation | Treatment |
|-----------|-----------|
| No types exist | Empty-state card: warehouse/factory icon, "No asset types yet", primary button "Add your first type", secondary link "Import vertical defaults" |
| Search returns 0 results | Inline empty: "No types match '[query]'" + "Create '[query]' as a new type →" |
| List loading | 3 skeleton rows with shimmer; table headers visible |
| Type save error | Toast: `⚠ Could not save type. [Retry]`; modal stays open |
| Archive blocked (assets exist) | Inline error on row: "Cannot archive — 4 active assets use this type. Reassign first." |

### 5.2 Asset Register (Type Selector)

| Situation | Treatment |
|-----------|-----------|
| Catalog is empty | Dropdown shows only "+ Create new type" option; note "No types yet — add one or create inline" |
| Type metadata loading | Inherited-fields section shows skeleton (2 shimmer rows) while fetching type details |
| Type fetch error | Error chip below selector: `⚠ Could not load type defaults. Enter values manually.`; all fields become editable |
| Partial submit (server error) | Banner at top of modal: `⚠ [message]`; form stays open; fields preserve user input |
| Missing required custom attr | Field-level red hint + modal-level count: "2 required fields missing" |

### 5.3 Company Create

| Situation | Treatment |
|-----------|-----------|
| Vertical not selected | CTA disabled; "Select a vertical to continue" below card grid |
| Server error on provision | Error banner inside modal; form stays open |
| Slow network | CTA shows spinner; cards non-interactive; no double-submit |

### 5.4 Global Loading Skeletons

All async data surfaces follow the design system pattern:
- Skeleton width: 60–90% of container (randomised per row for naturalness).
- Shimmer direction: left-to-right in LTR; **right-to-left in RTL**.
- Duration: 1.4 s cycle, ease-in-out.

---

## 6. Arabic RTL Notes

All flows must satisfy:

| Element | LTR | RTL (Arabic) |
|---------|-----|--------------|
| Modal CTA row | Cancel left · Primary right | Cancel right · Primary left |
| Vertical picker cards | Left-to-right grid flow | Right-to-left grid flow |
| Table | Column headers left-aligned | Column headers right-aligned |
| Kebab menu | Opens left-of-trigger | Opens right-of-trigger |
| Override chip | Right of field label | Left of field label |
| Toast / banner | Slides in from top-right | Slides in from top-left |
| Date inputs | `yyyy-mm-dd` placeholder | Use Gregorian; hijri conversion is a future enhancement |
| Number inputs | Left-to-right digit entry | `dir="ltr"` on `<input>` regardless of page dir (standard practice) |
| Shimmer direction | Left → right | Right → left |

**Arabic field labels (key new fields):**

| English | Arabic |
|---------|--------|
| Industry vertical | القطاع الصناعي |
| Asset type | نوع الأصل |
| Max age (years) | العمر الأقصى (سنوات) |
| Max repairs | الحد الأقصى للإصلاحات |
| Override | تجاوز |
| Reset to type default | إعادة إلى الافتراضي |
| Inherited from type | موروث من النوع |
| Create new type | إنشاء نوع جديد |

---

## 7. Navigation & Entry Points (Summary)

```
Companies page
  └─ + New Company → CompanyCreateModal
       ├─ Vertical picker [NEW A1]
       └─ → ProvisionCredentialsModal (existing)

Settings (sidebar, tenant admin)
  └─ Asset Types → /asset-types [NEW A1]
       ├─ List (filter · search · bulk)
       ├─ + New Type → CreateTypeModal [NEW A1]
       └─ Row → EditTypeModal [NEW A1]

Assets page  /  Site detail page
  └─ + Register Asset → AssetRegisterModal [EXTENDED A1]
       ├─ Type selector (searchable + inline create) [NEW]
       ├─ Inherited fields section [NEW]
       │   ├─ max_age (override)
       │   ├─ max_repairs (override)
       │   ├─ PM schedule (override)
       │   └─ Custom attributes (type-defined)
       └─ Existing lifecycle fields (unchanged)
```

---

## 8. Open Questions for Engineering

1. **API shape:** Will `POST /asset-types` return the seeded types after vertical selection, or is seeding a background job? (Affects UX of "import defaults" CTA timing.)
2. **Inline create type scope:** Mini-form creates a minimal type record; should it be auto-published or saved as draft requiring full edit before active?
3. **Override storage:** Per-asset `max_age_years` and `max_repair_count` already exist on the asset model. Confirm `asset_type_id` FK is added and `max_age_years` on asset = override when different from type default.
4. **Custom attr rendering on WO/report:** Out of scope for A1? Confirm whether technicians see custom attrs when opening a work order for a typed asset.
5. **Vertical migration:** If tenant wants to change vertical post-creation, what happens to seeded types already used by assets? (Recommend: disallow or add types only, never remove.)

---

*Document owner: UX (Iman). Engineering handoff: Backend engineer to spec `/asset-types` API; Frontend engineer to implement `AssetTypeModal`, extend `AssetRegisterModal`, extend `CompanyCreateModal`.*
