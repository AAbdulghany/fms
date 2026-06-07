# Multi-Tenancy — Learning Data Isolation

> **Goal**: Understand how FMS keeps each organization's data completely separate. Learn to build a multi-tenant system.

---

## Why Multi-Tenancy?

### The Problem: Sharing vs Isolation

```
┌─────────────────────────────────────────────────────────────┐
│      Single-Tenant (Each customer gets own DB)             │
├─────────────────────────────────────────────────────────────┤
│  Company A: DB_A                                        │
│  Company B: DB_B                                        │
│  Company C: DB_C                                        │
│                                                             │
│  ✅ Completely isolated                                 │
│  ❌ Expensive (one DB per customer)                     │
│  ❌ Hard to manage                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│      Multi-Tenant (Shared DB, separated by tenant_id)            │
├─────────────────────────────────────────────────────────────┤
│  Shared PostgreSQL Database:                             │
│  ┌─────────────────────────────────────────────┐         │
│  │ tenants:                                   │         │
│  │   - uuid: tenant-a, name: Company A         │         │
│  │   - uuid: tenant-b, name: Company B         │         │
│  │                                           │         │
│  │ users: tenant_id, email, role             │         │
│  │   - tenant-a, john@A.com, admin        │         │
│  │   - tenant-b, jane@B.com, admin        │         │
│  │                                           │         │
│  │ work_orders: tenant_id, title           │         │
│  │   - tenant-a, Fix AC                  │         │
│  │   - tenant-b, Fix heating             │         │
│  └─────────────────────────────────────────────┘         │
│                                                             │
│  ✅ Cost-effective (one DB for all)                       │
│  ✅ Easy to manage                                       │
│  ✅ Each sees only their data                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. The Tenant Model

### What is a Tenant?

A tenant is like a **company account** in the system:

```python
class Tenant(Base):
    __tablename__ = "tenants"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[str] = mapped_column(String(32), default="active")
    
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
```

---

## 2. Every Table Has tenant_id

### The Golden Rule

```
┌─────────────────────────────────────────────────────────────┐
│         THE GOLDEN RULE OF MULTI-TENANCY               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Every table that stores tenant data MUST have:                 │
│                                                             │
│  tenant_id: Mapped[uuid.UUID] = mapped_column(              │
│      UUID(as_uuid=True),                                     │
│      ForeignKey("tenants.id")                                │
│  )                                                         │
│                                                             │
│  Then EVERY query MUST filter by:                          │
│                                                             │
│  .where(Model.tenant_id == current.tenant_id)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### FMS Tables with tenant_id

```python
# ALL of these have tenant_id!
class User(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

class Client(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

class Site(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

class Asset(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

class WorkOrder(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )

class Invoice(Base):
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False
    )
```

---

## 3. The Isolation Pattern in Code

### Always Filter by Tenant

```python
# ❌ WRONG - leaks data across tenants!
@router.get("/work-orders")
def list_work_orders(db: Session = Depends(get_db)):
    return db.scalars(select(WorkOrder)).all()  # Returns ALL tenants!


# ✅ CORRECT - filter by current tenant
@router.get("/work-orders")
def list_work_orders(
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(WorkOrder)
        .where(WorkOrder.tenant_id == current.tenant_id)
    ).all()  # Only returns current tenant's data!
```

### Get Single Item Pattern

```python
def get_work_order(
    work_order_id: UUID,
    current: User,
    db: Session,
) -> WorkOrder:
    """Get work order with tenant isolation."""
    
    # 1. Get the record
    wo = db.get(WorkOrder, work_order_id)
    
    # 2. Check tenant - MUST do this for every get!
    # Returns 404 (not 403) to prevent enumeration
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="NOT_FOUND"
        )
    
    return wo
```

### Create with Tenant

```python
@router.post("/work-orders")
def create_work_order(
    body: WorkOrderCreate,
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Create work order - tenant is automatic!"""
    
    wo = WorkOrder(
        # automatic from current user!
        tenant_id=current.tenant_id,
        
        # from request body
        client_id=body.client_id,
        site_id=body.site_id,
        title=body.title,
    )
    
    db.add(wo)
    db.commit()
    return wo
```

---

## 4. Understanding get_current_user

### Why This Is Critical

The `get_current_user` dependency does TWO things:
1. **Authenticates** the user (is who they say?)
2. **Provides tenant context** (which organization?)

```python
def get_current_user(
    token: str = Depends(HTTPBearer),
    db: Session = Depends(get_db),
) -> User:
    """Validate token and return user with tenant context."""
    
    # 1. Decode token
    payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # 2. Token contains tenant_id!
    tenant_id = payload.get("tenant_id")
    user_id = payload.get("sub")
    
    # 3. Get user - verify they belong to that tenant
    user = db.get(User, UUID(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(401)
    
    # Important: Also verify tenant matches!
    if str(user.tenant_id) != tenant_id:
        raise HTTPException(401)
    
    # 4. Return user - contains tenant_id for all endpoints
    return user
```

---

## 5. Role-Based Secondary Filtering

### Beyond Tenant: Role Scoping

Even within ONE tenant, different users see different data:

```
┌─────────────────────────────────────────────────────────────┐
│           ROLE-BASED FILTERING WITHIN TENANT                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tenant A (Acme Corp):                                   │
│  ┌─────────────────────────────────────────────┐          │
│  │ Super Admin (admin@acme.com)                │          │
│  │   → Sees ALL work orders                  │          │
│  │                                        │          │
│  │ Client Admin (client@acme.com)           │          │
│  │   → Sees ONLY client_x's work orders    │          │
│  │                                        │          │
│  │ Site Manager (site1@acme.com)          │          │
│  │   → Sees ONLY assigned site's WOs      │          │
│  │                                        │          │
│  │ Technician (tech@acme.com)             │          │
│  │   → Sees ONLY assigned WOs             │          │
│  └─────────────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### How FMS Implements Role Filtering

```python
@router.get("/work-orders")
def list_work_orders(
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # Start with tenant filter
    q = select(WorkOrder).where(
        WorkOrder.tenant_id == current.tenant_id
    )
    
    # Then add role-based filtering
    if current.role == UserRole.technician:
        # Technicians see only their assigned WOs
        q = q.where(WorkOrder.assignee_user_id == current.id)
    
    elif current.role == UserRole.client_admin and current.client_id:
        # Client admins see only their client's WOs
        q = q.where(WorkOrder.client_id == current.client_id)
    
    elif current.role == UserRole.site_manager:
        # Site managers see only their scoped sites
        from app.models import UserSiteScope
        scoped = db.scalars(
            select(UserSiteScope.site_id)
            .where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped:
            q = q.where(WorkOrder.site_id.in_(scoped))
        else:
            q = q.where(false())  # Empty result
    
    return db.scalars(q).all()
```

---

## 6. The Security Principle: 404 vs 403

### Why This Matters

```
┌─────────────────────────────────────────────────────────────┐
│        NEVER RETURN 403 FOR TENANT VIOLATIONS                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User from Tenant A tries to access Tenant B's work order:      │
│                                                             │
│  ❌ Returns 403: "Access Denied"                           │
│     → Attacker now knows:                                    │
│        - The work order ID exists                          │
│        - They can try other IDs!                          │
│                                                             │
│  ✅ Returns 404: "Not Found"                               │
│     → Attacker sees:                                        │
│        - The work order doesn't exist (for them)           │
│        - No way to enumerate IDs!                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Correct Pattern

```python
# Always return 404 (not 403!) for tenant violations
if not work_order or work_order.tenant_id != current.tenant_id:
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        detail="NOT_FOUND"  # Generic message!
    )
```

---

## 7. UserSiteScope: Fine-Grained Access

### For Site Managers

Some users should only access specific sites:

```python
class UserSiteScope(Base):
    """Sites a user can access (for site managers)."""
    
    __tablename__ = "user_site_scopes"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True
    )
    
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.id"),
        primary_key=True
    )
```

### Assigning Sites

```python
@router.post("/users/{user_id}/scopes")
def assign_site_scopes(
    user_id: UUID,
    body: SiteScopesUpdate,
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Assign sites to a user."""
    
    # Remove old scopes
    db.execute(
        delete(UserSiteScope).where(
            UserSiteScope.user_id == user_id
        )
    )
    
    # Add new scopes
    for site_id in body.site_ids:
        db.add(UserSiteScope(
            user_id=user_id,
            site_id=site_id
        ))
    
    db.commit()
```

---

## 8. Testing Isolation

### How FMS Tests Isolation

Look at `backend/tests/test_isolation.py`:

```python
@pytest.mark.asyncio
async def test_other_tenant_work_order_not_found(tenant_a_user, tenant_b_wo):
    """User A should NOT see Tenant B's work order."""
    
    # Get client for tenant A
    client = create_client(tenant_a_user)
    
    # Try to access tenant B's work order
    response = await client.get(
        f"/api/v1/work-orders/{tenant_b_wo.id}"
    )
    
    # ✅ Returns 404, NOT 403!
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_random_uuid_returns_404(user):
    """Random UUID should return 404."""
    
    client = create_client(user)
    
    # Try random UUID
    response = await client.get(
        f"/api/v1/work-orders/{uuid.uuid4()}"
    )
    
    # Prevents enumeration!
    assert response.status_code == 404
```

---

## 9. Practice Exercises

### Exercise 1: Add Tenant Filter

Add tenant filtering to `/invoices`:

```python
@router.get("/invoices")
def list_invoices(
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Invoice)
        .where(Invoice.tenant_id == current.tenant_id)
    ).all()
```

### Exercise 2: Test Cross-Tenant Access

Write a test that proves tenant isolation:

```python
@pytest.mark.asyncio
async def test_prevent_cross_tenant_update(user_a, wo_b):
    """User A cannot update User B's work order."""
    
    client = create_client(user_a)  # Login as user A
    
    response = await client.patch(
        f"/api/v1/work-orders/{wo_b.id}",  # User B's work order
        json={"title": "Hacked!"}
    )
    
    assert response.status_code == 404  # Not found!
```

### Exercise 3: Filter by Client for Client Admins

```python
@router.get("/clients")
def list_clients(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Client).where(Client.tenant_id == current.tenant_id)
    
    if current.role == UserRole.client_admin and current.client_id:
        # Only see their own client
        query = query.where(Client.id == current.client_id)
    
    return db.scalars(query).all()
```

---

## 10. Key Takeaways

| Concept | Purpose | Code Pattern |
|---------|---------|--------------|
| `tenant_id` | Data partition | Every table |
| Filter by tenant | Always filter | `.where(tenant_id == ...)` |
| Return 404 | Don't reveal | `status.HTTP_404_NOT_FOUND` |
| Role filtering | Within tenant | `.where(client_id == ...)` |
| UserSiteScope | Site-level access | Filter by scoped sites |

---

## 11. Next Steps

1. **PostgreSQL RLS**: Database-level row security
2. **Audit logs**: Track who did what
3. **Tenant settings**: Per-tenant customization

---

## References

- [FMS Models](backend/app/models.py)
- [FMS Isolation Tests](backend/tests/test_isolation.py)
- [FMS Work Orders](backend/app/api/routes/work_orders.py)
- [ARCHITECTURE.md](../ARCHITECTURE.md)