# Role-Based Access Control (RBAC) — Knowledge Hub

> Learn RBAC by studying the FMS codebase.

---

## 1. RBAC in FMS

### The 6 Roles

| Role | Code | Permission Level |
|------|------|----------------|
| Super Admin | `super_admin` | Full system access |
| Company Admin | `company_admin` | Tenant-wide |
| Client Admin | `client_admin` | Single client |
| Site Manager | `site_manager` | Assigned sites |
| Technician | `technician` | Assigned WOs |
| Manager | `manager` | Read + approve |

### Defining Roles

```python
# backend/app/models/users.py (UserRole enum)
import enum

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    company_admin = "company_admin"
    client_admin = "client_admin"
    site_manager = "site_manager"
    technician = "technician"
    manager = "manager"
```

---

## 2. Role-Based Dependencies

### Creating Role Requirements

```python
# backend/app/api/deps.py
from functools import wraps
from app.models import UserRole

def require_roles(*allowed_roles: UserRole):
    """Dependency that checks if user has required role."""
    def role_checker(current: User = Depends(get_current_user)):
        if current.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current
    return role_checker
```

### Using in Routes

```python
# Only admins can create work orders
@router.post("/work-orders")
def create_work_order(
    ...,
    _: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.super_admin,
                UserRole.company_admin,
                UserRole.client_admin,
                UserRole.site_manager,
            )
        )
    ],
):
    ...
```

---

## 3. Role-Based Filtering

### Filter Data by Role

```python
@router.get("/work-orders")
def list_work_orders(
    current: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    q = select(WorkOrder).where(WorkOrder.tenant_id == current.tenant_id)
    
    # Role-based filtering
    if current.role == UserRole.technician:
        # Technicians see only their assigned WOs
        q = q.where(WorkOrder.assignee_user_id == current.id)
    
    elif current.role == UserRole.client_admin and current.client_id:
        # Client admins see only their client's WOs
        q = q.where(WorkOrder.client_id == current.client_id)
    
    elif current.role == UserRole.site_manager:
        # Site managers see only their scoped sites
        scoped = db.scalars(
            select(UserSiteScope.site_id)
            .where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped:
            q = q.where(WorkOrder.site_id.in_(scoped))
        else:
            q = q.where(false())  # Empty result
    
    return db.scalars(q.order_by(WorkOrder.opened_at.desc())).all()
```

---

## 4. Entity-Level Access Control

### Checking Access to Specific Resource

```python
def _access_work_order(
    db: Session,
    current: User,
    wo_id: UUID,
) -> WorkOrder:
    """Check if user can access a specific work order."""
    wo = db.get(WorkOrder, wo_id)
    
    # Tenant check
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    
    # Role-specific access
    if current.role == UserRole.technician:
        if wo.assignee_user_id != current.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    elif current.role == UserRole.client_admin and current.client_id:
        if wo.client_id != current.client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    elif current.role == UserRole.site_manager:
        scoped = db.scalars(
            select(UserSiteScope.site_id)
            .where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped and wo.site_id not in scoped:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
    
    return wo
```

---

## 5. RBAC Matrix

### Who Can Do What

| Endpoint | super_admin | company_admin | client_admin | site_manager | technician | manager |
|----------|-----------|-------------|-------------|-------------|------------|----------|
| GET /users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| POST /users | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| GET /work-orders | ✅ All | ✅ All | ✅ Client | ✅ Site | ✅ Assigned | ✅ All |
| POST /work-orders | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| GET /invoices | ✅ All | ✅ All | ✅ Client | ✅ Read | ✅ Read | ✅ All |

---

## 6. Site Scoping

### UserSiteScope Model

```python
# backend/app/models/users.py (UserRole enum)
class UserSiteScope(Base):
    """Sites a user can access (for site managers)."""
    __tablename__ = "user_site_scopes"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id"), primary_key=True
    )
    
    user: Mapped["User"] = relationship(back_populates="site_scopes")
```

### Assign Sites to User

```python
@router.post("/users/{user_id}/scopes")
def assign_site_scopes(
    user_id: UUID,
    body: SiteScopesUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Assign sites to a user."""
    user = db.get(User, user_id)
    
    # Remove old scopes
    db.execute(
        delete(UserSiteScope).where(UserSiteScope.user_id == user_id)
    )
    
    # Add new scopes
    for site_id in body.site_ids:
        db.add(UserSiteScope(user_id=user_id, site_id=site_id))
    
    db.commit()
    return {"message": "Scopes updated"}
```

---

## 7. Security Principles

### 1. Deny by Default

```python
# Default: Deny access unless explicitly allowed
@router.get("/work-orders/{id}")
def get_work_order(...):
    # Explicit check required
    wo = _access_work_order(db, current, work_order_id)
    return wo
```

### 2. Return 404, Not 403

```python
# Prevents enumeration attacks
if not resource or resource.tenant_id != current.tenant_id:
    raise HTTPException(status.HTTP_404_NOT_FOUND)  # Not 403!
```

### 3. Log Unauthorized Attempts

```python
from app.services.audit import write_audit

@router.patch("/work-orders/{id}")
def patch_work_order(...):
    wo = _access_work_order(db, current, work_order_id)
    
    # Log the access attempt
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="attempt_update",
        entity_type="work_order",
        entity_id=str(wo.id),
    )
```

---

## 8. Practice Exercises

### Exercise 1: Add Role Check to Endpoint

Add protection to `/assets` endpoint:

```python
@router.post("/assets")
def create_asset(
    body: AssetCreate,
    db: Session = Depends(get_db),
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        User,
        Depends(
            require_roles(
                UserRole.super_admin,
                UserRole.company_admin,
                UserRole.site_manager,
            )
        )
    ],
):
    asset = Asset(
        tenant_id=current.tenant_id,
        site_id=body.site_id,
        name=body.name,
        ...
    )
    db.add(asset)
    db.commit()
    return asset
```

### Exercise 2: Test Role Filtering

```python
def test_client_admin_sees_only_own(client_admin):
    """Client admin should only see their client's WOs."""
    response = client_admin.get("/api/v1/work-orders")
    assert response.status_code == 200
    
    wos = response.json()["data"]
    for wo in wos:
        assert wo["client_id"] == client_admin.client_id
```

---

## References

See [FMS RBAC (canonical)](../architecture/RBAC.md). Historical matrix: [archive/phase2/RBAC_Matrix.md](../archive/phase2/RBAC_Matrix.md).
- [FMS RBAC Tests](backend/tests/test_rbac.py)
- [FMS Isolation Tests](backend/tests/test_isolation.py)