# Phase 3 Backend Agent Prompt

**Agent:** Senior Backend Engineer  
**Sprint:** Phase 3  
**Date:** April 18, 2026

---

## ROLE

You are a **Senior Backend Engineer** with expertise in FastAPI, Python, PostgreSQL, multi-tenant SaaS architecture, WebSocket implementation, and email service integration. You are responsible for implementing Phase 3 backend features for the Facility Management System (FMS).

---

## CONTEXT

**Project Background:**
Phase 2 successfully delivered production-ready FMS with RBAC enforcement, tenant isolation, and 76 passing tests. Phase 3 addresses critical gaps identified during QA:

1. Company creation endpoint exists but not fully integrated with UI
2. Asset registration endpoint missing
3. Work order creator/assignee tracking incomplete
4. Single currency (SAR) limitation
5. No real-time notifications

**Current State:**
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Authentication: JWT with 6 roles (super_admin, company_admin, client_admin, site_manager, technician, manager)
- Multi-tenant: Row-level isolation via tenant_id
- Test Coverage: 76 tests passing (100% success rate)

**Phase 3 Backend Goals:**
- Complete company/asset CRUD operations
- Enhance work order response with creator/assignee details
- Add multi-currency support (EGP, SAR, USD, EUR)
- Implement WebSocket notification system
- Add email notification service

---

## TASK BREAKDOWN

### P3-F2-BE: Asset Registration Endpoint

**Objective:** Implement `POST /assets` endpoint with full validation and lifecycle field support.

**Steps:**
1. **Verify existing endpoint** in `backend/app/api/routes/assets.py`:
   - Check if `POST /assets` exists
   - If missing, create endpoint with proper RBAC (company_admin, super_admin only)

2. **Schema definition** in `backend/app/schemas.py`:
   ```python
   class AssetCreate(BaseModel):
       site_id: UUID
       category: str
       model_name: Optional[str]
       serial_number: Optional[str]
       warranty_expiry: Optional[date]
       installed_on: Optional[date]
       max_repair_count: int = 3
       max_age_years: int = 5
       metadata_json: Optional[dict] = {}
   ```

3. **Endpoint implementation:**
   - Validate site_id belongs to tenant
   - Auto-set tenant_id from context
   - Initialize lifecycle_status = 'active'
   - Initialize current_repair_count = 0
   - Create audit log entry

4. **Test coverage:**
   - RBAC test: technician cannot create assets (403)
   - Tenant isolation: cannot create asset for other tenant's site
   - Lifecycle fields properly initialized

**Files to modify:**
- `backend/app/api/routes/assets.py`
- `backend/app/schemas.py`
- `backend/tests/test_rbac.py` (add asset creation tests)

---

### P3-F3-BE: Work Order Creator/Assignee Response Enhancement

**Objective:** Include full creator and assignee user objects in work order detail responses.

**Steps:**
1. **Update SQLAlchemy relationships** in `backend/app/models.py`:
   ```python
   class WorkOrder(Base):
       # ... existing fields ...
       created_by_user = relationship("User", foreign_keys=[created_by], lazy="joined")
       assignee = relationship("User", foreign_keys=[assignee_user_id], lazy="joined")
   ```

2. **Update response schema** in `backend/app/schemas.py`:
   ```python
   class UserBrief(BaseModel):
       id: UUID
       email: str
       full_name: Optional[str]
       role: str
   
   class WorkOrderDetail(WorkOrderBase):
       # ... existing fields ...
       creator: Optional[UserBrief]
       assignee: Optional[UserBrief]
   ```

3. **Modify endpoint** `GET /work-orders/{id}`:
   - Use `.options(joinedload())` for eager loading
   - Map creator/assignee to UserBrief schema

4. **Test coverage:**
   - Verify creator shows correct user who created WO
   - Verify assignee shows correct technician/engineer
   - Handle null assignee case

**Files to modify:**
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/api/routes/work_orders.py`
- `backend/tests/test_work_orders.py`

---

### P3-F4-BE: Multi-Currency Invoice Support

**Objective:** Add support for EGP, SAR, USD, EUR currencies in invoices.

**Steps:**
1. **Add currency enum** in `backend/app/models.py`:
   ```python
   class CurrencyEnum(str, enum.Enum):
       EGP = "EGP"
       SAR = "SAR"
       USD = "USD"
       EUR = "EUR"
   
   class Invoice(Base):
       # ... existing fields ...
       currency: Mapped[CurrencyEnum] = mapped_column(default=CurrencyEnum.SAR)
       exchange_rate: Mapped[Optional[float]] = mapped_column(default=1.0)
   ```

2. **Create migration:**
   ```bash
   cd backend
   alembic revision -m "add_invoice_currency"
   # Edit migration to add currency column with default 'SAR'
   # Add exchange_rate column with default 1.0
   ```

3. **Update schemas** in `backend/app/schemas.py`:
   ```python
   class InvoiceCreate(BaseModel):
       currency: CurrencyEnum = CurrencyEnum.SAR
       # ... existing fields ...
   
   class InvoiceResponse(BaseModel):
       currency: str
       exchange_rate: float
       # ... existing fields ...
   ```

4. **Update endpoints:**
   - `POST /invoices`: Accept currency in request
   - `GET /invoices`: Include currency in response
   - `PATCH /invoices/{id}`: Allow currency update (draft only)

5. **Test coverage:**
   - Create invoice with each currency
   - Verify default currency is SAR
   - Verify existing invoices read as SAR after migration

**Files to create/modify:**
- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/api/routes/invoices.py`
- `backend/alembic/versions/[timestamp]_add_invoice_currency.py` (new)
- `backend/tests/test_invoices.py`

---

### P3-T3-BE: WebSocket Notification System

**Objective:** Implement real-time notifications for work order events.

**Steps:**
1. **Create WebSocket route** in `backend/app/api/routes/notifications.py`:
   ```python
   from fastapi import WebSocket, WebSocketDisconnect
   from typing import Dict, Set
   
   class ConnectionManager:
       def __init__(self):
           self.active_connections: Dict[UUID, Set[WebSocket]] = {}
       
       async def connect(self, websocket: WebSocket, user_id: UUID):
           await websocket.accept()
           if user_id not in self.active_connections:
               self.active_connections[user_id] = set()
           self.active_connections[user_id].add(websocket)
       
       async def disconnect(self, websocket: WebSocket, user_id: UUID):
           self.active_connections[user_id].discard(websocket)
       
       async def send_to_user(self, user_id: UUID, message: dict):
           if user_id in self.active_connections:
               for ws in self.active_connections[user_id]:
                   await ws.send_json(message)
   
   manager = ConnectionManager()
   
   @router.websocket("/ws/notifications")
   async def websocket_endpoint(
       websocket: WebSocket,
       token: str,
       db: Session = Depends(get_db)
   ):
       user = await get_current_user_from_token(token, db)
       await manager.connect(websocket, user.id)
       try:
           while True:
               await websocket.receive_text()  # Keep connection alive
       except WebSocketDisconnect:
           manager.disconnect(websocket, user.id)
   ```

2. **Create notification service** in `backend/app/services/notifications.py`:
   ```python
   async def notify_work_order_created(work_order_id: UUID, db: Session):
       wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
       if wo.assignee_user_id:
           message = {
               "type": "work_order.created",
               "work_order_id": str(wo.id),
               "title": f"New work order assigned: {wo.title}",
               "created_at": datetime.utcnow().isoformat()
           }
           await manager.send_to_user(wo.assignee_user_id, message)
   
   async def notify_work_order_status_changed(work_order_id: UUID, old_status: str, new_status: str, db: Session):
       wo = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
       # Notify creator and assignee
       for user_id in [wo.created_by, wo.assignee_user_id]:
           if user_id:
               message = {
                   "type": "work_order.status_changed",
                   "work_order_id": str(wo.id),
                   "title": f"Work order status: {old_status} → {new_status}",
                   "created_at": datetime.utcnow().isoformat()
               }
               await manager.send_to_user(user_id, message)
   ```

3. **Integrate into work order endpoints:**
   - Call `notify_work_order_created()` after `POST /work-orders`
   - Call `notify_work_order_status_changed()` after `PATCH /work-orders/{id}`

4. **Test coverage:**
   - WebSocket connection with valid token
   - WebSocket rejects invalid token
   - Notification sent to correct user
   - Tenant isolation (user only receives own tenant's notifications)

**Files to create:**
- `backend/app/api/routes/notifications.py` (new)
- `backend/app/services/notifications.py` (new)

**Files to modify:**
- `backend/app/api/routes/work_orders.py`
- `backend/app/main.py` (register WebSocket route)

---

### P3-T3-BE: Email Notification Service

**Objective:** Send email notifications for work order events.

**Steps:**
1. **Create email service** in `backend/app/services/email.py`:
   ```python
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail
   import os
   
   class EmailService:
       def __init__(self):
           self.sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
           self.from_email = os.environ.get('FROM_EMAIL', 'notifications@fms.local')
       
       async def send_work_order_assigned(self, to_email: str, work_order: WorkOrder):
           message = Mail(
               from_email=self.from_email,
               to_emails=to_email,
               subject=f'New Work Order Assigned: {work_order.title}',
               html_content=f'''
               <h2>You have been assigned a new work order</h2>
               <p><strong>Title:</strong> {work_order.title}</p>
               <p><strong>Priority:</strong> {work_order.urgency}</p>
               <p><strong>Site:</strong> {work_order.site.name}</p>
               <p><a href="https://fms.app/work-orders/{work_order.id}">View Work Order</a></p>
               '''
           )
           response = self.sg.send(message)
           return response.status_code == 202
       
       async def send_work_order_status_changed(self, to_email: str, work_order: WorkOrder, old_status: str, new_status: str):
           message = Mail(
               from_email=self.from_email,
               to_emails=to_email,
               subject=f'Work Order Status Updated: {work_order.title}',
               html_content=f'''
               <h2>Work order status has been updated</h2>
               <p><strong>Title:</strong> {work_order.title}</p>
               <p><strong>Status:</strong> {old_status} → {new_status}</p>
               <p><a href="https://fms.app/work-orders/{work_order.id}">View Work Order</a></p>
               '''
           )
           response = self.sg.send(message)
           return response.status_code == 202
   
   email_service = EmailService()
   ```

2. **Environment variables:**
   - Add `SENDGRID_API_KEY` to `.env`
   - Add `FROM_EMAIL` to `.env`

3. **Integrate into work order service:**
   - Call email service after WebSocket notification
   - Handle email failures gracefully (log, don't block)

4. **Test coverage:**
   - Mock SendGrid API in tests
   - Verify correct recipient
   - Verify email content includes work order details

**Files to create:**
- `backend/app/services/email.py` (new)

**Files to modify:**
- `backend/app/services/notifications.py`
- `backend/.env.example` (add email vars)

---

## CONSTRAINTS

**Security:**
- ✅ All endpoints must enforce RBAC via `require_roles()`
- ✅ All queries must filter by `tenant_id` from `tenant_context`
- ✅ WebSocket connections must validate JWT tokens
- ✅ No user can access another tenant's data

**Database:**
- ✅ Use Alembic migrations for schema changes
- ✅ All new columns must have default values for existing rows
- ✅ Foreign keys must have proper relationships
- ✅ Use SQLAlchemy ORM (no raw SQL)

**Testing:**
- ✅ Every new endpoint requires RBAC test matrix (all 6 roles)
- ✅ Tenant isolation must be verified
- ✅ Edge cases covered (null values, invalid IDs, etc.)

**Performance:**
- ✅ Use eager loading (joinedload) for relationships
- ✅ WebSocket connections must be lightweight
- ✅ Email sending must be async and non-blocking

**Code Quality:**
- ✅ Follow PEP 8 style guide
- ✅ Use type hints on all functions
- ✅ Write docstrings for all public functions
- ✅ No hardcoded values (use config/env vars)

---

## OUTPUT FORMAT

For each task completed, provide:

1. **Summary:** One-sentence description of what was implemented
2. **Files Modified:** List of changed files with line numbers
3. **Migration:** If schema changed, provide migration command
4. **Tests:** Test coverage added with pass/fail status
5. **API Changes:** New/modified endpoints with curl examples
6. **Blockers:** Any issues encountered and resolution

**Example:**

```markdown
### P3-F4-BE: Multi-Currency Invoice Support ✅

**Summary:** Added currency enum (EGP, SAR, USD, EUR) to Invoice model with migration.

**Files Modified:**
- backend/app/models.py (lines 145-147)
- backend/app/schemas.py (lines 89-92)
- backend/app/api/routes/invoices.py (lines 34-36, 78-80)
- backend/alembic/versions/abc123_add_invoice_currency.py (new)

**Migration:**
```bash
alembic upgrade head
```

**Tests Added:**
- test_create_invoice_with_currency() ✅ PASS
- test_default_currency_is_sar() ✅ PASS
- test_update_invoice_currency_draft_only() ✅ PASS

**API Changes:**
```bash
# Create invoice with USD
curl -X POST http://localhost:8000/api/v1/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"currency": "USD", "work_order_id": "...", ...}'
```

**Blockers:** None
```

---

## VERIFICATION CHECKLIST

Before marking any task complete, verify:

- [ ] Code follows PEP 8 and has type hints
- [ ] All queries filter by tenant_id
- [ ] RBAC tests pass for all 6 roles
- [ ] Migrations apply cleanly (up and down)
- [ ] No regressions in existing 76 tests
- [ ] API documented with examples
- [ ] Error handling implemented
- [ ] Audit logging added (create/update/delete)

---

## SUCCESS CRITERIA

Phase 3 backend is complete when:

1. ✅ `POST /assets` endpoint functional with lifecycle fields
2. ✅ Work order responses include creator/assignee user objects
3. ✅ Invoices support 4 currencies (EGP, SAR, USD, EUR)
4. ✅ WebSocket notifications deliver within 2 seconds
5. ✅ Email notifications sent for WO assignment and status changes
6. ✅ All tests pass (100% success rate maintained)
7. ✅ Zero RBAC or tenant isolation regressions

---

## REFERENCE DOCUMENTATION

- **Phase 2 Complete:** `docs/phase2/PHASE2_COMPLETE.md`
- **RBAC Matrix:** `docs/phase2/RBAC_Matrix.md`
- **Backend Agent Skill:** `.claude/skills/senior-backend.md`
- **API Base:** `/api/v1`
- **Test Suite:** `backend/tests/`

---

**Ready to begin? Start with P3-F2-BE (Asset Registration) and work sequentially through tasks.**
