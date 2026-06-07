# Testing — Knowledge Hub

> Learn testing by studying the FMS codebase.

---

## 1. Test Setup

### pytest Configuration

```python
# backend/pyproject.toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
```

### Test Fixtures

```python
# backend/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db():
    """In-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    
    # Create tables
    from app.models import Base
    Base.metadata.create_all(engine)
    
    session = Session()
    yield session
    session.close()
```

---

## 2. Test Fixtures

### Database Fixtures

```python
# backend/conftest.py
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    tenant = Tenant(name="Test Tenant")
    db.add(tenant)
    db.commit()
    return tenant
```

### Auth Fixtures

```python
@pytest.fixture
def super_admin(db, tenant):
    """Create a super admin user."""
    user = User(
        tenant_id=tenant.id,
        email="super@example.com",
        full_name="Super Admin",
        role=UserRole.super_admin,
        password_hash=hash_password("supersecret"),
    )
    db.add(user)
    db.commit()
    return user

def create_test_token(user: User) -> str:
    """Create JWT for testing."""
    return create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
    })
```

---

## 3. Writing Tests

### Testing Endpoints

```python
# backend/tests/test_work_orders.py
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_list_work_orders(super_admin):
    """Test listing work orders."""
    client = AsyncClient(
        transport=ASGITransport(app=app),
        headers={"Authorization": f"Bearer {create_test_token(super_admin)}"}
    )
    
    response = await client.get("/api/v1/work-orders")
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
```

### Testing CRUD

```python
@pytest.mark.asyncio
async def test_create_work_order(client_admin):
    """Test creating a work order."""
    response = await client_admin.post(
        "/api/v1/work-orders",
        json={
            "title": "Test WO",
            "client_id": str(client_id),
            "site_id": str(site_id),
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == "Test WO"
```

---

## 4. RBAC Tests

### Test Permissions

```python
# backend/tests/test_rbac.py

@pytest.mark.asyncio
async def test_technician_cannot_create_wo(technician):
    """Technicians should not be able to create work orders."""
    client = create_client(technician)
    
    response = await client.post(
        "/api/v1/work-orders",
        json={...}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_create_wo(company_admin):
    """Company admins should be able to create work orders."""
    client = create_client(company_admin)
    
    response = await client.post(
        "/api/v1/work-orders",
        json={...}
    )
    
    assert response.status_code == 200
```

### Test Role Filtering

```python
@pytest.mark.asyncio
async def test_client_admin_sees_only_own_wos(client_admin):
    """Client admin should only see their client's work orders."""
    client = create_client(client_admin)
    
    response = await client.get("/api/v1/work-orders")
    data = response.json()
    
    for wo in data["data"]:
        assert wo["client_id"] == str(client_admin.client_id)
```

---

## 5. Isolation Tests

### Test Cross-Tenant Access

```python
# backend/tests/test_isolation.py

@pytest.mark.asyncio
async def test_other_tenant_wo_not_visible(user_a, user_b_wo):
    """User A should not see User B's work order."""
    client_a = create_client(user_a)
    
    response = client_a.get(f"/api/v1/work-orders/{user_b_wo.id}")
    
    # Returns 404, not 403 (prevents enumeration)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_random_uuid_returns_404(user_a):
    """Random UUID should return 404."""
    client_a = create_client(user_a)
    
    response = client_a.get(f"/api/v1/work-orders/{uuid.uuid4()}")
    assert response.status_code == 404
```

---

## 6. Running Tests

### CLI Commands

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_rbac.py -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html

# Quick run
pytest backend/tests/ -q
```

---

## 7. Test Categories

| Category | Location | Tests |
|----------|----------|-------|
| RBAC | `test_rbac.py` | 46+ |
| Tenant Isolation | `test_isolation.py` | 24 |
| Asset Lifecycle | `test_asset_lifecycle.py` | 4 |
| Auth | `test_auth_login.py` | 3 |
| Tenancy | `test_tenancy.py` | 2 |

---

## 8. Best Practices

### 1. Use Fixtures

```python
@pytest.fixture
def user(db, tenant):
    """Reusable user fixture."""
    user = User(...)
    db.add(user)
    db.commit()
    return user
```

### 2. Test Both Success & Failure

```python
async def test_create_success(admin):
    """Success case."""
    response = await admin.post("/work-orders", json={...})
    assert response.status_code == 200

async def test_create_failure(technician):
    """Failure case (no permission)."""
    response = await technician.post("/work-orders", json={...})
    assert response.status_code == 403
```

### 3. Clean Up

```python
@pytest.fixture(autouse=True)
def cleanup(db):
    """Clean up after each test."""
    yield
    db.rollback()  # Reset database state
```

---

## 9. Practice Exercises

### Exercise 1: Write a Simple Test

```python
@pytest.mark.asyncio
async def test_list_users(super_admin):
    """Test listing users."""
    client = create_client(super_admin)
    
    response = await client.get("/api/v1/users")
    
    assert response.status_code == 200
    assert "data" in response.json()
```

### Exercise 2: Test Isolation

```python
@pytest.mark.asyncio
async def test_prevent_cross_tenant_update(user_a, work_order_b):
    """User A cannot update user B's work order."""
    client_a = create_client(user_a)
    
    response = await client_a.patch(
        f"/api/v1/work-orders/{work_order_b.id}",
        json={"title": "Hacked!"}
    )
    
    assert response.status_code == 404
```

---

## References

- [pytest Docs](https://docs.pytest.org/)
- [FMS Tests](backend/tests/)
- [FMS Test Results](README.md)