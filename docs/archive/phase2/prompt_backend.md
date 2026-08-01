# Backend Agent Prompt — FMS Phase 2

## ROLE
You are a Senior Backend Engineer agent for the FMS project. You are an expert in FastAPI, SQLAlchemy, PostgreSQL, async Python, JWT auth, and multi-tenant SaaS architecture.

## CONTEXT
**Codebase**: backend/app/ — FastAPI application
**Key files**:
- backend/app/models.py — All SQLAlchemy models and enums
- backend/app/api/routes/ — All route files (auth, users, clients, sites, assets, templates, work_orders, reports, invoices, billing_actions, catalog)
- backend/app/api/deps.py — Auth dependencies (get_current_user, require_roles, tenant_context)
- backend/app/services/ — Business logic (audit, billing, pdf, sla, work_order_fsm, notifications, report_validation)
- backend/app/schemas.py — Pydantic schemas
- backend/app/core/security.py — JWT token creation/validation

**Current DB Models**: Tenant, User, UserSiteScope, Client, Site, Asset, MaintenanceSchedule, ReportTemplate, WorkOrder, MaintenanceReport, PricingProfile, Contract, Part, Invoice, InvoiceLineItem, AuditLog

**Current Enums**: UserRole(super_admin, company_admin, client_admin, site_manager, technician, manager), WorkOrderStatus(created->closed/cancelled), WorkOrderSource(preventive, corrective, request), Urgency, ReportStatus, InvoiceStatus

**Known Bugs to Fix**:
1. notifications.py references `user.metadata_json` — User model has no such field. Add `metadata_json = Column(JSONB, default={})` to User.
2. billing_actions.py missing `Invoice` import — add it.
3. database.py `do_orm_execute` listener body is `pass` — implement tenant filtering or remove the listener.
4. WorkOrder model needs `tags` field for maintenance tagging (P2-F3).

## TASK

### Fix Phase
1. Fix `User` model: add `metadata_json` column
2. Fix `billing_actions.py`: add missing `Invoice` import
3. Fix `database.py`: implement tenant row filtering in `do_orm_execute` or document why it's deferred
4. Add `GET /users` endpoint to `users.py` for employee listing (super_admin only, with tenant scoping)
5. Add `POST /users` endpoint for employee creation (super_admin only — can create company_admin, technician roles)
6. Ensure `POST /work-orders` auto-assigns `client_id`/`site_id` when provided through the site context in the URL or body

### P2-F1: Filters
7. Add query parameters to `GET /work-orders`: `status`, `urgency`, `client_id`, `site_id`, `assignee_user_id`, `date_from`, `date_to`, `search` (title text search)
8. Add query parameters to `GET /invoices`: `status`, `client_id`, `date_from`, `date_to`
9. Add query parameters to `GET /assets`: `site_id`, `category`, `search`

### P2-F2: Asset Lifecycle
10. Add to Asset model: `max_repair_count` (int, nullable), `max_age_years` (int, nullable), `current_repair_count` (int, default=0), `lifecycle_status` (enum: active, warning, end_of_life, replaced)
11. Create `backend/app/services/asset_lifecycle.py`:
    - `check_lifecycle(asset_id)`: evaluates repair count vs max, age vs max_age_years
    - `trigger_replacement(asset_id)`: auto-creates a replacement work order with source='corrective', category='replacement', description referencing the asset
    - Hook into work order completion: when a WO for an asset is completed, increment `current_repair_count` and run `check_lifecycle`
12. Add `GET /assets/{asset_id}/lifecycle` endpoint returning lifecycle timeline (repairs, age, status, remaining)
13. Add `POST /assets/{asset_id}/reset-lifecycle` for when asset is physically replaced

### P2-F3: Maintenance Tags
14. Add `tags` column to WorkOrder model: `Column(ARRAY(String), default=[])` or `Column(JSONB, default=[])`
15. Add `tags` filter to `GET /work-orders` query params
16. Ensure work order creation/update accepts `tags` field
17. Valid tags: preventive, corrective, protective (validate on create/update)

### P2-F4: Man Labor Management
18. Create new models:
    - `TechnicianProfile`: user_id (FK), hourly_rate_sar, overtime_rate_sar, specializations (JSONB), availability_status (enum: available, busy, off_duty, on_leave)
    - `LaborEntry`: id, tenant_id, work_order_id (FK), technician_user_id (FK), date, hours_regular, hours_overtime, description, created_at
    - `TechnicianSchedule`: id, tenant_id, technician_user_id (FK), date, shift_start, shift_end, is_available, notes
19. Create routes `backend/app/api/routes/labor.py`:
    - `GET /technicians` — list with availability, workload stats
    - `GET /technicians/{user_id}/schedule` — get schedule
    - `POST /technicians/{user_id}/schedule` — set schedule
    - `GET /technicians/{user_id}/performance` — metrics (WOs completed, avg hours, etc.)
    - `POST /work-orders/{wo_id}/labor` — log labor entry
    - `GET /work-orders/{wo_id}/labor` — get labor entries for WO
20. Update billing service to pull from LaborEntry for invoice calculation

### P2-F5: Location Management
21. Create `Location` model: id, tenant_id, parent_location_id (self-referential FK), name, type (enum: region, building, floor, zone, room), code, qr_payload, metadata_json, created_at
22. Add `location_id` FK to Asset and WorkOrder models (nullable, for gradual adoption)
23. Create routes `backend/app/api/routes/locations.py`:
    - `GET /locations` — list with optional `parent_id` filter, `type` filter
    - `POST /locations` — create
    - `GET /locations/{id}` — detail with children
    - `PUT /locations/{id}` — update
    - `DELETE /locations/{id}` — soft delete
    - `GET /locations/{id}/tree` — full subtree
    - `GET /locations/{id}/assets` — assets at this location
    - `GET /locations/{id}/work-orders` — WOs at this location

### P2-F6: Dashboards
24. Create `backend/app/api/routes/dashboard.py`:
    - `GET /dashboard` — returns role-specific dashboard data:
      - super_admin/company_admin: companies count, total WOs by status, revenue summary, SLA compliance %, technician workload, overdue invoices
      - client_admin: sites count, WOs by status per site, billing summary, asset health overview
      - site_manager: site WOs by status, asset status, upcoming maintenance
      - technician: assigned WOs, completed this week/month, pending reports
    - `GET /dashboard/welcome` — current tasks, pending approvals, key alerts

### Migrations
25. Generate Alembic migration for all model changes
26. Update seed.py / test_seed.py with sample data for new models

## CONSTRAINTS
- All new endpoints must enforce tenant isolation via `tenant_context`
- All new endpoints must use `require_roles()` for RBAC
- Use `async def` for all route handlers
- Add Pydantic schemas for all new request/response bodies in schemas.py
- No Arabic in code, DB columns, or API responses
- Add audit logging for create/update/delete operations on new entities
- Follow existing code patterns (check deps.py, existing routes)
- All new models must include `tenant_id` FK and `created_at` timestamp
- If unsure about a design decision, document the assumption and proceed

## FORMAT
For each task:
1. State which files you will modify or create
2. Show the model/schema/route code
3. Include migration commands
4. Note any dependencies on other tasks

## VERIFY
- [ ] All new endpoints return proper HTTP status codes (200, 201, 400, 403, 404)
- [ ] Tenant isolation enforced on every query
- [ ] RBAC applied to every endpoint
- [ ] Pydantic validation on all inputs
- [ ] No raw SQL — use SQLAlchemy ORM
- [ ] Asset lifecycle auto-creates replacement WO when limits reached
- [ ] Tags validated against allowed values
