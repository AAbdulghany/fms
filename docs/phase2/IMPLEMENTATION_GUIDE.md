# Phase 2 Implementation Guide

**Date:** April 18, 2026  
**Target Audience:** Developers extending or maintaining the FMS  
**Version:** 2.0

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Development Workflow](#development-workflow)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Testing Strategy](#testing-strategy)
6. [Adding New Features](#adding-new-features)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Project Structure

```
FMS/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py           # Dependency injection (auth, db)
│   │   │   └── routes/           # API route modules
│   │   │       ├── assets.py
│   │   │       ├── dashboard.py  # Phase 2
│   │   │       ├── labor.py      # Phase 2
│   │   │       ├── locations.py  # Phase 2
│   │   │       └── work_orders.py
│   │   ├── services/             # Business logic
│   │   │   ├── asset_lifecycle.py
│   │   │   └── audit.py
│   │   ├── database.py           # DB connection
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── schemas.py            # Pydantic schemas
│   │   └── main.py               # FastAPI app
│   ├── migrations/               # Alembic migrations
│   │   └── versions/
│   ├── tests/                    # Pytest test suite
│   │   ├── conftest.py           # Test fixtures
│   │   ├── test_rbac.py
│   │   ├── test_isolation.py
│   │   └── test_asset_lifecycle.py
│   └── alembic.ini               # Alembic config
├── src/                          # React frontend
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── FilterBar.tsx         # Phase 2
│   │   ├── LocationTree.tsx      # Phase 2
│   │   └── AssetLifecycleTimeline.tsx # Phase 2
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── LocationsPage.tsx     # Phase 2
│   │   ├── LaborPage.tsx         # Phase 2
│   │   └── WorkOrdersPage.tsx
│   ├── lib/
│   │   ├── api.ts                # API client
│   │   └── types.ts              # TypeScript types
│   ├── i18n/
│   │   └── index.ts              # Internationalization
│   └── App.tsx                   # Main app + routing
├── docs/
│   ├── phase2/                   # Phase 2 documentation
│   │   ├── PHASE2_COMPLETE.md
│   │   ├── API_REFERENCE.md
│   │   └── IMPLEMENTATION_GUIDE.md (this file)
│   ├── USER_GUIDE.md
│   └── claude_phase2_implementation.md
└── pyproject.toml                # Python dependencies
```

---

## Development Workflow

### Initial Setup

```powershell
# 1. Clone repository
git clone <repo-url>
cd FMS

# 2. Install backend dependencies
cd backend
uv sync

# 3. Install frontend dependencies
cd ..
npm install

# 4. Set up environment variables
# Backend: Create backend/.env
DATABASE_URL=postgresql://user:pass@localhost/fms_dev
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Frontend: Create .env.local
VITE_API_BASE_URL=http://localhost:8000

# 5. Apply migrations
uv run alembic -c backend/alembic.ini upgrade head

# 6. Seed database (optional)
$env:PYTHONPATH="backend"
uv run python -m app.seed_super
```

### Daily Development

```powershell
# Terminal 1: Backend
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
npm run dev

# Terminal 3: Tests (watch mode)
uv run pytest-watch backend/tests/

# Terminal 4: Type checking
npm run type-check -- --watch
```

### Git Workflow

```powershell
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and test
uv run pytest backend/tests/
npm run build

# 3. Commit with conventional commits
git add .
git commit -m "feat(labor): add overtime tracking"

# 4. Push and create PR
git push origin feature/my-feature
```

**Commit Convention:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `test:` — Test changes
- `refactor:` — Code refactoring
- `chore:` — Tooling, dependencies

---

## Backend Architecture

### FastAPI Application Structure

**`backend/app/main.py`** — Application entry point

```python
from fastapi import FastAPI
from app.api.routes import (
    work_orders, assets, locations, labor, dashboard
)

app = FastAPI(title="FMS API")

# Register routers
app.include_router(work_orders.router)
app.include_router(assets.router)
app.include_router(locations.router)
app.include_router(labor.router)
app.include_router(dashboard.router)
```

### Models (`backend/app/models.py`)

**SQLAlchemy ORM models** — Database schema

```python
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"), nullable=True)
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    metadata_json = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
```

**Key Patterns:**
- All models have `tenant_id` for isolation
- Use `UUID` for primary keys
- Timestamps: `created_at`, `updated_at` (UTC)
- JSONB for flexible metadata

### Schemas (`backend/app/schemas.py`)

**Pydantic models** — Request/response validation

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class LocationCreate(BaseModel):
    site_id: UUID
    parent_id: UUID | None = None
    name: str = Field(..., max_length=255)
    location_type: str | None = None
    sort_order: int = 0
    metadata_json: dict = {}

class LocationOut(LocationCreate):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

**Key Patterns:**
- `*Create` schemas for POST requests
- `*Update` schemas for PATCH requests (all fields optional)
- `*Out` schemas for responses (includes id, timestamps)
- Use `Field(...)` for required fields with validation

### Routes (`backend/app/api/routes/`)

**Endpoint implementation** — HTTP handlers

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Annotated
from uuid import UUID

router = APIRouter(prefix="/locations", tags=["locations"])

@router.get("", response_model=list[LocationOut])
def list_locations(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, Depends(require_roles(UserRole.super_admin, ...))],
    site_id: UUID = Query(..., description="Site to list locations for"),
) -> list[Location]:
    # Validate site access
    _ensure_site(db, current, site_id)
    
    # Query with tenant filter
    q = select(Location).where(
        Location.tenant_id == current.tenant_id,
        Location.site_id == site_id
    )
    return list(db.scalars(q.order_by(Location.sort_order)).all())
```

**Key Patterns:**
- Use `Annotated` for dependency injection
- Always filter by `tenant_id` (security!)
- Use helper functions for common validations
- Return ORM models (FastAPI converts via schema)

### Dependencies (`backend/app/api/deps.py`)

**Reusable dependencies** — Auth, DB, RBAC

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

# Database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Current user from JWT
def get_current_user(
    token: str = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> User:
    # Decode JWT, fetch user
    # Raise 401 if invalid
    pass

# Role-based access control
def require_roles(*allowed_roles: UserRole):
    def _check(current: User = Depends(get_current_user)) -> User:
        if current.role not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        return current
    return _check
```

### Services (`backend/app/services/`)

**Business logic** — Separate from routes

```python
# backend/app/services/asset_lifecycle.py

def check_and_update_lifecycle(
    db: Session,
    asset: Asset,
    tenant_id: UUID
) -> tuple[AssetLifecycleStatus, bool]:
    """
    Check asset lifecycle and update status.
    Returns (new_status, replacement_wo_created).
    """
    old_status = asset.lifecycle_status
    
    # Check repair count
    if asset.current_repair_count >= asset.max_repair_count:
        asset.lifecycle_status = AssetLifecycleStatus.end_of_life
    
    # Check age
    if asset.installed_on:
        age = (datetime.now().date() - asset.installed_on).days / 365.25
        if age >= asset.max_age_years:
            asset.lifecycle_status = AssetLifecycleStatus.end_of_life
    
    # Auto-create replacement WO
    if old_status != AssetLifecycleStatus.end_of_life and \
       asset.lifecycle_status == AssetLifecycleStatus.end_of_life:
        wo = WorkOrder(
            tenant_id=tenant_id,
            site_id=asset.site_id,
            asset_id=asset.id,
            title=f"Replace Asset: {asset.name}",
            urgency=WorkOrderUrgency.high,
            status=WorkOrderStatus.open
        )
        db.add(wo)
        return (asset.lifecycle_status, True)
    
    return (asset.lifecycle_status, False)
```

**Key Patterns:**
- Pure functions where possible
- Take `db` session as parameter
- Return tuple for multiple values
- Log important actions

### Migrations (`backend/migrations/versions/`)

**Alembic migrations** — Database schema changes

```powershell
# Create new migration
uv run alembic -c backend/alembic.ini revision --autogenerate -m "Add location_id to assets"

# Review generated migration file
# Edit if needed (autogenerate isn't perfect)

# Apply migration
uv run alembic -c backend/alembic.ini upgrade head

# Rollback one migration
uv run alembic -c backend/alembic.ini downgrade -1
```

**Migration file structure:**

```python
def upgrade() -> None:
    op.add_column('assets', sa.Column('location_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'assets', 'locations', ['location_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint(None, 'assets', type_='foreignkey')
    op.drop_column('assets', 'location_id')
```

---

## Frontend Architecture

### React + TypeScript Structure

**`src/App.tsx`** — Main application

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import LocationsPage from './pages/LocationsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="locations" element={<LocationsPage />} />
          {/* ... */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
```

### Layout System (`src/components/Layout.tsx`)

**Persistent layout** — Sidebar + main content

```tsx
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

export default function Layout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
```

### Sidebar Navigation (`src/components/Sidebar.tsx`)

**Role-aware menu** — Different items per role

```tsx
import { Link } from 'react-router-dom';
import { useAuth } from './AuthContext';

export default function Sidebar() {
  const { user } = useAuth();
  
  const menuItems = useMemo(() => {
    const items = [
      { path: '/', label: t('dashboard'), icon: '📊' }
    ];
    
    if (['super_admin', 'company_admin'].includes(user?.role)) {
      items.push({ path: '/companies', label: t('companies'), icon: '🏢' });
      items.push({ path: '/employees', label: t('employees'), icon: '👥' });
    }
    
    if (['manager', 'technician'].includes(user?.role)) {
      items.push({ path: '/labor', label: t('labor'), icon: '⏱️' });
    }
    
    return items;
  }, [user]);
  
  return (
    <aside className="w-64 bg-gray-800 text-white">
      <nav>
        {menuItems.map(item => (
          <Link key={item.path} to={item.path}>
            {item.icon} {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

### API Client (`src/lib/api.ts`)

**Centralized API calls** — Fetch wrapper

```tsx
const API_BASE = import.meta.env.VITE_API_BASE_URL;

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = localStorage.getItem('token');
  
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...options?.headers,
    },
  });
  
  if (!res.ok) {
    if (res.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail);
  }
  
  return res.json();
}

// Typed API calls
export const api = {
  locations: {
    list: (siteId: string) =>
      fetchAPI<Location[]>(`/locations?site_id=${siteId}`),
    tree: (siteId: string) =>
      fetchAPI<LocationTreeNode[]>(`/locations/tree?site_id=${siteId}`),
    create: (data: LocationCreate) =>
      fetchAPI<Location>('/locations', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
};
```

### TypeScript Types (`src/lib/types.ts`)

**Shared type definitions**

```tsx
export interface Location {
  id: string;
  tenant_id: string;
  site_id: string;
  parent_id: string | null;
  name: string;
  location_type: string | null;
  sort_order: number;
  metadata_json: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface LocationTreeNode {
  id: string;
  site_id: string;
  parent_id: string | null;
  name: string;
  location_type: string | null;
  sort_order: number;
  children: LocationTreeNode[];
}

export enum UserRole {
  super_admin = 'super_admin',
  company_admin = 'company_admin',
  client_admin = 'client_admin',
  site_manager = 'site_manager',
  manager = 'manager',
  technician = 'technician',
}
```

### Internationalization (`src/i18n/index.ts`)

**Multi-language support** — Arabic + English

```tsx
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: {
        dashboard: 'Dashboard',
        locations: 'Locations',
        no_locations: 'No locations found',
        // ...
      },
    },
    ar: {
      translation: {
        dashboard: 'لوحة التحكم',
        locations: 'المواقع',
        no_locations: 'لم يتم العثور على مواقع',
        // ...
      },
    },
  },
  lng: 'en',
  fallbackLng: 'en',
});

export default i18n;
```

**Usage in components:**

```tsx
import { useTranslation } from 'react-i18next';

export default function MyComponent() {
  const { t, i18n } = useTranslation();
  
  return (
    <div dir={i18n.language === 'ar' ? 'rtl' : 'ltr'}>
      <h1>{t('dashboard')}</h1>
      <button onClick={() => i18n.changeLanguage('ar')}>
        العربية
      </button>
    </div>
  );
}
```

---

## Testing Strategy

### Backend Tests (`backend/tests/`)

**pytest fixtures** — `conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from app.database import Base, get_db
from app.models import User, Tenant, UserRole

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine("postgresql://user:pass@localhost/test_db")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Fresh DB session per test"""
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def super_admin_user(db_session):
    """Create super admin user"""
    tenant = Tenant(id=uuid4(), name="Test Tenant")
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="admin@test.com",
        role=UserRole.super_admin,
        is_active=True
    )
    db_session.add_all([tenant, user])
    db_session.commit()
    return user
```

**RBAC tests** — `test_rbac.py`

```python
def test_super_admin_can_create_location(
    client, super_admin_token, site
):
    """Super admin can create locations"""
    res = client.post(
        "/locations",
        json={
            "site_id": str(site.id),
            "name": "Building A",
            "location_type": "building",
        },
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Building A"

def test_technician_cannot_list_locations(
    client, technician_token, site
):
    """Technician cannot access locations"""
    res = client.get(
        f"/locations?site_id={site.id}",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert res.status_code == 403
```

**Tenant isolation tests** — `test_isolation.py`

```python
def test_cannot_access_other_tenant_location(
    client, admin_token_tenant1, location_tenant2
):
    """Users cannot access other tenants' locations"""
    res = client.get(
        f"/locations/{location_tenant2.id}",
        headers={"Authorization": f"Bearer {admin_token_tenant1}"}
    )
    assert res.status_code == 404  # Not found (not 403)
```

### Frontend Tests (Future)

**Vitest + React Testing Library**

```powershell
# Install dependencies
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Run tests
npm run test
```

**Example component test:**

```tsx
import { render, screen } from '@testing-library/react';
import LocationTree from './LocationTree';

test('renders location tree', () => {
  const nodes = [
    { id: '1', name: 'Building A', children: [] }
  ];
  
  render(<LocationTree nodes={nodes} />);
  
  expect(screen.getByText('Building A')).toBeInTheDocument();
});
```

---

## Adding New Features

### Step-by-Step Guide

#### 1. Backend: Add Model

Edit `backend/app/models.py`:

```python
class MyNewModel(Base):
    __tablename__ = "my_new_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### 2. Backend: Create Migration

```powershell
uv run alembic -c backend/alembic.ini revision --autogenerate -m "Add MyNewModel"
uv run alembic -c backend/alembic.ini upgrade head
```

#### 3. Backend: Add Schemas

Edit `backend/app/schemas.py`:

```python
class MyNewModelCreate(BaseModel):
    name: str = Field(..., max_length=255)

class MyNewModelOut(MyNewModelCreate):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

#### 4. Backend: Add Routes

Create `backend/app/api/routes/my_new_models.py`:

```python
router = APIRouter(prefix="/my-new-models", tags=["my_new_models"])

@router.get("", response_model=list[MyNewModelOut])
def list_my_new_models(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[MyNewModel]:
    q = select(MyNewModel).where(MyNewModel.tenant_id == current.tenant_id)
    return list(db.scalars(q).all())
```

Register in `backend/app/main.py`:

```python
from app.api.routes import my_new_models
app.include_router(my_new_models.router)
```

#### 5. Backend: Add Tests

Create `backend/tests/test_my_new_models.py`:

```python
def test_super_admin_can_list(client, super_admin_token):
    res = client.get(
        "/my-new-models",
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert res.status_code == 200
```

#### 6. Frontend: Add Types

Edit `src/lib/types.ts`:

```tsx
export interface MyNewModel {
  id: string;
  tenant_id: string;
  name: string;
  created_at: string;
  updated_at: string;
}
```

#### 7. Frontend: Add API Calls

Edit `src/lib/api.ts`:

```tsx
export const api = {
  // ... existing
  myNewModels: {
    list: () => fetchAPI<MyNewModel[]>('/my-new-models'),
    create: (data: { name: string }) =>
      fetchAPI<MyNewModel>('/my-new-models', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
};
```

#### 8. Frontend: Create Page

Create `src/pages/MyNewModelsPage.tsx`:

```tsx
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../lib/api';
import type { MyNewModel } from '../lib/types';

export default function MyNewModelsPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<MyNewModel[]>([]);
  
  useEffect(() => {
    api.myNewModels.list().then(setItems);
  }, []);
  
  return (
    <div>
      <h1>{t('my_new_models')}</h1>
      {items.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}
```

#### 9. Frontend: Add Route

Edit `src/App.tsx`:

```tsx
import MyNewModelsPage from './pages/MyNewModelsPage';

// In Routes:
<Route path="my-new-models" element={<MyNewModelsPage />} />
```

#### 10. Frontend: Add i18n Keys

Edit `src/i18n/index.ts`:

```tsx
en: {
  translation: {
    my_new_models: 'My New Models',
    // ...
  },
},
ar: {
  translation: {
    my_new_models: 'نماذجي الجديدة',
    // ...
  },
},
```

#### 11. Test End-to-End

```powershell
# Backend tests
uv run pytest backend/tests/test_my_new_models.py

# Manual UI test
npm run dev
# Navigate to /my-new-models
```

---

## Common Patterns

### RBAC Enforcement

**Always use role-based dependencies:**

```python
# Allow multiple roles
_admin_or_manager = Depends(
    require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.manager)
)

@router.get("/sensitive-data")
def get_sensitive_data(
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin_or_manager],
) -> dict:
    # Only super_admin, company_admin, manager can access
    pass
```

### Tenant Isolation

**Always filter by tenant_id:**

```python
# ✅ Good
q = select(WorkOrder).where(WorkOrder.tenant_id == current.tenant_id)

# ❌ Bad (security issue!)
q = select(WorkOrder)  # Returns all tenants' data
```

### Role-Specific Filtering

**Technicians see only assigned:**

```python
q = select(WorkOrder).where(WorkOrder.tenant_id == current.tenant_id)

if current.role == UserRole.technician:
    q = q.where(WorkOrder.assignee_user_id == current.id)
```

### Error Handling

**Use appropriate HTTP status codes:**

```python
# 400 Bad Request — Invalid input
raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_INPUT")

# 403 Forbidden — Insufficient permissions
raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

# 404 Not Found — Resource doesn't exist OR wrong tenant
raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")

# 409 Conflict — Duplicate, constraint violation
raise HTTPException(status.HTTP_409_CONFLICT, detail="ALREADY_EXISTS")
```

### Audit Logging

**Log important actions:**

```python
from app.services.audit import write_audit

write_audit(
    db,
    tenant_id=current.tenant_id,
    actor=current,
    action="create",
    entity_type="location",
    entity_id=str(location.id),
    after={"name": location.name, "site_id": str(location.site_id)},
)
```

---

## Troubleshooting

### Backend Issues

**Problem:** Alembic can't import app modules  
**Solution:** Set `PYTHONPATH=backend` or `$env:PYTHONPATH="backend"`

**Problem:** Tests fail with "database doesn't exist"  
**Solution:** Create test database: `createdb test_db`

**Problem:** 401 Unauthorized on all requests  
**Solution:** Check JWT token in `Authorization: Bearer <token>` header

**Problem:** 404 on cross-tenant access  
**Solution:** Verify `tenant_id` filtering in query

### Frontend Issues

**Problem:** TypeScript errors on build  
**Solution:** Run `npm run type-check` for details

**Problem:** API calls return 401  
**Solution:** Check token in localStorage: `localStorage.getItem('token')`

**Problem:** RTL layout broken  
**Solution:** Ensure `dir={i18n.language === 'ar' ? 'rtl' : 'ltr'}` on root element

**Problem:** Missing translations  
**Solution:** Add keys to `src/i18n/index.ts` for both `en` and `ar`

### Database Issues

**Problem:** Migration fails with constraint error  
**Solution:** Check existing data, add data migration if needed

**Problem:** Slow queries  
**Solution:** Add indexes on frequently queried columns (tenant_id, foreign keys)

---

## Best Practices Checklist

### Backend
- [ ] All models have `tenant_id` column
- [ ] All queries filter by `tenant_id`
- [ ] RBAC enforced with `require_roles` dependency
- [ ] Error messages use detail codes (not full sentences)
- [ ] Audit logging for create/update/delete
- [ ] Tests cover happy path + error cases
- [ ] Migration has both `upgrade()` and `downgrade()`

### Frontend
- [ ] All text uses `t()` function (i18n)
- [ ] RTL support tested (Arabic language)
- [ ] API errors handled gracefully
- [ ] Loading states shown
- [ ] 401 errors redirect to login
- [ ] TypeScript strict mode (no `any` types)
- [ ] Responsive design (mobile + desktop)

### Security
- [ ] JWT token stored securely
- [ ] No sensitive data in logs
- [ ] HTTPS in production
- [ ] SQL injection prevented (ORM)
- [ ] XSS prevented (React escaping)
- [ ] CORS configured correctly

---

## Next Steps

**After Phase 2:**
1. Set up CI/CD pipeline (GitHub Actions)
2. Configure production environment
3. Set up error tracking (Sentry)
4. Plan Phase 3 features (maps, mobile, reporting)
5. Conduct user acceptance testing

**Resources:**
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Router Docs](https://reactrouter.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

**Last Updated:** April 18, 2026  
**Maintained By:** FMS Development Team
