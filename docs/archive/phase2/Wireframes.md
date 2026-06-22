# Wireframes — FMS Phase 2

**Version:** 1.0  
**Date:** 2026-04-17  
**Pages:** Company Detail, Asset Detail, Welcome Dashboard

This document provides detailed ASCII wireframes for the 3 most critical pages in Phase 2, showing layout, component placement, and responsive behavior.

---

## Table of Contents

1. [Company Detail Page](#1-company-detail-page)
2. [Asset Detail Page](#2-asset-detail-page)
3. [Welcome Dashboard Page](#3-welcome-dashboard-page)

---

## 1. Company Detail Page

### Desktop Layout (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                         │
│ │          │  Home > Companies > ABC Facilities                                      │
│ │          │                                                                         │
│ │  FMS     │  ┌────────────────────────────────────────────────────────────────┐   │
│ │  Logo    │  │                                                                  │   │
│ │          │  │  ABC Facilities                          [Edit] [Archive]       │   │
│ ├──────────┤  │  contact@abc.com • +966 12 345 6789                            │   │
│ │          │  │                                                                  │   │
│ │ 🏠 Dash  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐                │   │
│ │ 🏢 Comp* │  │  │ ● Active   │ │  12 Sites  │ │  8 Active  │                │   │
│ │ 📍 Sites │  │  │            │ │            │ │   WOs      │                │   │
│ │ 📦 Asset │  │  └────────────┘ └────────────┘ └────────────┘                │   │
│ │ 👥 Emplo │  │                                                                  │   │
│ │ 📋 WOs   │  └────────────────────────────────────────────────────────────────┘   │
│ │ 💰 Invoi │                                                                         │
│ │          │  ┌──────┬──────────┬──────────┬──────────┬──────────────────────┐   │
│ │          │  │Sites*│Work Orders│Invoices  │Settings  │                      │   │
│ │          │  ├──────┴──────────┴──────────┴──────────┴──────────────────────┤   │
│ │          │  │                                                                │   │
│ │          │  │  [Search sites...]                        [+ Add Site]        │   │
│ │          │  │                                                                │   │
│ │          │  │  ┌──────────────────────────────────────────────────────────┐ │   │
│ │          │  │  │ Site Name         │ Location      │ Assets │ Active WOs  │ │   │
│ │          │  │  ├──────────────────────────────────────────────────────────┤ │   │
│ │          │  │  │ Riyadh HQ         │ Riyadh, SA    │   45   │     3       │ │   │
│ │          │  │  │ Jeddah Branch     │ Jeddah, SA    │   32   │     2       │ │   │
│ │          │  │  │ Dammam Office     │ Dammam, SA    │   28   │     3       │ │   │
│ │          │  │  │ Mecca Facility    │ Mecca, SA     │   18   │     0       │ │   │
│ │          │  │  │ Medina Center     │ Medina, SA    │   25   │     1       │ │   │
│ │          │  │  └──────────────────────────────────────────────────────────┘ │   │
│ │          │  │                                                                │   │
│ ├──────────┤  │                                                                │   │
│ │ ⚙️ Setti │  │                                                                │   │
│ │ 👤 Profi │  │                                                                │   │
│ │ 🚪 Logou │  │                                                                │   │
│ └──────────┘  └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│ 240px          Main Content Area (Offset by 240px)                                  │
│ Sidebar                                                                              │
└──────────────────────────────────────────────────────────────────────────────────────┘

* Active page/tab indicator
```

### Tablet Layout (768px - 1024px)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ┌──┐                                                                   │
│ │🏠│  Home > Companies > ABC Facilities                                │
│ │🏢│                                                                   │
│ │📍│  ┌──────────────────────────────────────────────────────────┐   │
│ │📦│  │                                                            │   │
│ │👥│  │  ABC Facilities               [Edit] [Archive]           │   │
│ │📋│  │  contact@abc.com • +966 12 345 6789                      │   │
│ │💰│  │                                                            │   │
│ │  │  │  ● Active  │  12 Sites  │  8 Active WOs                 │   │
│ │  │  │                                                            │   │
│ │⚙️│  └──────────────────────────────────────────────────────────┘   │
│ │👤│                                                                   │
│ └──┘  ┌──────┬──────────┬──────────┬──────────┐                     │
│ 60px  │Sites*│Work Orders│Invoices  │Settings  │                     │
│       ├──────┴──────────┴──────────┴──────────┴────────────────────┤ │
│       │                                                              │ │
│       │  [Search...]                          [+ Add Site]          │ │
│       │                                                              │ │
│       │  ┌────────────────────────────────────────────────────────┐ │ │
│       │  │ Site Name     │ Location    │ Assets │ Active WOs     │ │ │
│       │  ├────────────────────────────────────────────────────────┤ │ │
│       │  │ Riyadh HQ     │ Riyadh, SA  │   45   │     3          │ │ │
│       │  │ Jeddah Branch │ Jeddah, SA  │   32   │     2          │ │ │
│       │  │ Dammam Office │ Dammam, SA  │   28   │     3          │ │ │
│       │  └────────────────────────────────────────────────────────┘ │ │
│       │                                                              │ │
│       └──────────────────────────────────────────────────────────────┘ │
│                                                                          │
│ Icon-only sidebar (60px)                                                │
└────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)

```
┌────────────────────────────────┐
│ ☰  FMS                     [👤]│ ← Header with hamburger
├────────────────────────────────┤
│                                │
│ Home > ... > ABC Facilities    │ ← Collapsed breadcrumb
│                                │
│ ┌────────────────────────────┐ │
│ │ ABC Facilities             │ │
│ │ contact@abc.com            │ │
│ │ +966 12 345 6789           │ │
│ │                            │ │
│ │ ● Active                   │ │
│ │ 12 Sites • 8 Active WOs    │ │
│ │                            │ │
│ │ [Edit]  [Archive]          │ │
│ └────────────────────────────┘ │
│                                │
│ ┌──────────────────────────┐   │ ← Horizontal scroll tabs
│ │Sites* │ WOs │ Inv │ Set  │   │
│ └──────────────────────────┘   │
│                                │
│ [Search sites...]              │
│ [+ Add Site]                   │
│                                │
│ ┌────────────────────────────┐ │ ← Card view (no table)
│ │ Riyadh HQ                  │ │
│ │ 📍 Riyadh, SA              │ │
│ │                            │ │
│ │ 45 Assets • 3 Active WOs   │ │
│ │                            │ │
│ │ [View Details →]           │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ Jeddah Branch              │ │
│ │ 📍 Jeddah, SA              │ │
│ │                            │ │
│ │ 32 Assets • 2 Active WOs   │ │
│ │                            │ │
│ │ [View Details →]           │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ Dammam Office              │ │
│ │ 📍 Dammam, SA              │ │
│ │                            │ │
│ │ 28 Assets • 3 Active WOs   │ │
│ │                            │ │
│ │ [View Details →]           │ │
│ └────────────────────────────┘ │
│                                │
└────────────────────────────────┘
```

### Component Breakdown

**Header Section:**
- **Breadcrumb:** Shows hierarchical path
- **Page Title:** Company name (H1)
- **Subtitle:** Contact info (email, phone)
- **Actions:** Edit, Archive buttons (secondary, ghost)
- **Status Bar:** 3 stat cards (Status badge, Sites count, Active WOs count)

**Tabs Section:**
- **Tab List:** Sites (active), Work Orders, Invoices, Settings
- **Tab Indicator:** Blue underline for active tab

**Sites Tab Content:**
- **Toolbar:** Search input (left), Add Site button (right)
- **Data Table:**
  - Columns: Site Name (link), Location, Assets (count), Active WOs (count)
  - Row hover: Light gray background
  - Row click: Navigate to site detail
  - Sort: Click column header (future)

**Responsive Behavior:**
- **Desktop:** Fixed sidebar, full table, all columns visible
- **Tablet:** Icon-only sidebar, table with horizontal scroll if needed
- **Mobile:** Hidden sidebar (hamburger), card view instead of table

**Empty State:**
If no sites exist:
```
┌────────────────────────────┐
│                            │
│       [Map Pin Icon]       │
│                            │
│  No sites for this company │
│                            │
│   Add a site to start      │
│  managing assets and work  │
│          orders            │
│                            │
│    [+ Add First Site]      │
│                            │
└────────────────────────────┘
```

---

## 2. Asset Detail Page

### Desktop Layout (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                         │
│ │          │  Home > Assets > HVAC-001                                               │
│ │          │                                                                         │
│ │  FMS     │  ┌────────────────────────────────────────────────────────────────┐   │
│ │  Logo    │  │                                                                  │   │
│ │          │  │  HVAC Unit — HVAC-001                  [Edit] [Create WO]       │   │
│ ├──────────┤  │  Riyadh HQ • ABC Facilities                                     │   │
│ │          │  │                                                                  │   │
│ │ 🏠 Dash  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │   │
│ │ 🏢 Comp  │  │  │ ⚠ Warning  │ │ 8.7 years  │ │    87%     │ │ 15 days ago│  │   │
│ │ 📍 Sites │  │  │            │ │    Age     │ │  Lifespan  │ │   Last     │  │   │
│ │ 📦 Asset*│  │  │            │ │            │ │    Used    │ │   Maint.   │  │   │
│ │ 👥 Emplo │  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │   │
│ │ 📋 WOs   │  │                                                                  │   │
│ │ 💰 Invoi │  └────────────────────────────────────────────────────────────────┘   │
│ │          │                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │          │  │ Asset Lifecycle Timeline                                        │   │
│ │          │  │                                                                  │   │
│ │          │  │ ──○──────────○────────○──────⚠──○────────────────●──────      │   │
│ │          │  │   ↓          ↓        ↓      ↓  ↓                ↓            │   │
│ │          │  │ Installed   1yr      3yr    6yr 8.7yr           10yr          │   │
│ │          │  │ 2015-06    Maint.   Repair Major  NOW          Expected       │   │
│ │          │  │                            Repair              EOL             │   │
│ │          │  │                                                                  │   │
│ │          │  └────────────────────────────────────────────────────────────────┘   │
│ │          │                                                                         │
│ ├──────────┤  │ ⚠️ Warning: Asset is 87% through expected lifespan             │   │
│ │ ⚙️ Setti │  │    Replacement work order recommended.                         │   │
│ │ 👤 Profi │  │    [Create Replacement WO]                                     │   │
│ │ 🚪 Logou │  └────────────────────────────────────────────────────────────────┘   │
│ └──────────┘                                                                         │
│                ┌─────────┬─────────────┬──────────┬──────────────────────────┐     │
│                │Details* │Maintenance  │Work Orders│                          │     │
│                ├─────────┴─────────────┴──────────┴──────────────────────────┤     │
│                │                                                               │     │
│                │  Asset Information                                            │     │
│                │  ┌──────────────────────────────────────────────────────────┐│     │
│                │  │ Asset ID:          HVAC-001                              ││     │
│                │  │ Type:              HVAC Unit                             ││     │
│                │  │ Manufacturer:      Carrier                               ││     │
│                │  │ Model:             30RB-080                              ││     │
│                │  │ Serial Number:     ABC123XYZ                             ││     │
│                │  │ Installation Date: 2015-06-15                            ││     │
│                │  │ Expected Lifespan: 10 years                              ││     │
│                │  │ Current Age:       8.7 years                             ││     │
│                │  │ Location:          Riyadh HQ > Building A > Roof         ││     │
│                │  │                                                          ││     │
│                │  │ [QR Code]                                                ││     │
│                │  │ ┌────────┐                                              ││     │
│                │  │ │████████│  Scan to access                              ││     │
│                │  │ │███  ███│  asset details                               ││     │
│                │  │ │████████│                                              ││     │
│                │  │ └────────┘                                              ││     │
│                │  └──────────────────────────────────────────────────────────┘│     │
│                │                                                               │     │
│                └───────────────────────────────────────────────────────────────┘     │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Lifecycle Timeline Detail (Desktop)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Asset Lifecycle Timeline                                                   │
│                                                                             │
│                          Hover for details                                  │
│ ──────○──────────○────────○──────⚠──○────────────────●──────              │
│       │          │        │      │  │                │                     │
│    Installed   1 year   3 yrs  6 yrs NOW          Expected                │
│    2015-06    Preventive Repair Major 8.7 yrs       EOL                    │
│               $500       $1.2k Repair             10 years                 │
│                                 $5k                                         │
│                                                                             │
│ ○ = Maintenance event                                                       │
│ ⚠ = Warning zone (80-100% lifespan)                                        │
│ ● = End of life marker                                                      │
│ ─ = Active (green)                                                          │
│ ⚠ = Warning zone (yellow)                                                   │
│ ● = EOL marker (red)                                                        │
│                                                                             │
│ Current Status: ⚠ Warning (87% of lifespan used)                          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)

```
┌────────────────────────────────┐
│ ☰  FMS                     [👤]│
├────────────────────────────────┤
│                                │
│ Home > Assets > HVAC-001       │
│                                │
│ ┌────────────────────────────┐ │
│ │ HVAC Unit — HVAC-001       │ │
│ │ Riyadh HQ • ABC Facilities │ │
│ │                            │ │
│ │ [Edit]  [Create WO]        │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ ⚠ Warning                  │ │
│ │ 8.7 years old              │ │
│ │ 87% of lifespan used       │ │
│ │ Last maint: 15 days ago    │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ Lifecycle Timeline         │ │
│ │                            │ │
│ │ ○ Installed                │ │
│ │ │ 2015-06                  │ │
│ │ │                          │ │
│ │ ○ 1yr - Maintenance        │ │
│ │ │ $500                     │ │
│ │ │                          │ │
│ │ ○ 3yr - Repair             │ │
│ │ │ $1.2k                    │ │
│ │ │                          │ │
│ │ ⚠ 6yr - Major Repair       │ │
│ │ │ $5k                      │ │
│ │ │                          │ │
│ │ ⚠ 8.7yr - NOW              │ │
│ │ │                          │ │
│ │ ●                          │ │
│ │ │                          │ │
│ │ ● 10yr - Expected EOL      │ │
│ │                            │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ ⚠️ Warning                 │ │
│ │ Asset is 87% through       │ │
│ │ expected lifespan.         │ │
│ │ Replacement recommended.   │ │
│ │                            │ │
│ │ [Create Replacement WO]    │ │
│ └────────────────────────────┘ │
│                                │
│ ┌───────────────────────────┐  │ ← Scroll tabs
│ │Details*│ Maint │ WOs │    │  │
│ └───────────────────────────┘  │
│                                │
│ Asset Information              │
│ ┌────────────────────────────┐ │
│ │ Asset ID:      HVAC-001    │ │
│ │ Type:          HVAC Unit   │ │
│ │ Manufacturer:  Carrier     │ │
│ │ Model:         30RB-080    │ │
│ │ Serial:        ABC123XYZ   │ │
│ │ Installed:     2015-06-15  │ │
│ │ Lifespan:      10 years    │ │
│ │ Age:           8.7 years   │ │
│ │ Location:      Riyadh HQ   │ │
│ │                Building A  │ │
│ │                Roof        │ │
│ │                            │ │
│ │ [View QR Code]             │ │
│ └────────────────────────────┘ │
│                                │
└────────────────────────────────┘
```

### Component Breakdown

**Header Section:**
- **Breadcrumb:** Home > Assets > HVAC-001
- **Page Title:** HVAC Unit — HVAC-001
- **Subtitle:** Site • Company
- **Actions:** Edit, Create Work Order buttons
- **Status Bar:** 4 stat cards (Lifecycle badge, Age, Lifespan %, Last maintenance)

**Lifecycle Timeline:**
- **Visual:** Horizontal timeline (desktop), vertical timeline (mobile)
- **Events:** Installation, maintenance, repairs, current position, EOL
- **Colors:** Green (active), Yellow (warning zone), Red (EOL)
- **Interaction:** Hover for details (desktop), tap for details (mobile)
- **Current Position:** Animated pulse indicator

**Alert Banner:**
- **Warning Alert:** Yellow background, warning icon, message, CTA button
- **EOL Alert:** Red background, error icon, replacement link if exists

**Tabs Section:**
- **Tab List:** Details (active), Maintenance History, Work Orders
- **Tab Content:** Details table with asset information

**Asset Information:**
- **Layout:** Two-column key-value pairs (desktop), stacked (mobile)
- **Fields:** ID, Type, Manufacturer, Model, Serial, Dates, Location
- **QR Code:** Displayed as image, printable

**Responsive Behavior:**
- **Desktop:** Horizontal timeline, two-column layout, full sidebar
- **Tablet:** Horizontal timeline, stacked layout, icon-only sidebar
- **Mobile:** Vertical timeline, stacked layout, hidden sidebar

**Empty State (Maintenance History Tab):**
```
┌────────────────────────────┐
│                            │
│      [Wrench Icon]         │
│                            │
│ No maintenance history yet │
│                            │
│  Maintenance records will  │
│   appear here as work      │
│  orders are completed      │
│                            │
└────────────────────────────┘
```

---

## 3. Welcome Dashboard Page

### Desktop Layout — Super Admin (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │  FMS     │  │                                                                  │   │
│ │  Logo    │  │  Welcome, Ahmed Ali                                             │   │
│ │          │  │  Super Admin                                                     │   │
│ ├──────────┤  │                                                                  │   │
│ │          │  └────────────────────────────────────────────────────────────────┘   │
│ │ 🏠 Dash* │                                                                         │
│ │ 🏢 Comp  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│ │ 📍 Sites │  │ Companies   │ │ Active WOs  │ │Open Invoices│ │ Technicians │   │
│ │ 📦 Asset │  │             │ │             │ │             │ │             │   │
│ │ 👥 Emplo │  │     24      │ │     48      │ │  SAR 125k   │ │     15      │   │
│ │ 📋 WOs   │  │             │ │             │ │             │ │             │   │
│ │ 💰 Invoi │  │ ↑ 2 new     │ │ ↓ 12 less   │ │ ↑ SAR 25k   │ │ 3 busy      │   │
│ │          │  │             │ │             │ │             │ │             │   │
│ │          │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│ │          │                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │          │  │ Recent Work Orders                           [View All →]      │   │
│ ├──────────┤  ├────────────────────────────────────────────────────────────────┤   │
│ │ ⚙️ Setti │  │ ID      │ Title            │ Site        │ Status      │ Urgency│   │
│ │ 👤 Profi │  ├─────────────────────────────────────────────────────────────────   │
│ │ 🚪 Logou │  │ WO-001  │ HVAC Repair      │ Riyadh HQ   │ Assigned    │🔴Urgent│   │
│ └──────────┘  │ WO-002  │ Elevator Service │ Jeddah      │ In Progress │ Normal │   │
│                │ WO-003  │ Fire System Test │ Dammam      │ Created     │🔴Emerg │   │
│                │ WO-004  │ Generator Check  │ Riyadh HQ   │ In Progress │ Normal │   │
│                │ WO-005  │ Lighting Repair  │ Mecca       │ Assigned    │ Urgent │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│                ┌────────────────────────────────────────────────────────────────┐   │
│                │ Quick Actions                                                  │   │
│                ├────────────────────────────────────────────────────────────────┤   │
│                │ [+ Create Work Order] [+ Add Company] [+ Register Asset]       │   │
│                │ [+ Add Employee]      [📊 View Reports]                        │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Layout — Technician (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │  FMS     │  │                                                                  │   │
│ │  Logo    │  │  Welcome, Mohammed Khan                                         │   │
│ │          │  │  Technician                                                      │   │
│ ├──────────┤  │                                                                  │   │
│ │          │  └────────────────────────────────────────────────────────────────┘   │
│ │ 🏠 Dash* │                                                                         │
│ │ 📋 My WOs│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│ │ 📅 Sched │  │ My Tasks    │ │ In Progress │ │  Completed  │                   │
│ │          │  │             │ │             │ │             │                   │
│ │          │  │      5      │ │      2      │ │  12 (week)  │                   │
│ │          │  │             │ │             │ │             │                   │
│ │          │  │ 2 urgent    │ │             │ │             │                   │
│ │          │  │             │ │             │ │             │                   │
│ │          │  └─────────────┘ └─────────────┘ └─────────────┘                   │
│ │          │                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │          │  │ My Work Orders                           [View All →]          │   │
│ ├──────────┤  ├────────────────────────────────────────────────────────────────┤   │
│ │ ⚙️ Setti │  │ ☐ │ WO-001 │ HVAC Repair      │ Riyadh HQ   │🔴Urgent          │   │
│ │ 👤 Profi │  │ ☐ │ WO-003 │ Fire System Test │ Dammam      │🔴Emergency       │   │
│ │ 🚪 Logou │  │ ☐ │ WO-007 │ Pump Maintenance │ Jeddah      │ Urgent           │   │
│ └──────────┘  │ ☐ │ WO-009 │ Door Lock Repair │ Riyadh HQ   │ Normal           │   │
│                │ ✓ │ WO-002 │ Elevator Service │ Jeddah      │ Normal           │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│                ┌────────────────────────────────────────────────────────────────┐   │
│                │ Today's Schedule                                               │   │
│                ├────────────────────────────────────────────────────────────────┤   │
│                │ 09:00 - WO-001 @ Riyadh HQ (HVAC Repair)                      │   │
│                │ 14:00 - WO-003 @ Dammam (Fire System Test)                    │   │
│                │ 16:30 - WO-007 @ Jeddah (Pump Maintenance)                    │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│                ┌────────────────────────────────────────────────────────────────┐   │
│                │ Quick Actions                                                  │   │
│                ├────────────────────────────────────────────────────────────────┤   │
│                │ [🔍 View My Tasks] [▶️ Start Work] [✓ Complete Report]        │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Layout — Client Admin (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────┐                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │  FMS     │  │                                                                  │   │
│ │  Logo    │  │  Welcome, Fatima Ahmed                                          │   │
│ │          │  │  ABC Facilities — Client Admin                                  │   │
│ ├──────────┤  │                                                                  │   │
│ │          │  └────────────────────────────────────────────────────────────────┘   │
│ │ 🏠 Dash* │                                                                         │
│ │ 📍 Sites │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│ │ 📋 WOs   │  │   Sites     │ │ Active WOs  │ │  Pending    │                   │
│ │ 📦 Assets│  │             │ │             │ │  Invoices   │                   │
│ │ 💰 Invoi │  │     12      │ │      8      │ │  SAR 45k    │                   │
│ │ 📊 Repor │  │             │ │             │ │             │                   │
│ │          │  │             │ │ 2 overdue   │ │             │                   │
│ │          │  │             │ │             │ │             │                   │
│ │          │  └─────────────┘ └─────────────┘ └─────────────┘                   │
│ │          │                                                                         │
│ │          │  ┌────────────────────────────────────────────────────────────────┐   │
│ │          │  │ Work Orders by Status                                          │   │
│ ├──────────┤  ├────────────────────────────────────────────────────────────────┤   │
│ │ ⚙️ Setti │  │ Completed     ████████████░░░░░░░░ 60% (24 orders)            │   │
│ │ 👤 Profi │  │ In Progress   ██████░░░░░░░░░░░░░░ 30% (12 orders)            │   │
│ │ 🚪 Logou │  │ Pending       ██░░░░░░░░░░░░░░░░░░ 10% ( 4 orders)            │   │
│ └──────────┘  └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│                ┌────────────────────────────────────────────────────────────────┐   │
│                │ Recent Activity                                                │   │
│                ├────────────────────────────────────────────────────────────────┤   │
│                │ • WO-001 marked as Completed (2 hours ago)                    │   │
│                │ • Invoice INV-123 generated (1 day ago)                       │   │
│                │ • New site added: Riyadh Branch 2 (3 days ago)                │   │
│                │ • WO-007 assigned to Mohammed Khan (3 days ago)               │   │
│                │ • Asset HVAC-002 reached warning status (5 days ago)          │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
│                ┌────────────────────────────────────────────────────────────────┐   │
│                │ Quick Actions                                                  │   │
│                ├────────────────────────────────────────────────────────────────┤   │
│                │ [+ Create Work Order] [💰 View Invoices] [📊 View Reports]     │   │
│                └────────────────────────────────────────────────────────────────┘   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Layout — Super Admin (< 768px)

```
┌────────────────────────────────┐
│ ☰  FMS                     [👤]│
├────────────────────────────────┤
│                                │
│ Welcome, Ahmed Ali             │
│ Super Admin                    │
│                                │
│ ┌────────────┐ ┌────────────┐ │
│ │ Companies  │ │ Active WOs │ │
│ │            │ │            │ │
│ │     24     │ │     48     │ │
│ │            │ │            │ │
│ │ ↑ 2 new    │ │ ↓ 12 less  │ │
│ └────────────┘ └────────────┘ │
│                                │
│ ┌────────────┐ ┌────────────┐ │
│ │   Open     │ │Technicians │ │
│ │  Invoices  │ │            │ │
│ │ SAR 125k   │ │     15     │ │
│ │            │ │            │ │
│ │ ↑ SAR 25k  │ │ 3 busy     │ │
│ └────────────┘ └────────────┘ │
│                                │
│ Recent Work Orders             │
│                   [View All →] │
│ ┌────────────────────────────┐ │
│ │ WO-001                     │ │
│ │ HVAC Repair                │ │
│ │ Riyadh HQ • Assigned       │ │
│ │ 🔴 Urgent                  │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ WO-002                     │ │
│ │ Elevator Service           │ │
│ │ Jeddah • In Progress       │ │
│ │ Normal                     │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ WO-003                     │ │
│ │ Fire System Test           │ │
│ │ Dammam • Created           │ │
│ │ 🔴 Emergency               │ │
│ └────────────────────────────┘ │
│                                │
│ Quick Actions                  │
│ [+ Create WO]  [+ Add Company] │
│ [+ Register Asset] [+ Employee]│
│ [📊 View Reports]              │
│                                │
└────────────────────────────────┘
```

### Mobile Layout — Technician (< 768px)

```
┌────────────────────────────────┐
│ ☰  FMS                     [👤]│
├────────────────────────────────┤
│                                │
│ Welcome, Mohammed Khan         │
│ Technician                     │
│                                │
│ ┌────────────┐ ┌────────────┐ │
│ │  My Tasks  │ │In Progress │ │
│ │            │ │            │ │
│ │      5     │ │      2     │ │
│ │            │ │            │ │
│ │ 2 urgent   │ │            │ │
│ └────────────┘ └────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │        Completed           │ │
│ │                            │ │
│ │       12 (week)            │ │
│ │                            │ │
│ └────────────────────────────┘ │
│                                │
│ My Work Orders    [View All →] │
│ ┌────────────────────────────┐ │
│ │ ☐ WO-001                   │ │
│ │ HVAC Repair                │ │
│ │ Riyadh HQ • 🔴 Urgent      │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ ☐ WO-003                   │ │
│ │ Fire System Test           │ │
│ │ Dammam • 🔴 Emergency      │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ ☐ WO-007                   │ │
│ │ Pump Maintenance           │ │
│ │ Jeddah • Urgent            │ │
│ └────────────────────────────┘ │
│                                │
│ Today's Schedule               │
│ • 09:00 - WO-001 @ Riyadh HQ   │
│ • 14:00 - WO-003 @ Dammam      │
│ • 16:30 - WO-007 @ Jeddah      │
│                                │
│ Quick Actions                  │
│ [🔍 View Tasks] [▶️ Start Work]│
│ [✓ Complete Report]            │
│                                │
└────────────────────────────────┘
```

### Component Breakdown

**Header Section:**
- **Greeting:** "Welcome, [Name]"
- **Role Label:** User's role (Super Admin, Technician, etc.)

**Stat Cards:**
- **Super Admin:** Companies, Active WOs, Open Invoices, Technicians
- **Technician:** My Tasks, In Progress, Completed (week)
- **Client Admin:** Sites, Active WOs, Pending Invoices
- **Site Manager:** Assets, Active WOs, Overdue Maintenance

**Data Visualization:**
- **Super Admin:** Recent work orders table
- **Technician:** Task list with checkboxes, today's schedule
- **Client Admin:** Work orders by status (horizontal bar chart), activity feed
- **Site Manager:** Assets by lifecycle (pie chart), upcoming maintenance

**Quick Actions:**
- **Super Admin:** Create WO, Add Company, Register Asset, Add Employee, View Reports
- **Technician:** View Tasks, Start Work, Complete Report
- **Client Admin:** Create WO, View Invoices, View Reports
- **Site Manager:** Create WO, Register Asset, Schedule Maintenance

**Responsive Behavior:**
- **Desktop:** 4-column stat card grid, full table, fixed sidebar
- **Tablet:** 2-column stat card grid, table view, icon-only sidebar
- **Mobile:** 2-column stat card grid, card view instead of table, hidden sidebar

**Empty State (No Tasks):**
```
┌────────────────────────────┐
│                            │
│      [Clipboard Icon]      │
│                            │
│   No tasks assigned yet    │
│                            │
│  You're all caught up!     │
│  Check back later for new  │
│       assignments          │
│                            │
└────────────────────────────┘
```

---

## Summary

These wireframes provide detailed layout specifications for the 3 most critical pages:

1. **Company Detail Page:**
   - Hierarchical navigation (breadcrumbs)
   - Tabbed interface (Sites, Work Orders, Invoices, Settings)
   - Nested sites table with action buttons
   - Responsive: Fixed sidebar (desktop) → Icon-only (tablet) → Hamburger (mobile)
   - Responsive: Table (desktop) → Card view (mobile)

2. **Asset Detail Page:**
   - Visual lifecycle timeline (horizontal on desktop, vertical on mobile)
   - Alert banners for warning/EOL status
   - Tabbed interface (Details, Maintenance History, Work Orders)
   - QR code for on-site scanning
   - Responsive: Timeline orientation changes, layout stacks on mobile

3. **Welcome Dashboard Page:**
   - Role-specific stat cards and widgets
   - Super Admin: Company overview, recent WOs table
   - Technician: Task-focused, schedule view
   - Client Admin: Charts, activity feed
   - Responsive: 4-col → 2-col → 2-col grid, table → card view

**Design Principles Applied:**
- Consistent sidebar navigation (240px desktop, 60px tablet, hamburger mobile)
- Stat cards with value, label, and change indicator
- Tables for data-dense views (desktop), cards for mobile
- Tab navigation for related content sections
- Alert banners for important warnings
- Empty states for better UX
- Touch-friendly button sizes (44x44px minimum)

**Next Steps:**
1. Validate wireframes with stakeholders
2. Create high-fidelity mockups in Figma/Sketch
3. Build component library based on wireframes
4. Implement responsive layouts
5. Conduct usability testing
