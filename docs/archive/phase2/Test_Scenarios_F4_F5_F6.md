# Test Scenarios for P2-F4, P2-F5, P2-F6

**Date:** April 17, 2026  
**QA Agent:** Senior QA Engineer  
**Version:** 1.0

---

## Overview

This document provides detailed test scenarios for the three major Phase 2 features:
- **P2-F4**: Man Labor Management
- **P2-F5**: Location Management
- **P2-F6**: Customized Dashboards + Welcome Pages

---

## P2-F4: Man Labor Management

### Feature Description
Track technician assignments, hours logged, hourly rates, availability/scheduling, overtime tracking, performance metrics, and cost tracking per technician per work order.

### Backend Models Required
- `TechnicianProfile` - Extended technician data (hourly_rate, specializations)
- `LaborEntry` - Hours logged against work orders
- `TechnicianSchedule` - Availability calendar
- `PerformanceMetrics` - Calculated metrics (WOs completed, avg time)

---

### Test Scenarios - Labor Entry

**TS-LABOR-001: Create Labor Entry**
- **Given**: Technician assigned to work order
- **When**: POST /labor-entries with work_order_id, technician_id, hours_worked=4.5
- **Then**: 
  - Labor entry created
  - Linked to work order
  - Cost calculated (hours_worked * hourly_rate)

**TS-LABOR-002: Technician Can Only Log Own Hours**
- **Given**: Technician A logged in
- **When**: POST /labor-entries with technician_id=TechnicianB
- **Then**: Returns 403 Forbidden

**TS-LABOR-003: Manager Can Log Hours for Any Technician**
- **Given**: Manager logged in
- **When**: POST /labor-entries with any technician_id
- **Then**: Labor entry created successfully

**TS-LABOR-004: Labor Entry Validation - Negative Hours**
- **When**: POST /labor-entries with hours_worked=-2
- **Then**: Returns 400 Bad Request

**TS-LABOR-005: Labor Entry Validation - Excessive Hours**
- **When**: POST /labor-entries with hours_worked=25 (> 24 hours in a day)
- **Then**: Returns 400 Bad Request

**TS-LABOR-006: Update Labor Entry**
- **Given**: Existing labor entry with hours_worked=4
- **When**: PATCH /labor-entries/{id} with hours_worked=5
- **Then**: 
  - Hours updated
  - Cost recalculated
  - updated_at timestamp updated

**TS-LABOR-007: Delete Labor Entry**
- **Given**: Existing labor entry
- **When**: DELETE /labor-entries/{id}
- **Then**: Labor entry deleted (or soft-deleted)

**TS-LABOR-008: Get Labor Entries for Work Order**
- **Given**: Work order with 3 labor entries
- **When**: GET /work-orders/{id}/labor-entries
- **Then**: Returns all 3 labor entries

**TS-LABOR-009: Labor Entry Respects Tenant Isolation**
- **Given**: Tenant A has labor entry
- **When**: Tenant B user requests GET /labor-entries/{tenant_a_entry_id}
- **Then**: Returns 404 Not Found

---

### Test Scenarios - Overtime Calculation

**TS-LABOR-010: Regular Hours (No Overtime)**
- **Given**: Technician profile with regular_hours_per_day=8
- **When**: Log 6 hours in a day
- **Then**: 
  - regular_hours = 6
  - overtime_hours = 0

**TS-LABOR-011: Overtime Calculation**
- **Given**: Technician profile with regular_hours_per_day=8, overtime_multiplier=1.5
- **When**: Log 10 hours in a day
- **Then**: 
  - regular_hours = 8
  - overtime_hours = 2
  - cost = (8 * hourly_rate) + (2 * hourly_rate * 1.5)

**TS-LABOR-012: Multiple Entries Same Day**
- **Given**: Technician logs 5 hours on WO-1, then 4 hours on WO-2 same day
- **When**: Calculate daily totals
- **Then**: 
  - Total hours = 9
  - regular_hours = 8
  - overtime_hours = 1

**TS-LABOR-013: Weekly Overtime Threshold**
- **Given**: Technician profile with weekly_overtime_threshold=40
- **When**: Log 50 hours across 5 days
- **Then**: 
  - regular_hours = 40
  - overtime_hours = 10

---

### Test Scenarios - Technician Scheduling

**TS-LABOR-014: Create Schedule Entry**
- **Given**: Technician profile
- **When**: POST /technicians/{id}/schedule with date, start_time, end_time, availability='available'
- **Then**: Schedule entry created

**TS-LABOR-015: Mark Technician as Unavailable**
- **When**: POST /technicians/{id}/schedule with availability='unavailable', reason='sick_leave'
- **Then**: 
  - Schedule entry created
  - Technician not shown in available list for that date

**TS-LABOR-016: Get Available Technicians for Date**
- **Given**: 5 technicians, 2 marked unavailable on 2026-04-20
- **When**: GET /technicians/available?date=2026-04-20
- **Then**: Returns 3 available technicians

**TS-LABOR-017: Schedule Conflict Detection**
- **Given**: Technician scheduled 9am-5pm on 2026-04-20
- **When**: Try to create another schedule entry 3pm-7pm same day
- **Then**: Returns 400 Bad Request (conflict)

**TS-LABOR-018: Recurring Schedule**
- **When**: POST /technicians/{id}/schedule with recurring_pattern='weekly', days=['monday', 'wednesday']
- **Then**: Schedule entries created for next 4 weeks

**TS-LABOR-019: Update Schedule Entry**
- **Given**: Schedule entry for 9am-5pm
- **When**: PATCH /schedule-entries/{id} with end_time='3pm'
- **Then**: Schedule updated

**TS-LABOR-020: Delete Schedule Entry**
- **Given**: Future schedule entry
- **When**: DELETE /schedule-entries/{id}
- **Then**: Entry deleted, technician available again

---

### Test Scenarios - Performance Metrics

**TS-LABOR-021: Calculate Work Orders Completed**
- **Given**: Technician completed 15 work orders this month
- **When**: GET /technicians/{id}/performance?month=2026-04
- **Then**: Returns work_orders_completed=15

**TS-LABOR-022: Calculate Average Time per Work Order**
- **Given**: Technician completed 10 WOs with total 40 hours logged
- **When**: GET /technicians/{id}/performance
- **Then**: Returns avg_hours_per_wo=4.0

**TS-LABOR-023: On-Time Completion Rate**
- **Given**: Technician completed 8 WOs on time, 2 late
- **When**: GET /technicians/{id}/performance
- **Then**: Returns on_time_rate=80%

**TS-LABOR-024: Total Labor Cost**
- **Given**: Technician hourly_rate=50, logged 100 hours this month (10 overtime)
- **When**: GET /technicians/{id}/performance?month=2026-04
- **Then**: Returns total_cost = (90 * 50) + (10 * 50 * 1.5) = 5250

**TS-LABOR-025: Performance Metrics Respect Tenant Isolation**
- **Given**: Tenant A technician
- **When**: Tenant B user requests GET /technicians/{tenant_a_tech_id}/performance
- **Then**: Returns 404 Not Found

**TS-LABOR-026: Leaderboard - Top Performers**
- **Given**: 10 technicians with various completion rates
- **When**: GET /technicians/leaderboard?metric=work_orders_completed&limit=5
- **Then**: Returns top 5 technicians sorted by WOs completed

---

### Test Scenarios - Technician Assignment

**TS-LABOR-027: Assign Technician to Work Order**
- **Given**: Work order with status='created'
- **When**: PATCH /work-orders/{id} with assignee_user_id={technician_id}
- **Then**: 
  - Work order assigned
  - status changes to 'assigned'
  - Technician receives notification

**TS-LABOR-028: Reassign Work Order**
- **Given**: Work order assigned to Technician A
- **When**: PATCH /work-orders/{id} with assignee_user_id={technician_b_id}
- **Then**: 
  - Work order reassigned to Technician B
  - Technician A receives unassignment notification
  - Technician B receives assignment notification

**TS-LABOR-029: Cannot Assign to Non-Technician**
- **When**: PATCH /work-orders/{id} with assignee_user_id={manager_id}
- **Then**: Returns 400 Bad Request (user is not a technician)

**TS-LABOR-030: Auto-Suggest Technician Based on Availability**
- **Given**: 3 technicians available, 1 with lowest current workload
- **When**: GET /work-orders/suggest-technician?site_id={site_id}
- **Then**: Returns technician with lowest workload

**TS-LABOR-031: Auto-Suggest Based on Specialization**
- **Given**: Technician A specializes in 'hvac', WO category='hvac'
- **When**: GET /work-orders/suggest-technician?category=hvac
- **Then**: Returns Technician A as top suggestion

---

### Test Scenarios - Labor Billing Integration

**TS-LABOR-032: Invoice Includes Labor Costs**
- **Given**: Work order with 2 labor entries (10 hours total)
- **When**: Generate invoice for work order
- **Then**: Invoice includes labor line items with correct costs

**TS-LABOR-033: Overtime Separately Itemized**
- **Given**: Labor entry with 8 regular hours + 2 overtime hours
- **When**: Generate invoice
- **Then**: 
  - Line item 1: "Regular Labor - 8 hours @ $50/hr" = $400
  - Line item 2: "Overtime Labor - 2 hours @ $75/hr" = $150

**TS-LABOR-034: Multiple Technicians on Same Work Order**
- **Given**: WO with labor from Technician A (5 hrs) and Technician B (3 hrs)
- **When**: Generate invoice
- **Then**: Invoice includes separate line items for each technician

---

## P2-F5: Location Management

### Feature Description
Hierarchical location tree (Region -> Building -> Floor -> Zone -> Room), location-based asset grouping, work order filtering by location, QR code scanning for location identification.

### Backend Models Required
- `Location` - Self-referential hierarchical model (parent_location_id)
- `Asset.location_id` - FK to Location
- `WorkOrder.location_id` - FK to Location

---

### Test Scenarios - Location CRUD

**TS-LOC-001: Create Root Location (Region)**
- **When**: POST /locations with name="North Region", type='region', parent_location_id=null
- **Then**: Location created at root level

**TS-LOC-002: Create Child Location (Building)**
- **Given**: Region location exists
- **When**: POST /locations with name="Building A", type='building', parent_location_id={region_id}
- **Then**: Building created under region

**TS-LOC-003: Create Multi-Level Hierarchy**
- **Given**: Region -> Building -> Floor
- **When**: POST /locations with name="Zone 1", type='zone', parent_location_id={floor_id}
- **Then**: Zone created, hierarchy depth = 4

**TS-LOC-004: Get Location Tree**
- **Given**: Location hierarchy with 10 locations
- **When**: GET /locations/tree?site_id={site_id}
- **Then**: Returns nested JSON tree structure

**TS-LOC-005: Update Location**
- **Given**: Location with name="Building A"
- **When**: PATCH /locations/{id} with name="Building A - Main"
- **Then**: Location updated

**TS-LOC-006: Move Location to Different Parent**
- **Given**: Zone under Floor 1
- **When**: PATCH /locations/{id} with parent_location_id={floor_2_id}
- **Then**: Zone moved to Floor 2

**TS-LOC-007: Delete Location with No Children**
- **Given**: Empty room location
- **When**: DELETE /locations/{id}
- **Then**: Location deleted

**TS-LOC-008: Cannot Delete Location with Children**
- **Given**: Building with 3 floors
- **When**: DELETE /locations/{building_id}
- **Then**: Returns 400 Bad Request (has children)

**TS-LOC-009: Cannot Delete Location with Assets**
- **Given**: Room with 5 assets
- **When**: DELETE /locations/{room_id}
- **Then**: Returns 400 Bad Request (has assets)

**TS-LOC-010: Cascade Delete Option**
- **Given**: Building with floors, zones, rooms
- **When**: DELETE /locations/{building_id}?cascade=true
- **Then**: Building and all descendants deleted

---

### Test Scenarios - Circular Reference Prevention

**TS-LOC-011: Prevent Self-Reference**
- **When**: PATCH /locations/{id} with parent_location_id={same_id}
- **Then**: Returns 400 Bad Request

**TS-LOC-012: Prevent Circular Reference (Child as Parent)**
- **Given**: Building A -> Floor 1 -> Zone 1
- **When**: PATCH /locations/{building_a_id} with parent_location_id={zone_1_id}
- **Then**: Returns 400 Bad Request (would create circular reference)

**TS-LOC-013: Prevent Deep Nesting (Max Depth)**
- **Given**: Location hierarchy depth = 10
- **When**: POST /locations with parent at depth 10
- **Then**: Returns 400 Bad Request (exceeds max depth)

---

### Test Scenarios - Location-Based Asset Grouping

**TS-LOC-014: Assign Asset to Location**
- **Given**: Asset and Room location
- **When**: PATCH /assets/{id} with location_id={room_id}
- **Then**: Asset assigned to location

**TS-LOC-015: Get Assets by Location**
- **Given**: Room with 5 assets
- **When**: GET /assets?location_id={room_id}
- **Then**: Returns 5 assets

**TS-LOC-016: Get Assets by Parent Location (Recursive)**
- **Given**: Building with 3 floors, 10 assets across floors
- **When**: GET /assets?location_id={building_id}&recursive=true
- **Then**: Returns all 10 assets

**TS-LOC-017: Move Asset Between Locations**
- **Given**: Asset in Room A
- **When**: PATCH /assets/{id} with location_id={room_b_id}
- **Then**: Asset moved to Room B

**TS-LOC-018: Location Breadcrumbs for Asset**
- **Given**: Asset in "North Region > Building A > Floor 1 > Zone 1 > Room 101"
- **When**: GET /assets/{id}
- **Then**: Response includes location_path array with full hierarchy

---

### Test Scenarios - Location-Based Work Order Filtering

**TS-LOC-019: Filter Work Orders by Location**
- **Given**: 5 WOs in Building A, 3 WOs in Building B
- **When**: GET /work-orders?location_id={building_a_id}
- **Then**: Returns 5 work orders

**TS-LOC-020: Filter Work Orders by Parent Location (Recursive)**
- **Given**: 10 WOs across 3 floors in Building A
- **When**: GET /work-orders?location_id={building_a_id}&recursive=true
- **Then**: Returns all 10 work orders

**TS-LOC-021: Create Work Order with Location**
- **When**: POST /work-orders with location_id={room_id}
- **Then**: Work order created, linked to location

**TS-LOC-022: Work Order Inherits Asset Location**
- **Given**: Asset in Room 101
- **When**: POST /work-orders with asset_id={asset_id}, location_id=null
- **Then**: Work order location_id auto-populated from asset's location

---

### Test Scenarios - QR Code Integration

**TS-LOC-023: Generate QR Code for Location**
- **Given**: Location with id=123e4567
- **When**: GET /locations/{id}/qr-code
- **Then**: Returns QR code image (PNG) encoding location URL

**TS-LOC-024: Scan QR Code to View Location**
- **Given**: QR code payload = "fms://location/{id}"
- **When**: Scan QR code with mobile app
- **Then**: Redirects to LocationDetailPage

**TS-LOC-025: Create Work Order from QR Scan**
- **Given**: Technician scans location QR code
- **When**: Click "Create Work Order" button
- **Then**: WO creation form opens with location_id pre-filled

**TS-LOC-026: Invalid QR Code Payload**
- **Given**: QR code with payload = "invalid"
- **When**: Scan QR code
- **Then**: Shows error message "Invalid location code"

---

### Test Scenarios - Location UI Components

**TS-LOC-027: Location Tree View (Expandable)**
- **Given**: Location hierarchy with 20 locations
- **When**: View LocationTree component
- **Then**: 
  - Displays tree with expand/collapse icons
  - Only root level expanded by default
  - Clicking node expands children

**TS-LOC-028: Location Breadcrumbs**
- **Given**: User viewing Room 101 (depth = 5)
- **When**: View LocationDetailPage
- **Then**: Breadcrumbs show: North Region > Building A > Floor 1 > Zone 1 > Room 101

**TS-LOC-029: Location Search/Filter**
- **Given**: 50 locations across site
- **When**: Type "Room 1" in search box
- **Then**: Tree filters to show only matching locations + parents

**TS-LOC-030: Drag-and-Drop Location Move**
- **Given**: Zone 1 under Floor 1
- **When**: Drag Zone 1 and drop on Floor 2
- **Then**: 
  - Zone 1 moved to Floor 2
  - Confirmation dialog shown
  - Tree updates

---

### Test Scenarios - Location Tenant Isolation

**TS-LOC-031: Locations Respect Tenant Isolation**
- **Given**: Tenant A has 10 locations, Tenant B has 5 locations
- **When**: Tenant A user requests GET /locations
- **Then**: Returns only Tenant A's 10 locations

**TS-LOC-032: Cannot Move Location to Different Tenant**
- **Given**: Tenant A location, Tenant B location
- **When**: Tenant A tries PATCH /locations/{a_id} with parent_location_id={b_id}
- **Then**: Returns 404 Not Found (Tenant B location not accessible)

---

## P2-F6: Customized Dashboards + Welcome Pages

### Feature Description
Role-specific dashboards with widgets showing relevant metrics, and personalized welcome pages with current tasks.

### Backend Endpoints Required
- `GET /dashboard` - Role-specific dashboard data
- `GET /dashboard/widgets` - Available widget types
- `GET /users/me/tasks` - Current tasks for logged-in user

---

### Test Scenarios - Role-Specific Dashboards

**TS-DASH-001: Super Admin Dashboard Data**
- **Given**: Super admin logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Total companies count
  - Total work orders across all companies
  - Total revenue
  - SLA compliance percentage
  - Top 5 technicians by performance
  - Work order status breakdown (pie chart data)

**TS-DASH-002: Company Admin Dashboard Data**
- **Given**: Company admin logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Total sites in tenant
  - Open work orders count
  - Revenue this month
  - SLA compliance for tenant
  - Technician workload

**TS-DASH-003: Client Admin Dashboard Data**
- **Given**: Client admin logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Sites overview (count, active WOs per site)
  - Open work orders for their company
  - Billing summary (pending invoices, total due)
  - Asset health (active, warning, end_of_life counts)

**TS-DASH-004: Site Manager Dashboard Data**
- **Given**: Site manager logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Site-specific work orders (open, in progress, completed)
  - Asset status for their site
  - Upcoming maintenance schedules
  - Recent activity feed

**TS-DASH-005: Technician Dashboard Data**
- **Given**: Technician logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Assigned work orders (by status)
  - Hours logged this week
  - Performance metrics (WOs completed, avg time)
  - Next scheduled work order

**TS-DASH-006: Manager Dashboard Data**
- **Given**: Manager logged in
- **When**: GET /dashboard
- **Then**: Returns:
  - Team overview (technicians, workload)
  - Pending approvals (reports, billing actions)
  - Work order trends (weekly/monthly chart)

---

### Test Scenarios - Dashboard Widgets

**TS-DASH-007: Work Order Status Widget**
- **When**: Render WorkOrderStatusWidget
- **Then**: Displays pie chart with status breakdown (created, assigned, in_progress, completed)

**TS-DASH-008: Asset Health Widget**
- **When**: Render AssetHealthWidget
- **Then**: Displays bar chart with lifecycle status counts (active, warning, end_of_life, replaced)

**TS-DASH-009: SLA Compliance Widget**
- **Given**: 100 WOs, 85 completed on time
- **When**: Render SLAComplianceWidget
- **Then**: Displays 85% with color indicator (green if > 80%, yellow if 60-80%, red if < 60%)

**TS-DASH-010: Revenue Widget**
- **Given**: Total revenue this month = $50,000
- **When**: Render RevenueWidget
- **Then**: Displays "$50,000" with trend indicator (up/down vs last month)

**TS-DASH-011: Technician Workload Widget**
- **Given**: 5 technicians with varying assigned WO counts
- **When**: Render TechnicianWorkloadWidget
- **Then**: Displays horizontal bar chart, sorted by workload

**TS-DASH-012: Recent Activity Widget**
- **Given**: Last 10 actions (WO created, report submitted, invoice approved)
- **When**: Render RecentActivityWidget
- **Then**: Displays timeline/feed with timestamps

**TS-DASH-013: Upcoming Maintenance Widget**
- **Given**: 3 maintenance schedules due next week
- **When**: Render UpcomingMaintenanceWidget
- **Then**: Displays list with dates, asset names, schedule type

---

### Test Scenarios - Welcome Page

**TS-DASH-014: Welcome Page for Super Admin**
- **Given**: Super admin logged in
- **When**: Navigate to /welcome (or / redirect)
- **Then**: Displays:
  - Greeting "Welcome, {full_name}"
  - Current tasks: Pending employee approvals, system alerts
  - Quick actions: Create Company, View All Work Orders
  - Dashboard summary cards (companies, WOs, revenue)

**TS-DASH-015: Welcome Page for Technician**
- **Given**: Technician with 5 assigned work orders
- **When**: Navigate to /welcome
- **Then**: Displays:
  - Greeting "Welcome, {full_name}"
  - Current tasks: 5 assigned work orders (list with urgency indicators)
  - Quick actions: View My Work Orders, Log Hours
  - Performance summary (WOs completed this week)

**TS-DASH-016: Welcome Page for Client Admin**
- **Given**: Client admin with 3 pending invoice approvals
- **When**: Navigate to /welcome
- **Then**: Displays:
  - Greeting "Welcome, {full_name}"
  - Current tasks: 3 pending approvals, 8 open work orders
  - Quick actions: Approve Invoices, Create Work Order
  - Dashboard summary (sites, WOs, assets)

**TS-DASH-017: Welcome Page with No Current Tasks**
- **Given**: User with no assigned tasks
- **When**: Navigate to /welcome
- **Then**: Displays "No current tasks" message with quick action buttons

**TS-DASH-018: Welcome Page Redirects to Default on Login**
- **Given**: User logs in
- **When**: Authentication succeeds
- **Then**: Redirects to /welcome

---

### Test Scenarios - Dashboard Customization

**TS-DASH-019: User Saves Custom Widget Layout**
- **Given**: User drags widgets to reorder
- **When**: Click "Save Layout"
- **Then**: Layout saved to user.metadata_json, persists on reload

**TS-DASH-020: User Hides Widget**
- **Given**: Dashboard with 6 widgets
- **When**: Click "Hide" on RevenueWidget
- **Then**: Widget hidden, layout updates

**TS-DASH-021: User Restores Default Layout**
- **Given**: User has custom layout
- **When**: Click "Reset to Default"
- **Then**: Layout restored to role default

**TS-DASH-022: Widget Visibility Based on Role**
- **Given**: Super admin role
- **When**: View dashboard
- **Then**: All widget types available
- **Given**: Technician role
- **When**: View dashboard
- **Then**: Only technician-relevant widgets shown (no revenue, SLA)

---

### Test Scenarios - Dashboard Data Accuracy

**TS-DASH-023: Work Order Count Accuracy**
- **Given**: Tenant has 25 work orders
- **When**: View dashboard
- **Then**: WorkOrderCountWidget shows 25

**TS-DASH-024: Revenue Calculation Accuracy**
- **Given**: 10 paid invoices totaling $100,000
- **When**: View RevenueWidget
- **Then**: Displays "$100,000"

**TS-DASH-025: Asset Lifecycle Distribution Accuracy**
- **Given**: 50 assets (40 active, 8 warning, 2 end_of_life)
- **When**: View AssetHealthWidget
- **Then**: Chart shows correct distribution

**TS-DASH-026: Dashboard Data Respects Tenant Isolation**
- **Given**: Tenant A has 100 WOs, Tenant B has 50 WOs
- **When**: Tenant A admin views dashboard
- **Then**: Shows 100 WOs (not 150)

**TS-DASH-027: Dashboard Data Respects Role Scope**
- **Given**: Site manager for Site X (10 WOs), Site Y has 15 WOs
- **When**: Site manager views dashboard
- **Then**: Shows only 10 WOs (Site X)

---

### Test Scenarios - Real-Time Updates

**TS-DASH-028: Dashboard Auto-Refresh**
- **Given**: Dashboard displaying data
- **When**: Wait 60 seconds (polling interval)
- **Then**: Data refreshes automatically

**TS-DASH-029: Manual Refresh Button**
- **Given**: Dashboard with stale data
- **When**: Click "Refresh" button
- **Then**: Data immediately refetches and updates

**TS-DASH-030: WebSocket Real-Time Updates (Optional)**
- **Given**: WebSocket connection established
- **When**: New work order created in backend
- **Then**: Dashboard work order count increments without page reload

---

### Test Scenarios - Dashboard Performance

**TS-DASH-031: Dashboard Loads in < 2 Seconds**
- **Given**: Database with 10,000 work orders, 1,000 assets
- **When**: Load dashboard
- **Then**: Initial render completes in < 2 seconds

**TS-DASH-032: Widget Data Fetched in Parallel**
- **Given**: Dashboard with 6 widgets
- **When**: Load dashboard
- **Then**: All widget API calls fire simultaneously (not sequentially)

**TS-DASH-033: Cached Dashboard Data**
- **Given**: User viewed dashboard 30 seconds ago
- **When**: Navigate back to dashboard
- **Then**: Shows cached data immediately, then refreshes in background

---

### Test Scenarios - Chart Rendering

**TS-DASH-034: Pie Chart Renders Correctly**
- **Given**: WorkOrderStatusWidget with data
- **When**: Render chart
- **Then**: 
  - Pie chart displays with correct proportions
  - Legend shows status labels
  - Tooltips show exact counts on hover

**TS-DASH-035: Bar Chart Renders Correctly**
- **Given**: TechnicianWorkloadWidget with data
- **When**: Render chart
- **Then**: 
  - Horizontal bars display
  - Bars sorted by value
  - Axis labels visible

**TS-DASH-036: Line Chart for Trends**
- **Given**: Work order trend data (last 30 days)
- **When**: Render WorkOrderTrendWidget
- **Then**: 
  - Line chart shows daily counts
  - X-axis shows dates
  - Y-axis shows counts
  - Gridlines visible

**TS-DASH-037: Empty State for No Data**
- **Given**: New tenant with no work orders
- **When**: Render WorkOrderStatusWidget
- **Then**: Shows "No data available" message with illustration

---

### Test Scenarios - Dashboard Localization

**TS-DASH-038: Dashboard Labels in Arabic**
- **Given**: User locale is 'ar'
- **When**: View dashboard
- **Then**: 
  - All widget titles in Arabic
  - Chart labels in Arabic
  - Numbers use Arabic numerals

**TS-DASH-039: Dashboard Layout RTL**
- **Given**: User locale is 'ar'
- **When**: View dashboard
- **Then**: 
  - Widgets arranged right-to-left
  - Charts mirror correctly
  - Legends positioned on left

---

### Test Scenarios - Mobile Responsive Dashboard

**TS-DASH-040: Dashboard on Mobile (320px width)**
- **When**: View dashboard on mobile
- **Then**: 
  - Widgets stack vertically
  - Charts resize to fit
  - Touch gestures work (tap, swipe)

**TS-DASH-041: Dashboard on Tablet (768px width)**
- **When**: View dashboard on tablet
- **Then**: 
  - Widgets in 2-column grid
  - All content visible without horizontal scroll

---

## Summary

### Test Count by Feature

| Feature | Test Scenarios |
|---------|---------------|
| P2-F4: Labor Management | 34 scenarios |
| P2-F5: Location Management | 32 scenarios |
| P2-F6: Dashboards | 41 scenarios |
| **Total** | **107 scenarios** |

### Test Priority Matrix

| Priority | Scenarios | Examples |
|----------|-----------|----------|
| CRITICAL | 25 | Tenant isolation, RBAC, data accuracy |
| HIGH | 45 | Core functionality, CRUD operations |
| MEDIUM | 30 | UI components, performance |
| LOW | 7 | Customization, edge cases |

### Implementation Order

1. **Week 1**: P2-F4 Labor Management (Backend + Unit Tests)
2. **Week 2**: P2-F5 Location Management (Backend + Unit Tests)
3. **Week 3**: P2-F6 Dashboards (Backend + Unit Tests)
4. **Week 4**: Integration Tests + E2E Tests for all features
5. **Week 5**: Performance Tests, Localization Tests, Bug Fixes

---

**End of Test Scenarios Document**
