# UI Specifications — FMS Phase 2

**Version:** 1.0  
**Date:** 2026-04-17  
**Status:** Draft for Review

This document provides detailed UI specifications for all missing pages and components needed for Phase 2 of the FMS project.

---

## Table of Contents

1. [Companies Page](#1-companies-page)
2. [Company Detail Page](#2-company-detail-page)
3. [Sites Page](#3-sites-page)
4. [Site Detail Page](#4-site-detail-page)
5. [Assets Page](#5-assets-page)
6. [Asset Detail Page](#6-asset-detail-page)
7. [Employees Page](#7-employees-page)
8. [Welcome/Dashboard Page](#8-welcomedashboard-page)
9. [Sidebar Navigation](#9-sidebar-navigation)
10. [Breadcrumb Navigation](#10-breadcrumb-navigation)

---

## 1. Companies Page

### Overview
**Purpose:** List all client companies for super_admin and company_admin roles.  
**URL:** `/companies`  
**Roles:** super_admin, company_admin  
**Layout:** Table with filters

### Visual Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│ Companies                              [+ Create Company]│
├─────────────────────────────────────────────────────────┤
│ [FilterBar: Search, Status, Date]                       │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Company Name    │ Sites │ Active WOs │ Status      │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ ABC Facilities  │   12  │     8      │ ● Active    │ │
│ │ XYZ Properties  │    5  │     3      │ ● Active    │ │
│ │ DEF Holdings    │   20  │    15      │ ● Active    │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Container:**
```tsx
<div className="space-y-6">
  <PageHeader 
    title="Companies" 
    action={<Button variant="primary">+ Create Company</Button>}
  />
  <FilterBar
    showSearch
    showStatusFilter
    showDateRange
    availableStatuses={["active", "inactive", "suspended"]}
  />
  <DataTable columns={columns} data={companies} />
</div>
```

**Table Columns:**
1. **Company Name** — Link to detail page, primary text `text-base font-medium`
2. **Contact** — Email/phone, secondary text `text-sm text-neutral-600`
3. **Sites Count** — Number badge
4. **Active Work Orders** — Number badge with color (red if > 10)
5. **Status** — Badge component
6. **Actions** — Dropdown menu (View, Edit, Deactivate)

**Card Layout (Mobile):**
```tsx
<Card className="p-4 space-y-3">
  <div className="flex items-start justify-between">
    <div>
      <Link className="text-base font-medium text-primary-600">
        ABC Facilities
      </Link>
      <p className="text-sm text-neutral-600">contact@abc.com</p>
    </div>
    <StatusBadge status="active" />
  </div>
  <div className="flex gap-4 text-sm">
    <span className="text-neutral-600">12 Sites</span>
    <span className="text-neutral-600">8 Active WOs</span>
  </div>
  <Button variant="ghost" size="sm">View Details →</Button>
</Card>
```

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Card view, single column, hamburger menu |
| **Tablet (640px - 1024px)** | Table view with scrollable container, icon-only sidebar |
| **Desktop (> 1024px)** | Full table view, fixed sidebar |

### Filtering and Search

**Search Functionality:**
- Real-time search as user types (debounced 300ms)
- Searches: Company name, contact email, phone
- Placeholder: "Search companies..."

**Filters:**
- **Status:** All, Active, Inactive, Suspended
- **Date Range:** Created from/to
- **Has Active WOs:** Yes/No toggle

**URL Sync:**
- Filters persist in URL: `/companies?status=active&search=ABC`

### Actions

**Primary Actions:**
1. **Create Company** — Opens modal with form
2. **View Details** — Navigate to `/companies/:id`
3. **Edit** — Opens edit modal
4. **Deactivate** — Confirmation dialog

**Bulk Actions (Future):**
- Select multiple → Export CSV
- Select multiple → Bulk status change

### Empty State

**No Companies Yet:**
```
┌────────────────────────────────────┐
│                                    │
│         [Building Icon]            │
│                                    │
│     No companies registered yet    │
│                                    │
│  Add your first client company to  │
│      start managing their sites    │
│                                    │
│      [+ Create First Company]      │
│                                    │
└────────────────────────────────────┘
```

**No Results (Filtered):**
```
┌────────────────────────────────────┐
│         [Search Icon]              │
│                                    │
│     No companies match filters     │
│                                    │
│  Try adjusting your search or      │
│          filter criteria           │
│                                    │
│       [Clear All Filters]          │
└────────────────────────────────────┘
```

### Design Tokens

**Colors:**
- Background: `bg-neutral-50` (page), `bg-neutral-0` (cards/table)
- Borders: `border-neutral-200`
- Primary action: `bg-primary-600 hover:bg-primary-700`
- Status active: `bg-success-light text-success-dark`
- Status inactive: `bg-neutral-200 text-neutral-600`

**Typography:**
- Page title: `text-3xl font-semibold text-neutral-900`
- Company name: `text-base font-medium text-primary-600`
- Metadata: `text-sm text-neutral-600`
- Counts: `text-sm font-medium text-neutral-900`

**Spacing:**
- Page container: `space-y-6`
- Card padding: `p-6`
- Table cell padding: `px-4 py-3`

### RTL Considerations

- Table text-align: Use `text-start` (auto RTL)
- Flex layouts: Use `gap-*` (symmetric)
- Margins: Use logical properties (`ms-*`, `me-*`)
- Icons: Flip directional icons (arrows)

### Accessibility

**ARIA Labels:**
```tsx
<button aria-label="Create new company">+ Create Company</button>
<input aria-label="Search companies" placeholder="Search..." />
<Link aria-label="View details for ABC Facilities">ABC Facilities</Link>
```

**Keyboard Navigation:**
- Tab through table rows
- Enter/Space to activate links/buttons
- Escape to close modals
- Arrow keys for table navigation (future)

**Screen Reader:**
- Table has `role="table"` (semantic `<table>`)
- Status badges have text labels, not color-only
- Loading states announce via `aria-live="polite"`

---

## 2. Company Detail Page

### Overview
**Purpose:** View company details with nested sites list.  
**URL:** `/companies/:id`  
**Roles:** super_admin, company_admin, client_admin  
**Layout:** Header + Tabs + Nested content

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Home > Companies > ABC Facilities                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ABC Facilities                           [Edit] [Archive] │
│  contact@abc.com • +966 12 345 6789                       │
│  Status: ● Active • 12 Sites • 8 Active Work Orders       │
│                                                            │
├─────┬──────────┬──────────┬──────────┬──────────────────  │
│Sites│Work Orders│Invoices  │Settings  │                    │
├─────┴──────────┴──────────┴──────────┴──────────────────  │
│                                                            │
│  [FilterBar: Search sites]                [+ Add Site]     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Site Name         │ Location      │ Assets │ WOs     │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ Riyadh HQ         │ Riyadh       │   45   │   3     │ │
│  │ Jeddah Branch     │ Jeddah       │   32   │   2     │ │
│  │ Dammam Office     │ Dammam       │   28   │   3     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Structure:**
```tsx
<div className="space-y-6">
  <Breadcrumb items={[
    { label: "Home", href: "/" },
    { label: "Companies", href: "/companies" },
    { label: "ABC Facilities", href: "/companies/abc-123" }
  ]} />
  
  <PageHeader
    title="ABC Facilities"
    subtitle="contact@abc.com • +966 12 345 6789"
    actions={
      <>
        <Button variant="secondary">Edit</Button>
        <Button variant="ghost">Archive</Button>
      </>
    }
  />
  
  <StatusBar>
    <StatusBadge status="active" />
    <Stat label="Sites" value={12} />
    <Stat label="Active Work Orders" value={8} />
  </StatusBar>
  
  <Tabs defaultTab="sites">
    <Tab id="sites" label="Sites">
      <SitesTable companyId={companyId} />
    </Tab>
    <Tab id="work-orders" label="Work Orders">
      <WorkOrdersTable companyId={companyId} />
    </Tab>
    <Tab id="invoices" label="Invoices">
      <InvoicesTable companyId={companyId} />
    </Tab>
    <Tab id="settings" label="Settings">
      <CompanySettings companyId={companyId} />
    </Tab>
  </Tabs>
</div>
```

**Sites Tab Content:**
- Nested sites table
- Each row links to `/companies/:companyId/sites/:siteId`
- Inline actions: View, Edit, Archive

### Key Information Displayed

**Header Section:**
1. Company name (H1)
2. Primary contact (email, phone)
3. Status badge
4. Quick stats (sites count, active WOs, total invoices)

**Tabs:**
1. **Sites** — Nested sites list with quick stats
2. **Work Orders** — All WOs for this company (across sites)
3. **Invoices** — Billing history
4. **Settings** — Company settings (billing contact, preferences)

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Stack header, tabs scroll horizontally, cards view |
| **Tablet (640px - 1024px)** | Header side-by-side, tabs full width, table view |
| **Desktop (> 1024px)** | Full layout with fixed sidebar |

### Actions

**Primary Actions:**
1. **Edit Company** — Opens modal with editable fields
2. **Archive Company** — Confirmation dialog
3. **Add Site** — Opens site creation modal (in Sites tab)

**Secondary Actions:**
4. **Export Data** — Download CSV of sites/WOs
5. **View Reports** — Navigate to reports page

### Empty State (Sites Tab)

```
┌────────────────────────────────────┐
│         [Map Pin Icon]             │
│                                    │
│      No sites for this company     │
│                                    │
│   Add a site to start managing     │
│     assets and work orders         │
│                                    │
│         [+ Add First Site]         │
└────────────────────────────────────┘
```

### Design Tokens

**Colors:**
- Tab active: `border-b-2 border-primary-600 text-primary-600`
- Tab inactive: `border-b-2 border-transparent text-neutral-600 hover:text-neutral-900`
- Status bar background: `bg-neutral-100 rounded-lg p-4`

**Typography:**
- Company name: `text-3xl font-semibold text-neutral-900`
- Subtitle: `text-base text-neutral-600`
- Tab labels: `text-sm font-medium`

**Spacing:**
- Status bar stats: `gap-6`
- Tab content: `pt-6`

### RTL Considerations

- Breadcrumb separator: Use logical separator (auto-flips)
- Tabs: Use `flex` with `gap-*` (symmetric)
- Status bar: Use `flex gap-6` (symmetric)

### Accessibility

**ARIA Labels:**
```tsx
<Tabs aria-label="Company information tabs">
  <Tab id="sites" aria-controls="sites-panel">Sites</Tab>
</Tabs>
<div id="sites-panel" role="tabpanel" aria-labelledby="sites-tab">
  {/* Content */}
</div>
```

**Keyboard Navigation:**
- Arrow keys to switch tabs
- Tab to move through interactive elements
- Enter/Space to activate

---

## 3. Sites Page

### Overview
**Purpose:** List all sites (filtered by company for client_admin).  
**URL:** `/sites` or `/companies/:companyId/sites`  
**Roles:** super_admin, company_admin, client_admin, site_manager  
**Layout:** Card grid with map integration (future)

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Sites                                     [+ Create Site]   │
├────────────────────────────────────────────────────────────┤
│ [FilterBar: Search, Company, City]                         │
├────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐│
│ │ Riyadh HQ       │  │ Jeddah Branch   │  │ Dammam Office││
│ │ ABC Facilities  │  │ ABC Facilities  │  │ ABC Facilities││
│ │ 📍 Riyadh, SA   │  │ 📍 Jeddah, SA   │  │ 📍 Dammam, SA││
│ │                 │  │                 │  │               ││
│ │ 45 Assets       │  │ 32 Assets       │  │ 28 Assets     ││
│ │ 3 Active WOs    │  │ 2 Active WOs    │  │ 3 Active WOs  ││
│ │                 │  │                 │  │               ││
│ │ [View Details]  │  │ [View Details]  │  │ [View Details]││
│ └─────────────────┘  └─────────────────┘  └──────────────┘│
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Container:**
```tsx
<div className="space-y-6">
  <PageHeader 
    title="Sites" 
    action={<Button variant="primary">+ Create Site</Button>}
  />
  <FilterBar
    showSearch
    showCompanyFilter
    showLocationFilter
  />
  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {sites.map(site => <SiteCard key={site.id} site={site} />)}
  </div>
</div>
```

**Site Card:**
```tsx
<Card className="p-6 space-y-4 hover:border-primary-300 transition-colors">
  <div className="flex items-start justify-between">
    <div className="flex-1">
      <Link className="text-lg font-medium text-primary-600 hover:underline">
        {site.name}
      </Link>
      <p className="text-sm text-neutral-600">{site.company_name}</p>
      <p className="text-sm text-neutral-500 flex items-center gap-1">
        <MapPinIcon className="w-4 h-4" />
        {site.city}, {site.country}
      </p>
    </div>
    <QRCodeButton siteId={site.id} />
  </div>
  
  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-neutral-200">
    <Stat label="Assets" value={site.asset_count} />
    <Stat label="Active WOs" value={site.active_wo_count} color={site.active_wo_count > 5 ? "warning" : "default"} />
  </div>
  
  <Button variant="ghost" size="sm" fullWidth>
    View Details →
  </Button>
</Card>
```

### Key Information Displayed

**Site Card Content:**
1. Site name (link to detail)
2. Company name (parent)
3. Location (city, country with icon)
4. QR code button (for mobile check-in)
5. Asset count
6. Active work orders count
7. View details button

### Filtering and Search

**Search Functionality:**
- Searches: Site name, company name, city, address
- Placeholder: "Search sites..."

**Filters:**
- **Company** — Dropdown (if super_admin)
- **City** — Dropdown (common cities)
- **Has Active WOs** — Yes/No toggle

### Actions

**Primary Actions:**
1. **Create Site** — Opens modal with form (company, name, address)
2. **View Details** — Navigate to `/sites/:id`
3. **Show QR Code** — Modal with printable QR code for site
4. **Edit Site** — Opens edit modal
5. **Archive Site** — Confirmation dialog

### Empty State

**No Sites Yet:**
```
┌────────────────────────────────────┐
│         [Map Pin Icon]             │
│                                    │
│       No sites registered yet      │
│                                    │
│   Add your first site to start     │
│  tracking assets and work orders   │
│                                    │
│        [+ Create First Site]       │
└────────────────────────────────────┘
```

### QR Code Feature

**QR Code Modal:**
- Displays site QR code (encodes site ID)
- Print button
- Download PNG button
- Use case: Technicians scan on arrival

**QR Code Content:**
```json
{
  "type": "fms_site",
  "site_id": "abc-123",
  "company_id": "xyz-456",
  "url": "https://fms.example.com/sites/abc-123"
}
```

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | 1 column card grid |
| **Tablet (640px - 1024px)** | 2 column card grid |
| **Desktop (> 1024px)** | 3 column card grid |

### Map Integration (Future)

**Map View Toggle:**
- Switch between card grid and map view
- Map shows pins for each site location
- Click pin → Site card popup
- Cluster pins when zoomed out

### Design Tokens

**Colors:**
- Card hover: `hover:border-primary-300`
- Location icon: `text-neutral-500`
- QR code button: `text-primary-600 hover:text-primary-700`

**Typography:**
- Site name: `text-lg font-medium text-primary-600`
- Company name: `text-sm text-neutral-600`
- Location: `text-sm text-neutral-500`

**Spacing:**
- Card grid gap: `gap-4`
- Card padding: `p-6`
- Stats grid: `grid-cols-2 gap-4`

### RTL Considerations

- QR code: Always centered (no RTL impact)
- Location icon: No flip needed
- Stats grid: Symmetric layout

### Accessibility

**ARIA Labels:**
```tsx
<Link aria-label="View details for Riyadh HQ site">Riyadh HQ</Link>
<Button aria-label="Show QR code for Riyadh HQ">
  <QRCodeIcon />
</Button>
```

**Keyboard Navigation:**
- Tab through cards
- Enter to view details
- Focus visible on cards

---

## 4. Site Detail Page

### Overview
**Purpose:** View site details with nested assets and work orders.  
**URL:** `/sites/:id` or `/companies/:companyId/sites/:siteId`  
**Roles:** All roles (filtered by permission)  
**Layout:** Header + Tabs + Nested content

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Home > Companies > ABC Facilities > Sites > Riyadh HQ      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Riyadh HQ                         [Edit] [QR Code] [•••]  │
│  ABC Facilities                                            │
│  📍 King Fahd Road, Riyadh 12345, Saudi Arabia            │
│  Status: ● Active • 45 Assets • 3 Active Work Orders      │
│                                                            │
├────────┬────────────┬──────────┬──────────────────────────│
│Assets  │Work Orders │Locations │Maintenance Schedule      │
├────────┴────────────┴──────────┴──────────────────────────│
│                                                            │
│  [FilterBar: Search assets]              [+ Register Asset]│
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Asset ID      │ Type      │ Lifecycle │ Last Maint.  │ │
│  ├──────────────────────────────────────────────────────┤ │
│  │ HVAC-001      │ HVAC Unit │ ✓ Active  │ 2 days ago   │ │
│  │ HVAC-002      │ HVAC Unit │ ⚠ Warning │ 15 days ago  │ │
│  │ ELEV-001      │ Elevator  │ ✓ Active  │ 1 week ago   │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Structure:**
```tsx
<div className="space-y-6">
  <Breadcrumb items={breadcrumbItems} />
  
  <PageHeader
    title="Riyadh HQ"
    subtitle="ABC Facilities"
    meta={<LocationBadge>{fullAddress}</LocationBadge>}
    actions={
      <>
        <Button variant="secondary">Edit</Button>
        <Button variant="secondary">QR Code</Button>
        <DropdownMenu>
          <MenuItem>Archive</MenuItem>
          <MenuItem>Export Data</MenuItem>
        </DropdownMenu>
      </>
    }
  />
  
  <StatusBar>
    <StatusBadge status="active" />
    <Stat label="Assets" value={45} />
    <Stat label="Active Work Orders" value={3} />
    <Stat label="Last Inspection" value="2 weeks ago" />
  </StatusBar>
  
  <Tabs defaultTab="assets">
    <Tab id="assets" label="Assets">
      <AssetsTable siteId={siteId} />
    </Tab>
    <Tab id="work-orders" label="Work Orders">
      <WorkOrdersTable siteId={siteId} />
    </Tab>
    <Tab id="locations" label="Locations">
      <LocationTree siteId={siteId} />
    </Tab>
    <Tab id="schedule" label="Maintenance Schedule">
      <MaintenanceCalendar siteId={siteId} />
    </Tab>
  </Tabs>
</div>
```

### Key Information Displayed

**Header Section:**
1. Site name (H1)
2. Company name (link to company)
3. Full address with map pin icon
4. Status badge
5. Quick stats (assets, active WOs, last inspection)

**Tabs:**
1. **Assets** — All assets at this site
2. **Work Orders** — All WOs for this site
3. **Locations** — Hierarchical location tree (Building > Floor > Zone > Room)
4. **Maintenance Schedule** — Calendar view of scheduled maintenance

### Hierarchical Breadcrumb

```tsx
<Breadcrumb>
  <BreadcrumbItem href="/">Home</BreadcrumbItem>
  <BreadcrumbItem href="/companies">Companies</BreadcrumbItem>
  <BreadcrumbItem href="/companies/abc-123">ABC Facilities</BreadcrumbItem>
  <BreadcrumbItem href="/companies/abc-123/sites">Sites</BreadcrumbItem>
  <BreadcrumbItem href="/sites/xyz-789" active>Riyadh HQ</BreadcrumbItem>
</Breadcrumb>
```

### Actions

**Primary Actions:**
1. **Edit Site** — Opens modal with editable fields
2. **Show QR Code** — Modal with printable QR code
3. **Register Asset** — Opens asset creation modal
4. **Create Work Order** — Opens WO creation modal

**Secondary Actions:**
5. **Archive Site** — Confirmation dialog
6. **Export Data** — Download CSV of assets/WOs
7. **View on Map** — Opens map view (future)

### Empty State (Assets Tab)

```
┌────────────────────────────────────┐
│         [Package Icon]             │
│                                    │
│      No assets at this site yet    │
│                                    │
│   Register your first asset to     │
│      start tracking maintenance    │
│                                    │
│      [+ Register First Asset]      │
└────────────────────────────────────┘
```

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Stack header, tabs scroll horizontally, cards view |
| **Tablet (640px - 1024px)** | Header side-by-side, tabs full width, table view |
| **Desktop (> 1024px)** | Full layout with fixed sidebar |

### Design Tokens

**Colors:**
- Location badge: `bg-neutral-100 text-neutral-700 rounded-md px-2 py-1`
- Status bar: `bg-neutral-50 rounded-lg p-4`

**Typography:**
- Site name: `text-3xl font-semibold text-neutral-900`
- Company name: `text-lg text-neutral-600`
- Address: `text-sm text-neutral-600`

**Spacing:**
- Header meta spacing: `gap-2`
- Status bar stats: `gap-6`

### RTL Considerations

- Address layout: Use `flex flex-col` (symmetric)
- Breadcrumb: Auto-flip separator

### Accessibility

**ARIA Labels:**
```tsx
<Breadcrumb aria-label="Breadcrumb navigation">
  {/* Items */}
</Breadcrumb>
<Tabs aria-label="Site information tabs">
  {/* Tabs */}
</Tabs>
```

**Keyboard Navigation:**
- Arrow keys for tabs
- Tab for interactive elements

---

## 5. Assets Page

### Overview
**Purpose:** List all assets (filtered by company/site based on role).  
**URL:** `/assets`  
**Roles:** All roles (filtered by permission)  
**Layout:** Table with lifecycle badges

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Assets                                [+ Register Asset]    │
├────────────────────────────────────────────────────────────┤
│ [FilterBar: Search, Site, Type, Lifecycle Status]          │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Asset ID   │ Type      │ Site      │Lifecycle│ Age   │   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ HVAC-001   │ HVAC Unit │ Riyadh HQ │✓ Active │ 2.3yr │   │
│ │ HVAC-002   │ HVAC Unit │ Jeddah   │⚠ Warning│ 8.7yr │   │
│ │ ELEV-001   │ Elevator  │ Riyadh HQ │✓ Active │ 1.5yr │   │
│ │ GEN-001    │ Generator │ Dammam    │🔴 EOL   │ 12yr  │   │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Container:**
```tsx
<div className="space-y-6">
  <PageHeader 
    title="Assets" 
    action={<Button variant="primary">+ Register Asset</Button>}
  />
  <FilterBar
    showSearch
    showSiteFilter
    showCategoryFilter
    showLifecycleFilter
  />
  <DataTable columns={columns} data={assets} />
</div>
```

**Table Columns:**
1. **Asset ID** — Link to detail page, monospace
2. **Type/Category** — Text with icon
3. **Site** — Link to site detail
4. **Lifecycle Status** — Badge component (`AssetLifecycleBadge`)
5. **Age** — Calculated from installation date, color-coded
6. **Last Maintenance** — Relative time
7. **Actions** — Dropdown menu (View, Edit, Create WO, Decommission)

### Asset Lifecycle Badges

**Statuses:**
- **Active** (Green) — Asset operating normally, < 80% of expected lifespan
- **Warning** (Yellow) — Asset approaching end of life, 80-100% of expected lifespan
- **End of Life** (Red) — Asset exceeded expected lifespan, replacement recommended
- **Replaced** (Gray) — Asset decommissioned/replaced

**Age Color Coding:**
- < 3 years: `text-neutral-600` (normal)
- 3-5 years: `text-warning-dark` (approaching mid-life)
- 5-10 years: `text-warning-main` (aging)
- 10+ years: `text-error-main` (old)

### Filtering and Search

**Search Functionality:**
- Searches: Asset ID, type, category, site name, manufacturer
- Placeholder: "Search assets..."

**Filters:**
- **Site** — Dropdown (filtered by role)
- **Type** — Dropdown (HVAC, Elevator, Generator, Fire System, etc.)
- **Lifecycle Status** — Multi-select (Active, Warning, EOL, Replaced)
- **Age Range** — Slider (0-20 years)

### Actions

**Primary Actions:**
1. **Register Asset** — Opens modal with form (site, type, ID, installation date, expected lifespan)
2. **View Details** — Navigate to `/assets/:id`
3. **Create Work Order** — Quick WO creation for this asset
4. **Edit Asset** — Opens edit modal
5. **Decommission** — Confirmation dialog, marks as replaced

### Empty State

**No Assets Yet:**
```
┌────────────────────────────────────┐
│         [Package Icon]             │
│                                    │
│       No assets registered yet     │
│                                    │
│  Register your first asset to      │
│    start tracking lifecycle and    │
│        maintenance history         │
│                                    │
│      [+ Register First Asset]      │
└────────────────────────────────────┘
```

### Asset Detail Modal/Page Option

**Design Decision:**
- **Option A:** Dedicated page `/assets/:id` (recommended for rich lifecycle data)
- **Option B:** Modal overlay with asset detail (faster navigation)

**Recommendation:** Use dedicated page for asset lifecycle timeline visualization.

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Card view with lifecycle badge prominent |
| **Tablet (640px - 1024px)** | Table view with horizontal scroll |
| **Desktop (> 1024px)** | Full table view |

### Design Tokens

**Colors:**
- Asset ID: `text-primary-600 font-mono text-sm`
- Age warning: `text-warning-main`
- Age critical: `text-error-main`

**Typography:**
- Asset ID: `font-mono text-sm font-medium`
- Type: `text-sm text-neutral-700`
- Age: `text-sm font-medium`

**Spacing:**
- Table cell padding: `px-4 py-3`

### RTL Considerations

- Table columns: Use `text-start` for text alignment
- Badges: Centered content (no RTL impact)

### Accessibility

**ARIA Labels:**
```tsx
<AssetLifecycleBadge status="warning" aria-label="Asset lifecycle status: Warning, approaching end of life" />
<Link aria-label="View details for asset HVAC-001">HVAC-001</Link>
```

**Color Accessibility:**
- Lifecycle badges have text labels, not color-only
- Age color coding supplemented with text (e.g., "12yr (EOL)")

---

## 6. Asset Detail Page

### Overview
**Purpose:** View asset details with lifecycle timeline and maintenance history.  
**URL:** `/assets/:id`  
**Roles:** All roles (filtered by permission)  
**Layout:** Header + Lifecycle Timeline + Tabs

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Home > Assets > HVAC-001                                   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  HVAC Unit — HVAC-001                    [Edit] [Create WO]│
│  Riyadh HQ • ABC Facilities                               │
│  Status: ⚠ Warning • Age: 8.7 years • 87% of lifespan     │
│                                                            │
├────────────────────────────────────────────────────────────┤
│  Asset Lifecycle Timeline                                  │
│  ──○──────────○────────○──────⚠──○────────────────●──────│
│  Installed  1yr       3yr     6yr  8yr (now)     10yr (EOL)│
│  2015-06    Maint.   Repair  Major Last Maint.  Expected   │
│                              Repair                         │
├────────────────────────────────────────────────────────────┤
│ ⚠️ Warning: Asset is 87% through expected lifespan         │
│    Replacement work order recommended.                     │
│    [Create Replacement WO]                                 │
├──────────┬─────────────┬──────────────────────────────────│
│Details   │Maintenance  │Work Orders                        │
├──────────┴─────────────┴──────────────────────────────────│
│                                                            │
│  Asset Information                                         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Asset ID:          HVAC-001                          │ │
│  │ Type:              HVAC Unit                         │ │
│  │ Manufacturer:      Carrier                           │ │
│  │ Model:             30RB-080                          │ │
│  │ Serial Number:     ABC123XYZ                         │ │
│  │ Installation Date: 2015-06-15                        │ │
│  │ Expected Lifespan: 10 years                          │ │
│  │ Current Age:       8.7 years                         │ │
│  │ Location:          Riyadh HQ > Building A > Roof     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Structure:**
```tsx
<div className="space-y-6">
  <Breadcrumb items={breadcrumbItems} />
  
  <PageHeader
    title={`${asset.type} — ${asset.asset_id}`}
    subtitle={`${asset.site_name} • ${asset.company_name}`}
    actions={
      <>
        <Button variant="secondary">Edit</Button>
        <Button variant="primary">Create Work Order</Button>
      </>
    }
  />
  
  <StatusBar>
    <AssetLifecycleBadge status={asset.lifecycle_status} />
    <Stat label="Age" value={`${asset.age_years} years`} />
    <Stat label="Lifespan Used" value={`${asset.lifespan_percentage}%`} />
    <Stat label="Last Maintenance" value={asset.last_maintenance_relative} />
  </StatusBar>
  
  <AssetLifecycleTimeline asset={asset} />
  
  {asset.lifecycle_status === "warning" && (
    <Alert variant="warning">
      ⚠️ Warning: Asset is {asset.lifespan_percentage}% through expected lifespan.
      Replacement work order recommended.
      <Button variant="secondary" size="sm">Create Replacement WO</Button>
    </Alert>
  )}
  
  {asset.lifecycle_status === "end_of_life" && (
    <Alert variant="error">
      🔴 End of Life: Asset has exceeded expected lifespan.
      {asset.replacement_wo_id && (
        <p>Replacement work order: <Link to={`/work-orders/${asset.replacement_wo_id}`}>View WO</Link></p>
      )}
      {!asset.replacement_wo_id && (
        <Button variant="primary" size="sm">Create Replacement WO</Button>
      )}
    </Alert>
  )}
  
  <Tabs defaultTab="details">
    <Tab id="details" label="Details">
      <AssetDetails asset={asset} />
    </Tab>
    <Tab id="maintenance" label="Maintenance History">
      <MaintenanceHistory assetId={asset.id} />
    </Tab>
    <Tab id="work-orders" label="Work Orders">
      <WorkOrdersTable assetId={asset.id} />
    </Tab>
  </Tabs>
</div>
```

### Asset Lifecycle Timeline

**Visual Component:**
```
Timeline (Horizontal)
──────○──────────○────────○──────⚠──○────────────────●──────
      ↓          ↓        ↓      ↓  ↓                ↓
   Installed   1yr      3yr    6yr 8yr              10yr
   2015-06    Maint.   Repair Major Last          Expected
                              Repair Maint.           EOL
```

**Timeline Events:**
- **Installation** (circle) — Asset registered
- **Maintenance** (circle) — Routine maintenance WO completed
- **Repair** (circle) — Corrective repair WO completed
- **Major Repair** (circle with star) — High-cost repair
- **Current Position** (animated pulse) — "You are here"
- **Expected EOL** (red marker) — End of expected lifespan

**Color Coding:**
- Past events: `text-neutral-500`
- Current position: `text-primary-600` (animated pulse)
- Warning zone (80-100%): `text-warning-main`
- EOL marker: `text-error-main`

**Implementation Notes:**
- Use SVG for timeline visualization
- Responsive: Stack vertically on mobile
- Tooltip on hover: Event date, WO ID, cost

### Key Information Displayed

**Details Tab:**
1. Asset ID (monospace)
2. Type/Category
3. Manufacturer
4. Model number
5. Serial number
6. Installation date
7. Expected lifespan (years)
8. Current age (calculated)
9. Location (hierarchical path)
10. QR code (for scanning on-site)

**Maintenance History Tab:**
- Table of all maintenance WOs for this asset
- Columns: Date, Type (preventive/corrective), Description, Cost, Technician
- Sortable by date
- Filter by type

**Work Orders Tab:**
- All WOs related to this asset (active and historical)
- Same table as Work Orders page, filtered by asset

### Actions

**Primary Actions:**
1. **Edit Asset** — Opens modal with editable fields
2. **Create Work Order** — Opens WO creation modal with asset pre-selected
3. **Create Replacement WO** — Auto-creates replacement WO (for EOL assets)
4. **Decommission** — Marks asset as replaced, requires replacement asset ID

**Secondary Actions:**
5. **View QR Code** — Modal with printable QR code
6. **Export History** — Download CSV of maintenance history
7. **View Location** — Navigate to location detail page

### Empty State (Maintenance History Tab)

```
┌────────────────────────────────────┐
│         [Wrench Icon]              │
│                                    │
│   No maintenance history yet       │
│                                    │
│  Maintenance records will appear   │
│   here as work orders are completed│
│                                    │
└────────────────────────────────────┘
```

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Timeline vertical, tabs scroll horizontally |
| **Tablet (640px - 1024px)** | Timeline horizontal, tabs full width |
| **Desktop (> 1024px)** | Full layout |

### Design Tokens

**Colors:**
- Timeline line: `border-neutral-300`
- Timeline events: `bg-primary-500` (circle)
- Current position: `bg-primary-600` with pulse animation
- Warning zone: `bg-warning-light`
- EOL marker: `bg-error-main`
- Alert background: `bg-warning-light` or `bg-error-light`

**Typography:**
- Asset ID: `font-mono text-xl font-semibold text-neutral-900`
- Subtitle: `text-base text-neutral-600`
- Timeline labels: `text-xs text-neutral-500`

**Spacing:**
- Timeline height: `h-20` on desktop, `h-auto` on mobile
- Alert padding: `p-4`

### RTL Considerations

- Timeline: Flip direction (right-to-left for RTL)
- Details table: Use `text-start` for alignment

### Accessibility

**ARIA Labels:**
```tsx
<Timeline aria-label="Asset lifecycle timeline from installation to end of life">
  <TimelineEvent aria-label="Installation on June 15, 2015">
    {/* Event details */}
  </TimelineEvent>
</Timeline>
```

**Keyboard Navigation:**
- Timeline events focusable
- Tooltip on focus (not just hover)

---

## 7. Employees Page

### Overview
**Purpose:** Manage users/employees with role assignment.  
**URL:** `/employees`  
**Roles:** super_admin, company_admin  
**Layout:** Table with role badges and filters

### Visual Hierarchy

```
┌────────────────────────────────────────────────────────────┐
│ Employees                              [+ Create Employee]  │
├────────────────────────────────────────────────────────────┤
│ [FilterBar: Search, Role, Status]                          │
├────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────┐   │
│ │ Name          │ Email          │ Role         │Status│   │
│ ├──────────────────────────────────────────────────────┤   │
│ │ Ahmed Ali     │ ahmed@fms.com  │ Technician   │●Active│  │
│ │ Sara Ibrahim  │ sara@fms.com   │ Site Manager │●Active│  │
│ │ Mohammed Khan │ khan@fms.com   │ Technician   │●Active│  │
│ │ Fatima Ahmed  │ fatima@fms.com │ Client Admin │●Active│  │
│ └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Layout Specifications

**Page Container:**
```tsx
<div className="space-y-6">
  <PageHeader 
    title="Employees" 
    action={<Button variant="primary">+ Create Employee</Button>}
  />
  <FilterBar
    showSearch
    showRoleFilter
    showStatusFilter
  />
  <DataTable columns={columns} data={employees} />
</div>
```

**Table Columns:**
1. **Name** — Link to user detail/edit
2. **Email** — Text
3. **Phone** — Text (optional)
4. **Role** — Badge component
5. **Assigned Sites** — Comma-separated site names (for technicians/site managers)
6. **Status** — Badge (Active/Inactive)
7. **Actions** — Dropdown menu (Edit, Change Role, Deactivate, Reset Password)

### Role Badges

**Roles:**
- **Super Admin** — `bg-purple-100 text-purple-700`
- **Company Admin** — `bg-blue-100 text-blue-700`
- **Client Admin** — `bg-teal-100 text-teal-700`
- **Site Manager** — `bg-green-100 text-green-700`
- **Technician** — `bg-orange-100 text-orange-700`

**Badge Style:**
```tsx
<span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClass}`}>
  {role}
</span>
```

### User Creation Form

**Modal Content:**
```tsx
<Modal title="Create Employee">
  <Form>
    <FormField label="Name" type="text" required />
    <FormField label="Email" type="email" required />
    <FormField label="Phone" type="tel" />
    <FormField label="Role" type="select" options={roles} required />
    
    {role === "technician" || role === "site_manager" ? (
      <FormField label="Assigned Sites" type="multiselect" options={sites} />
    ) : null}
    
    <FormField label="Initial Password" type="password" required />
    <FormField label="Send Welcome Email" type="checkbox" defaultChecked />
    
    <ButtonGroup>
      <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      <Button variant="primary" type="submit">Create Employee</Button>
    </ButtonGroup>
  </Form>
</Modal>
```

### Filtering and Search

**Search Functionality:**
- Searches: Name, email, phone
- Placeholder: "Search employees..."

**Filters:**
- **Role** — Multi-select (all roles)
- **Status** — Active/Inactive
- **Assigned Site** — Dropdown (for technicians/site managers)

### Actions

**Primary Actions:**
1. **Create Employee** — Opens modal with form
2. **Edit Employee** — Opens edit modal
3. **Change Role** — Opens role assignment modal
4. **Deactivate/Activate** — Toggle status
5. **Reset Password** — Sends password reset email

**Bulk Actions (Future):**
- Select multiple → Export CSV
- Select multiple → Bulk role change
- Select multiple → Bulk deactivate

### Empty State

**No Employees Yet:**
```
┌────────────────────────────────────┐
│         [Users Icon]               │
│                                    │
│      No employees registered yet   │
│                                    │
│   Add your first employee to       │
│   start assigning work orders      │
│                                    │
│     [+ Create First Employee]      │
└────────────────────────────────────┘
```

### Role Assignment Interface

**Change Role Modal:**
```tsx
<Modal title="Change Role for Ahmed Ali">
  <Form>
    <FormField label="Current Role" value="Technician" disabled />
    <FormField label="New Role" type="select" options={roles} required />
    
    {newRole === "technician" || newRole === "site_manager" ? (
      <FormField label="Assigned Sites" type="multiselect" options={sites} />
    ) : null}
    
    <Alert variant="warning">
      ⚠️ Changing role will affect user permissions immediately.
    </Alert>
    
    <ButtonGroup>
      <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      <Button variant="primary" type="submit">Change Role</Button>
    </ButtonGroup>
  </Form>
</Modal>
```

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | Card view, role badge prominent |
| **Tablet (640px - 1024px)** | Table view with horizontal scroll |
| **Desktop (> 1024px)** | Full table view |

### Design Tokens

**Colors:**
- Role badges: Defined above
- Status active: `text-success-main`
- Status inactive: `text-neutral-500`

**Typography:**
- Name: `text-base font-medium text-neutral-900`
- Email: `text-sm text-neutral-600`
- Role badge: `text-xs font-medium`

**Spacing:**
- Table cell padding: `px-4 py-3`

### RTL Considerations

- Table columns: Use `text-start`
- Role badges: Centered (no RTL impact)

### Accessibility

**ARIA Labels:**
```tsx
<Button aria-label="Create new employee">+ Create Employee</Button>
<Link aria-label="Edit employee Ahmed Ali">Edit</Link>
<select aria-label="Filter by role">
  <option>All Roles</option>
</select>
```

**Keyboard Navigation:**
- Tab through table rows
- Enter to edit

---

## 8. Welcome/Dashboard Page

### Overview
**Purpose:** Role-specific landing page with quick stats and actions.  
**URL:** `/` or `/dashboard`  
**Roles:** All roles (different layouts)  
**Layout:** Card grid with widgets

### Role-Specific Layouts

#### Super Admin / Company Admin Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ Welcome, Ahmed Ali                                         │
│ Super Admin                                                │
├────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│ │ Companies   │ │ Active WOs  │ │ Open Invoices│ │Techs  ││
│ │     24      │ │     48      │ │   SAR 125k   │ │  15   ││
│ │ ↑ 2 new     │ │ ↓ 12 less   │ │ ↑ SAR 25k    │ │ 3 busy││
│ └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
├────────────────────────────────────────────────────────────┤
│ Recent Work Orders                          [View All →]   │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ WO-001 │ HVAC Repair      │ Riyadh HQ   │ Urgent    │   │
│ │ WO-002 │ Elevator Service │ Jeddah      │ Normal    │   │
│ │ WO-003 │ Fire System Test │ Dammam      │ Emergency │   │
│ └──────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│ Quick Actions                                              │
│ [+ Create Work Order] [+ Add Company] [+ Register Asset]   │
└────────────────────────────────────────────────────────────┘
```

**Widgets:**
1. **Companies Count** — Total companies, change from last month
2. **Active Work Orders** — Current open WOs, change indicator
3. **Open Invoices** — Total amount pending, change indicator
4. **Technicians** — Total techs, how many currently busy
5. **Recent Work Orders** — Last 5 WOs across all companies
6. **Quick Actions** — Common admin actions

#### Technician Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ Welcome, Mohammed Khan                                     │
│ Technician                                                 │
├────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│ │ My Tasks    │ │ In Progress │ │ Completed   │          │
│ │     5       │ │     2       │ │   12 (week) │          │
│ │ 2 urgent    │ │             │ │             │          │
│ └─────────────┘ └─────────────┘ └─────────────┘          │
├────────────────────────────────────────────────────────────┤
│ My Work Orders                          [View All →]       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ☐ WO-001 │ HVAC Repair      │ Riyadh HQ   │🔴 Urgent │  │
│ │ ☐ WO-003 │ Fire System Test │ Dammam      │🔴Emergency│  │
│ │ ✓ WO-002 │ Elevator Service │ Jeddah      │ Normal    │   │
│ └──────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│ Today's Schedule                                           │
│ 09:00 - WO-001 @ Riyadh HQ (HVAC Repair)                  │
│ 14:00 - WO-003 @ Dammam (Fire System Test)                │
└────────────────────────────────────────────────────────────┘
```

**Widgets:**
1. **My Tasks** — Assigned to me, not started
2. **In Progress** — Currently working on
3. **Completed This Week** — Count
4. **My Work Orders** — Task list with checkboxes
5. **Today's Schedule** — Time-ordered list of assigned WOs

#### Client Admin Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ Welcome, Fatima Ahmed                                      │
│ ABC Facilities — Client Admin                              │
├────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│ │ Sites       │ │ Active WOs  │ │ Pending     │          │
│ │     12      │ │     8       │ │ Invoices    │          │
│ │             │ │ 2 overdue   │ │  SAR 45k    │          │
│ └─────────────┘ └─────────────┘ └─────────────┘          │
├────────────────────────────────────────────────────────────┤
│ Work Orders by Status                                      │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ █████░░░░░ Completed (60%)                           │   │
│ │ ███░░░░░░░ In Progress (30%)                         │   │
│ │ ██░░░░░░░░ Pending (10%)                             │   │
│ └──────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│ Recent Activity                                            │
│ • WO-001 marked as Completed (2 hours ago)                │
│ • Invoice INV-123 generated (1 day ago)                   │
│ • New site added: Riyadh Branch 2 (3 days ago)            │
└────────────────────────────────────────────────────────────┘
```

**Widgets:**
1. **Sites Count** — Total sites for this company
2. **Active Work Orders** — Current open WOs, overdue count
3. **Pending Invoices** — Total amount pending payment
4. **Work Orders by Status** — Horizontal bar chart
5. **Recent Activity Feed** — Last 10 events across company

#### Site Manager Dashboard

```
┌────────────────────────────────────────────────────────────┐
│ Welcome, Sara Ibrahim                                      │
│ Riyadh HQ — Site Manager                                   │
├────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│ │ Assets      │ │ Active WOs  │ │ Overdue     │          │
│ │     45      │ │     3       │ │ Maintenance │          │
│ │ 2 at EOL    │ │ 1 urgent    │ │      1      │          │
│ └─────────────┘ └─────────────┘ └─────────────┘          │
├────────────────────────────────────────────────────────────┤
│ Assets by Lifecycle Status                                 │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ● Active (38)   ● Warning (5)   ● EOL (2)           │   │
│ └──────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────┤
│ Upcoming Maintenance                                       │
│ • HVAC-001 preventive maintenance due in 3 days           │
│ • ELEV-001 inspection due next week                       │
└────────────────────────────────────────────────────────────┘
```

**Widgets:**
1. **Assets Count** — Total assets at this site, EOL count
2. **Active Work Orders** — Current open WOs, urgent count
3. **Overdue Maintenance** — Count of assets overdue for maintenance
4. **Assets by Lifecycle** — Pie chart or count badges
5. **Upcoming Maintenance** — Next 5 scheduled maintenance tasks

### Layout Specifications

**Page Structure:**
```tsx
<div className="space-y-6">
  <PageHeader
    title={`Welcome, ${user.name}`}
    subtitle={roleLabel}
  />
  
  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <StatCard label="Companies" value={24} change="+2" />
    <StatCard label="Active WOs" value={48} change="-12" trend="down" />
    <StatCard label="Open Invoices" value="SAR 125k" change="+SAR 25k" />
    <StatCard label="Technicians" value={15} subtitle="3 busy" />
  </div>
  
  <Card>
    <CardHeader title="Recent Work Orders" action={<Link>View All →</Link>} />
    <DataTable columns={recentWOColumns} data={recentWOs} compact />
  </Card>
  
  <div className="flex flex-wrap gap-3">
    <Button variant="primary">+ Create Work Order</Button>
    <Button variant="secondary">+ Add Company</Button>
    <Button variant="secondary">+ Register Asset</Button>
  </div>
</div>
```

**Stat Card:**
```tsx
<Card className="p-6 hover:border-primary-300 transition-colors">
  <p className="text-sm text-neutral-500">{label}</p>
  <p className="text-3xl font-bold text-primary-600">{value}</p>
  {change && (
    <p className={`text-xs ${trend === 'up' ? 'text-success-main' : 'text-error-main'}`}>
      {trend === 'up' ? '↑' : '↓'} {change}
    </p>
  )}
  {subtitle && <p className="text-xs text-neutral-600">{subtitle}</p>}
</Card>
```

### Quick Actions by Role

| Role | Quick Actions |
|------|---------------|
| **Super Admin** | Create WO, Add Company, Register Asset, Add Employee, View Reports |
| **Company Admin** | Create WO, Add Site, Register Asset, Add Employee |
| **Client Admin** | Create WO, View Invoices, View Reports |
| **Site Manager** | Create WO, Register Asset, Schedule Maintenance |
| **Technician** | View My Tasks, Start Work, Complete Report |

### Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| **Mobile (< 640px)** | 1 column, stat cards stack vertically |
| **Tablet (640px - 1024px)** | 2 column grid for stats, cards full width |
| **Desktop (> 1024px)** | 4 column grid for stats, 2 column for larger cards |

### Design Tokens

**Colors:**
- Stat card value: `text-3xl font-bold text-primary-600`
- Change indicator (up): `text-success-main`
- Change indicator (down): `text-error-main`
- Card hover: `hover:border-primary-300`

**Typography:**
- Welcome title: `text-3xl font-semibold text-neutral-900`
- Role subtitle: `text-lg text-neutral-600`
- Stat label: `text-sm text-neutral-500`
- Stat value: `text-3xl font-bold`

**Spacing:**
- Page container: `space-y-6`
- Stat grid gap: `gap-4`
- Card padding: `p-6`

### RTL Considerations

- Grid layout: Symmetric (no RTL impact)
- Change indicators: Use `↑`/`↓` (universal)

### Accessibility

**ARIA Labels:**
```tsx
<Card aria-label="Companies statistic">
  <Stat label="Companies" value={24} />
</Card>
```

**Keyboard Navigation:**
- Tab through stat cards (if clickable)
- Quick action buttons fully keyboard accessible

---

## 9. Sidebar Navigation

### Overview
**Purpose:** Primary navigation for all pages.  
**Location:** Left side (LTR), Right side (RTL)  
**Layout:** Fixed sidebar on desktop, hamburger on mobile

### Visual Hierarchy (Desktop)

```
┌──────────────────┐
│  [FMS Logo]      │ ← Header (80px height)
├──────────────────┤
│                  │
│ 🏠 Dashboard     │ ← Active (blue bg)
│ 🏢 Companies     │
│ 📍 Sites         │
│ 📦 Assets        │
│ 👥 Employees     │
│ 📋 Work Orders   │
│ 💰 Invoices      │
│                  │
├──────────────────┤
│ ⚙️ Settings      │ ← Bottom section
│ 👤 Profile       │
│ 🚪 Logout        │
└──────────────────┘
    240px width
```

### Layout Specifications

**Sidebar Structure:**
```tsx
<aside className="fixed inset-y-0 start-0 z-40 w-60 bg-neutral-0 border-e border-neutral-200">
  {/* Header */}
  <div className="flex h-20 items-center justify-center border-b border-neutral-200">
    <Logo />
  </div>
  
  {/* Navigation */}
  <nav className="flex-1 overflow-y-auto p-4" aria-label="Main navigation">
    <NavSection>
      <NavItem href="/" icon={<HomeIcon />} active>Dashboard</NavItem>
      <NavItem href="/companies" icon={<BuildingIcon />}>Companies</NavItem>
      <NavItem href="/sites" icon={<MapPinIcon />}>Sites</NavItem>
      <NavItem href="/assets" icon={<PackageIcon />}>Assets</NavItem>
      <NavItem href="/employees" icon={<UsersIcon />}>Employees</NavItem>
      <NavItem href="/work-orders" icon={<ClipboardIcon />}>Work Orders</NavItem>
      <NavItem href="/invoices" icon={<DollarIcon />}>Invoices</NavItem>
    </NavSection>
  </nav>
  
  {/* Footer */}
  <div className="border-t border-neutral-200 p-4">
    <NavItem href="/settings" icon={<SettingsIcon />}>Settings</NavItem>
    <NavItem href="/profile" icon={<UserIcon />}>Profile</NavItem>
    <NavItem onClick={handleLogout} icon={<LogoutIcon />}>Logout</NavItem>
  </div>
</aside>
```

**Nav Item:**
```tsx
<Link
  href={href}
  className={`
    flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium
    transition-colors
    ${active 
      ? 'bg-primary-600 text-white' 
      : 'text-neutral-700 hover:bg-neutral-100'
    }
  `}
>
  <span className="w-5 h-5">{icon}</span>
  <span>{children}</span>
</Link>
```

### Responsive Behavior

#### Desktop (> 1024px)
- **Fixed sidebar:** 240px width, always visible
- **Main content:** `ms-60` (offset by sidebar width)

#### Tablet (768px - 1024px)
- **Icon-only sidebar:** 60px width, collapse text labels
- **Show labels on hover** (optional)
- **Main content:** `ms-15` (offset by icon sidebar width)

#### Mobile (< 768px)
- **Hidden sidebar:** Hamburger menu button in header
- **Overlay sidebar:** Slides in from start, full-width, backdrop overlay
- **Close button:** X button in sidebar header
- **Main content:** Full width, no offset

**Mobile Sidebar:**
```tsx
{/* Mobile: Hamburger button */}
<button
  className="lg:hidden fixed top-4 start-4 z-50"
  onClick={() => setSidebarOpen(true)}
  aria-label="Open navigation menu"
>
  <MenuIcon className="w-6 h-6" />
</button>

{/* Mobile: Overlay sidebar */}
{sidebarOpen && (
  <>
    {/* Backdrop */}
    <div
      className="fixed inset-0 z-40 bg-black/50 lg:hidden"
      onClick={() => setSidebarOpen(false)}
    />
    
    {/* Sidebar */}
    <aside className="fixed inset-y-0 start-0 z-50 w-64 bg-neutral-0 lg:hidden">
      {/* Close button */}
      <button
        className="absolute top-4 end-4"
        onClick={() => setSidebarOpen(false)}
        aria-label="Close navigation menu"
      >
        <XIcon className="w-6 h-6" />
      </button>
      
      {/* Nav content (same as desktop) */}
    </aside>
  </>
)}
```

### Role-Specific Navigation

**Navigation Items by Role:**

| Item | super_admin | company_admin | client_admin | site_manager | technician |
|------|-------------|---------------|--------------|--------------|------------|
| Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| Companies | ✓ | ✓ | ✗ | ✗ | ✗ |
| Sites | ✓ | ✓ | ✓ | ✗ | ✗ |
| Assets | ✓ | ✓ | ✓ | ✓ | ✗ |
| Employees | ✓ | ✓ | ✗ | ✗ | ✗ |
| Work Orders | ✓ | ✓ | ✓ | ✓ | ✓ (My WOs) |
| Invoices | ✓ | ✓ | ✓ | ✗ | ✗ |
| Labor | ✓ | ✓ | ✗ | ✗ | ✗ |
| Reports | ✓ | ✓ | ✓ | ✓ | ✗ |
| Settings | ✓ | ✓ | ✓ | ✓ | ✓ |

### Active State

**Indicators:**
- **Background:** `bg-primary-600` (active), `bg-transparent` (inactive)
- **Text:** `text-white` (active), `text-neutral-700` (inactive)
- **Icon:** Same color as text
- **Border:** `border-s-4 border-primary-600` (alternative, not used here)

### Hover State

**Inactive Items:**
- Background: `hover:bg-neutral-100`
- Text: No color change
- Cursor: `cursor-pointer`

### Design Tokens

**Colors:**
- Sidebar background: `bg-neutral-0`
- Border: `border-neutral-200`
- Active item background: `bg-primary-600`
- Active item text: `text-white`
- Inactive item text: `text-neutral-700`
- Hover background: `hover:bg-neutral-100`

**Typography:**
- Nav item text: `text-sm font-medium`
- Logo text: `text-xl font-bold text-primary-600`

**Spacing:**
- Sidebar width: `w-60` (240px)
- Icon sidebar width: `w-15` (60px)
- Nav item padding: `px-3 py-2.5`
- Nav item gap: `gap-3`
- Section spacing: `space-y-1`

### RTL Considerations

**Positioning:**
- LTR: `start-0` → `left: 0`
- RTL: `start-0` → `right: 0`
- Border: `border-e` → `border-right` (LTR), `border-left` (RTL)

**Icon Flipping:**
- Most icons: No flip needed
- Directional icons (arrows): Flip horizontally in RTL

### Accessibility

**ARIA Labels:**
```tsx
<nav aria-label="Main navigation">
  <Link href="/" aria-current={active ? "page" : undefined}>
    Dashboard
  </Link>
</nav>
```

**Keyboard Navigation:**
- Tab through nav items
- Enter/Space to activate link
- Escape to close mobile sidebar
- Focus trap in mobile sidebar (when open)

**Screen Reader:**
- Sidebar has `<nav>` semantic element
- Active item has `aria-current="page"`
- Mobile toggle has `aria-label="Open navigation menu"`
- Mobile close has `aria-label="Close navigation menu"`

---

## 10. Breadcrumb Navigation

### Overview
**Purpose:** Show hierarchical location and allow quick navigation up the hierarchy.  
**Location:** Top of page content, below sidebar/header  
**Layout:** Horizontal list with separators

### Visual Hierarchy

```
Home > Companies > ABC Facilities > Sites > Riyadh HQ
```

### Layout Specifications

**Breadcrumb Structure:**
```tsx
<nav aria-label="Breadcrumb" className="mb-4">
  <ol className="flex items-center gap-2 text-sm text-neutral-600">
    <li>
      <Link href="/" className="hover:text-primary-600 transition-colors">
        Home
      </Link>
    </li>
    <li aria-hidden="true" className="text-neutral-400">›</li>
    <li>
      <Link href="/companies" className="hover:text-primary-600 transition-colors">
        Companies
      </Link>
    </li>
    <li aria-hidden="true" className="text-neutral-400">›</li>
    <li>
      <Link href="/companies/abc-123" className="hover:text-primary-600 transition-colors">
        ABC Facilities
      </Link>
    </li>
    <li aria-hidden="true" className="text-neutral-400">›</li>
    <li>
      <Link href="/companies/abc-123/sites" className="hover:text-primary-600 transition-colors">
        Sites
      </Link>
    </li>
    <li aria-hidden="true" className="text-neutral-400">›</li>
    <li aria-current="page" className="font-medium text-neutral-900">
      Riyadh HQ
    </li>
  </ol>
</nav>
```

**Breadcrumb Component:**
```tsx
interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-2 text-sm text-neutral-600">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {item.active ? (
              <span className="font-medium text-neutral-900" aria-current="page">
                {item.label}
              </span>
            ) : (
              <Link
                href={item.href!}
                className="hover:text-primary-600 transition-colors"
              >
                {item.label}
              </Link>
            )}
            {index < items.length - 1 && (
              <span aria-hidden="true" className="text-neutral-400">›</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
```

### Separator Options

**Separator Styles:**
- **Chevron:** `›` (recommended, clear hierarchy)
- **Slash:** `/` (compact, less clear)
- **Arrow:** `→` (directional, good for LTR only)
- **Dash:** `-` (minimal, less clear)

**Recommendation:** Use `›` chevron, auto-flips in RTL to `‹`

### Responsive Behavior

#### Desktop (> 1024px)
- Full breadcrumb visible

#### Tablet (640px - 1024px)
- Full breadcrumb with ellipsis if too long
- Example: `Home > ... > Sites > Riyadh HQ`

#### Mobile (< 640px)
- **Option A:** Show only last 2 items: `Sites > Riyadh HQ`
- **Option B:** Show all with horizontal scroll
- **Recommendation:** Show last 2 items + ellipsis for long paths

**Mobile Breadcrumb:**
```tsx
{/* Mobile: Show last 2 items */}
<nav aria-label="Breadcrumb" className="mb-4">
  <ol className="flex items-center gap-2 text-sm text-neutral-600">
    {items.length > 2 && (
      <>
        <li>
          <button
            onClick={showFullBreadcrumb}
            className="text-neutral-400 hover:text-primary-600"
            aria-label="Show full breadcrumb"
          >
            ...
          </button>
        </li>
        <li aria-hidden="true" className="text-neutral-400">›</li>
      </>
    )}
    {items.slice(-2).map((item, index) => (
      <li key={index} className="flex items-center gap-2">
        {/* Item content */}
      </li>
    ))}
  </ol>
</nav>
```

### Hierarchy Examples

**Common Breadcrumb Paths:**

1. **Company Detail:**
   - `Home > Companies > ABC Facilities`

2. **Site Detail (from company):**
   - `Home > Companies > ABC Facilities > Sites > Riyadh HQ`

3. **Asset Detail:**
   - `Home > Assets > HVAC-001`
   - OR (context-aware):
   - `Home > Sites > Riyadh HQ > Assets > HVAC-001`

4. **Work Order Detail:**
   - `Home > Work Orders > WO-001`
   - OR (context-aware):
   - `Home > Sites > Riyadh HQ > Work Orders > WO-001`

5. **Employee Detail:**
   - `Home > Employees > Ahmed Ali`

**Context-Aware Breadcrumbs:**
- If navigating from Company → Site → Asset, show full path
- If navigating directly to Asset, show shortened path
- Use referrer or route context to determine path

### Design Tokens

**Colors:**
- Link text: `text-neutral-600 hover:text-primary-600`
- Active item: `text-neutral-900 font-medium`
- Separator: `text-neutral-400`

**Typography:**
- Font size: `text-sm`
- Link weight: `font-normal`
- Active weight: `font-medium`

**Spacing:**
- Gap between items: `gap-2`
- Margin bottom: `mb-4`

### RTL Considerations

**Separator Flipping:**
- LTR: `›` (right-pointing chevron)
- RTL: `‹` (left-pointing chevron)
- Implementation: Use CSS `transform: scaleX(-1)` in RTL

```css
[dir="rtl"] .breadcrumb-separator {
  transform: scaleX(-1);
}
```

**Order:**
- LTR: `Home > Companies > ABC`
- RTL: `ABC < Companies < Home` (reversed visually, same markup)

### Accessibility

**ARIA Labels:**
```tsx
<nav aria-label="Breadcrumb">
  <ol>
    <li>
      <a href="/">Home</a>
    </li>
    <li>
      <span aria-current="page">Current Page</span>
    </li>
  </ol>
</nav>
```

**Semantic Markup:**
- Use `<nav>` with `aria-label="Breadcrumb"`
- Use `<ol>` for ordered list of links
- Use `aria-current="page"` for active item
- Use `aria-hidden="true"` for separators

**Keyboard Navigation:**
- Tab through links
- Skip separators (not focusable)

**Screen Reader:**
- Announces: "Breadcrumb navigation"
- Announces each link
- Announces "current page" for active item
- Skips separators (aria-hidden)

---

## Summary of UI Specifications

This document provides detailed specifications for 10 key UI elements needed for Phase 2:

1. ✅ **Companies Page** — List view with filters, card/table layout
2. ✅ **Company Detail Page** — Hierarchical detail with nested sites
3. ✅ **Sites Page** — Card grid with QR codes
4. ✅ **Site Detail Page** — Nested assets and WOs
5. ✅ **Assets Page** — Lifecycle-aware table view
6. ✅ **Asset Detail Page** — Lifecycle timeline visualization
7. ✅ **Employees Page** — User management with role badges
8. ✅ **Welcome/Dashboard Page** — Role-specific widgets
9. ✅ **Sidebar Navigation** — Responsive, role-based
10. ✅ **Breadcrumb Navigation** — Hierarchical context

**Next Steps:**
1. Review and approve specifications
2. Create wireframes for Companies Detail, Asset Detail, and Welcome pages
3. Implement core component library (Button, Modal, Card, Badge, etc.)
4. Implement sidebar navigation
5. Implement breadcrumb component
6. Build pages iteratively

**Estimated Implementation Time:**
- Core components: 3-4 days
- Sidebar + breadcrumb: 2-3 days
- Pages (10 pages): 5-7 days
- **Total:** 10-14 days of frontend development
