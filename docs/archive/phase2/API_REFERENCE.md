# Phase 2 API Reference

**Date:** April 18, 2026  
**Base URL:** `http://localhost:8000` (development)  
**Version:** 2.0

---

## Authentication

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Get Token

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=secret
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

---

## Dashboard Endpoints

### Get Dashboard Summary

```http
GET /dashboard/summary
Authorization: Bearer <token>
```

**Role-Aware Response Examples:**

**Super Admin / Company Admin:**
```json
{
  "role": "super_admin",
  "clients_count": 5,
  "sites_count": 12,
  "assets_count": 150,
  "open_work_orders": 23,
  "technicians_count": 8,
  "pending_invoices_draft": 4,
  "completed_this_week": 15,
  "assets_at_eol": 3
}
```

**Technician:**
```json
{
  "role": "technician",
  "my_assigned_open": 5,
  "my_in_progress": 2,
  "open_work_orders": 5,
  "completed_this_week": 8
}
```

**Client Admin:**
```json
{
  "role": "client_admin",
  "clients_count": 1,
  "sites_count": 3,
  "assets_count": 45,
  "open_work_orders": 7,
  "pending_invoices_draft": 2,
  "completed_this_week": 5,
  "assets_at_eol": 1
}
```

**Roles:** All roles  
**Tenant Scoped:** Yes  
**Filters:** Role-based automatic filtering

---

## Location Endpoints

### List Locations

```http
GET /locations?site_id=<uuid>
Authorization: Bearer <token>
```

**Query Parameters:**
- `site_id` (required) — UUID of site to list locations for

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "site_id": "550e8400-e29b-41d4-a716-446655440002",
    "parent_id": null,
    "name": "Building A",
    "location_type": "building",
    "sort_order": 0,
    "metadata_json": {},
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T10:00:00Z"
  }
]
```

**Roles:** super_admin, company_admin, client_admin, site_manager  
**Tenant Scoped:** Yes  
**Site Scoped:** Yes (site manager sees only assigned sites)

---

### Get Location Tree

```http
GET /locations/tree?site_id=<uuid>
Authorization: Bearer <token>
```

**Query Parameters:**
- `site_id` (required) — UUID of site to get tree for

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "site_id": "550e8400-e29b-41d4-a716-446655440002",
    "parent_id": null,
    "name": "Building A",
    "location_type": "building",
    "sort_order": 0,
    "children": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "site_id": "550e8400-e29b-41d4-a716-446655440002",
        "parent_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Floor 1",
        "location_type": "floor",
        "sort_order": 1,
        "children": []
      }
    ]
  }
]
```

**Roles:** super_admin, company_admin, client_admin, site_manager  
**Tenant Scoped:** Yes  
**Returns:** Hierarchical tree structure

---

### Create Location

```http
POST /locations
Authorization: Bearer <token>
Content-Type: application/json

{
  "site_id": "550e8400-e29b-41d4-a716-446655440002",
  "parent_id": null,
  "name": "Building B",
  "location_type": "building",
  "sort_order": 1,
  "metadata_json": {}
}
```

**Validation:**
- `site_id` must belong to same tenant
- `parent_id` (if provided) must belong to same site
- `name` required (max 255 chars)

**Response:** Location object (same as list)

**Roles:** super_admin, company_admin, client_admin, site_manager  
**Tenant Scoped:** Yes

---

### Update Location

```http
PATCH /locations/{location_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Building B - Updated",
  "sort_order": 2
}
```

**Partial Update:** All fields optional  
**Validation:** `parent_id` cannot be self or create cycle

**Response:** Updated location object

**Roles:** super_admin, company_admin, client_admin, site_manager  
**Tenant Scoped:** Yes

---

### Delete Location

```http
DELETE /locations/{location_id}
Authorization: Bearer <token>
```

**Validation:** Cannot delete if location has children

**Response:** 204 No Content

**Roles:** super_admin, company_admin, client_admin, site_manager  
**Tenant Scoped:** Yes

---

## Labor Management Endpoints

### List Technician Profiles

```http
GET /labor/profiles
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "hourly_rate_sar": 150.00,
    "overtime_multiplier": 1.5,
    "is_active": true,
    "skills_json": {"certifications": ["HVAC", "Electrical"]},
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T10:00:00Z"
  }
]
```

**Roles:** super_admin, company_admin, manager, technician  
**Technician Scope:** Technicians see only their own profile  
**Tenant Scoped:** Yes

---

### Create Technician Profile

```http
POST /labor/profiles
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "hourly_rate_sar": 150.00,
  "overtime_multiplier": 1.5,
  "is_active": true,
  "skills_json": {"certifications": ["HVAC"]}
}
```

**Validation:**
- `user_id` must exist in same tenant
- User must have role `technician`
- Cannot create duplicate profile for same user

**Response:** Profile object

**Roles:** super_admin, company_admin, manager  
**Tenant Scoped:** Yes

---

### Update Technician Profile

```http
PATCH /labor/profiles/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "hourly_rate_sar": 175.00,
  "is_active": false
}
```

**Partial Update:** All fields optional

**Response:** Updated profile object

**Roles:** super_admin, company_admin, manager  
**Tenant Scoped:** Yes

---

### List Labor Entries

```http
GET /labor/entries?work_order_id=<uuid>&user_id=<uuid>
Authorization: Bearer <token>
```

**Query Parameters:**
- `work_order_id` (optional) — Filter by work order
- `user_id` (optional) — Filter by technician

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "work_order_id": "550e8400-e29b-41d4-a716-446655440002",
    "user_id": "550e8400-e29b-41d4-a716-446655440003",
    "work_date": "2026-04-18",
    "hours_regular": 6.5,
    "hours_overtime": 1.5,
    "notes": "Completed HVAC repair",
    "created_at": "2026-04-18T16:00:00Z"
  }
]
```

**Roles:** super_admin, company_admin, manager, technician  
**Technician Scope:** Technicians see only their own entries  
**Tenant Scoped:** Yes

---

### Create Labor Entry

```http
POST /labor/entries
Authorization: Bearer <token>
Content-Type: application/json

{
  "work_order_id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440003",
  "work_date": "2026-04-18",
  "hours_regular": 6.5,
  "hours_overtime": 1.5,
  "notes": "Completed HVAC repair"
}
```

**Validation:**
- `work_order_id` must exist in same tenant
- `user_id` must exist in same tenant
- **Technicians:** Can only log hours for WOs where they are assignee
- **Technicians:** `user_id` must be their own ID

**Response:** Labor entry object

**Roles:** super_admin, company_admin, manager, technician  
**Tenant Scoped:** Yes  
**Special Rule:** Technicians limited to assigned WOs

---

### List Technician Schedules

```http
GET /labor/schedules?user_id=<uuid>
Authorization: Bearer <token>
```

**Query Parameters:**
- `user_id` (optional) — Filter by technician

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "day_of_week": 0,
    "start_time": "08:00:00",
    "end_time": "17:00:00",
    "is_active": true,
    "created_at": "2026-04-18T10:00:00Z"
  }
]
```

**Day of Week:** 0=Monday, 1=Tuesday, ..., 6=Sunday

**Roles:** super_admin, company_admin, manager, technician  
**Technician Scope:** Technicians see only their own schedule  
**Tenant Scoped:** Yes

---

### Create Technician Schedule

```http
POST /labor/schedules
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "day_of_week": 0,
  "start_time": "08:00:00",
  "end_time": "17:00:00",
  "is_active": true
}
```

**Validation:**
- `user_id` must exist in same tenant
- Unique constraint: (tenant_id, user_id, day_of_week)

**Response:** Schedule object

**Roles:** super_admin, company_admin, manager  
**Tenant Scoped:** Yes

---

### Delete Technician Schedule

```http
DELETE /labor/schedules/{schedule_id}
Authorization: Bearer <token>
```

**Response:** 204 No Content

**Roles:** super_admin, company_admin, manager  
**Tenant Scoped:** Yes

---

## Enhanced Filtering (Existing Endpoints)

### Work Orders with Filters

```http
GET /work-orders?status=open&urgency=high&site_id=<uuid>&date_from=2026-04-01&search=repair
Authorization: Bearer <token>
```

**New Query Parameters:**
- `status` — Filter by status (open, assigned, in_progress, completed, closed, cancelled)
- `urgency` — Filter by urgency (low, medium, high, urgent)
- `client_id` — Filter by client UUID
- `site_id` — Filter by site UUID
- `assignee_user_id` — Filter by assigned technician UUID
- `date_from` — Filter by created_at >= date (ISO 8601)
- `date_to` — Filter by created_at <= date (ISO 8601)
- `search` — Full-text search in title (case-insensitive)
- `tags` — Filter by tags (comma-separated: preventive,corrective)

**Example Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "client_id": "550e8400-e29b-41d4-a716-446655440002",
    "site_id": "550e8400-e29b-41d4-a716-446655440003",
    "location_id": "550e8400-e29b-41d4-a716-446655440004",
    "asset_id": "550e8400-e29b-41d4-a716-446655440005",
    "wo_number": "WO-2026-001234",
    "title": "HVAC System Repair",
    "description": "AC unit not cooling properly",
    "urgency": "high",
    "status": "in_progress",
    "tags": ["corrective", "urgent"],
    "assignee_user_id": "550e8400-e29b-41d4-a716-446655440006",
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T14:30:00Z"
  }
]
```

**Roles:** All roles (technicians see only assigned WOs)  
**Tenant Scoped:** Yes

---

### Assets with Filters

```http
GET /assets?site_id=<uuid>&category=hvac&search=unit&lifecycle_status=warning
Authorization: Bearer <token>
```

**New Query Parameters:**
- `site_id` — Filter by site UUID (existing, required for some roles)
- `category` — Filter by asset category
- `search` — Full-text search in asset name (case-insensitive)
- `lifecycle_status` — Filter by status (active, warning, end_of_life, replaced)

**Example Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "site_id": "550e8400-e29b-41d4-a716-446655440002",
    "location_id": "550e8400-e29b-41d4-a716-446655440003",
    "asset_number": "ASSET-001234",
    "name": "HVAC Unit - Building A",
    "category": "hvac",
    "lifecycle_status": "warning",
    "max_repair_count": 3,
    "current_repair_count": 2,
    "max_age_years": 5,
    "installed_on": "2021-04-18",
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T14:30:00Z"
  }
]
```

**Roles:** super_admin, company_admin, client_admin, site_manager, manager  
**Tenant Scoped:** Yes

---

### Invoices with Filters

```http
GET /invoices?status=draft&client_id=<uuid>&date_from=2026-04-01
Authorization: Bearer <token>
```

**New Query Parameters:**
- `status` — Filter by status (draft, sent, paid, overdue, cancelled)
- `client_id` — Filter by client UUID
- `date_from` — Filter by issued_at >= date (ISO 8601)
- `date_to` — Filter by issued_at <= date (ISO 8601)

**Example Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
    "client_id": "550e8400-e29b-41d4-a716-446655440002",
    "invoice_number": "INV-2026-001234",
    "status": "draft",
    "subtotal_sar": 5000.00,
    "tax_sar": 750.00,
    "total_sar": 5750.00,
    "issued_at": "2026-04-18T10:00:00Z",
    "due_at": "2026-05-18T10:00:00Z",
    "created_at": "2026-04-18T10:00:00Z",
    "updated_at": "2026-04-18T14:30:00Z"
  }
]
```

**Roles:** super_admin, company_admin, client_admin, manager  
**Tenant Scoped:** Yes

---

## Asset Lifecycle Endpoints

### Check Asset Lifecycle

Asset lifecycle status is automatically updated when:
1. Asset reaches `max_repair_count` (via work order completion)
2. Asset exceeds `max_age_years` (calculated from `installed_on`)

**Status Transitions:**
- `active` → `warning` (approaching limits)
- `warning` → `end_of_life` (limits reached)
- `end_of_life` → `replaced` (after replacement WO created)

**Automatic Actions:**
- When status changes to `end_of_life`, a replacement work order is created
- Replacement WO has title: "Replace Asset: {asset_name}"

**Check via GET /assets/{id}:**

```http
GET /assets/{asset_id}
Authorization: Bearer <token>
```

**Response includes lifecycle fields:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "lifecycle_status": "warning",
  "max_repair_count": 3,
  "current_repair_count": 2,
  "max_age_years": 5,
  "installed_on": "2021-04-18",
  "age_years": 5.0
}
```

**Roles:** super_admin, company_admin, client_admin, site_manager, manager  
**Tenant Scoped:** Yes

---

## Error Responses

### Common Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Insufficient permissions for role |
| 404 | Not Found | Resource doesn't exist or wrong tenant |
| 409 | Conflict | Duplicate entry, constraint violation |
| 422 | Unprocessable Entity | Invalid request body schema |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "NOT_FOUND"
}
```

or

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

**Not implemented in Phase 2** — Consider for Phase 3:
- 100 requests/minute per user
- 1000 requests/minute per tenant
- Burst allowance: 20 requests

---

## Pagination

**Not implemented in Phase 2** — All list endpoints return full results.

**Consider for Phase 3:**
- `limit` — Number of results per page (default 50, max 200)
- `offset` — Number of results to skip
- Response includes total count

---

## Best Practices

### Authentication
- Store JWT token securely (localStorage or httpOnly cookie)
- Include `Authorization: Bearer <token>` header on all requests
- Handle 401 errors by redirecting to login
- Refresh token before expiry (not implemented in Phase 2)

### Error Handling
- Check response status code before parsing JSON
- Display user-friendly error messages
- Log technical errors for debugging
- Handle 403 errors by showing "insufficient permissions" message

### Performance
- Use filters to reduce payload size
- Cache dashboard data (invalidate on relevant changes)
- Debounce search input (300ms delay)
- Implement optimistic UI updates for better UX

### Security
- Never log JWT tokens
- Validate all user input on frontend
- Trust backend validation (don't bypass)
- Use HTTPS in production

---

## Changelog

### Phase 2 (v2.0) - April 18, 2026
- Added `/dashboard/summary` endpoint
- Added `/locations/*` endpoints (CRUD + tree)
- Added `/labor/*` endpoints (profiles, entries, schedules)
- Enhanced filtering on `/work-orders`, `/assets`, `/invoices`
- Added `lifecycle_status` to assets
- Added `tags` to work orders
- Added `location_id` to assets and work orders

### Phase 1 (v1.0) - April 10, 2026
- Initial MVP endpoints
- Basic CRUD for clients, sites, assets, work orders, invoices
- User authentication and RBAC

---

**API Version:** 2.0  
**Last Updated:** April 18, 2026  
**Maintained By:** FMS Development Team
