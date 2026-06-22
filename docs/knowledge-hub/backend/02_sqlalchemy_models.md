# SQLAlchemy Models — Learning by Understanding Data

> **Goal**: Understand how FMS stores data using SQLAlchemy ORM. Move beyond "just SQL" to "object-oriented database".

---

## Why SQLAlchemy?

### The Problem: Raw SQL vs ORM

```
┌─────────────────────────────────────────────────────────────┐
│              Raw SQL (Harder to maintain)                   │
├─────────────────────────────────────────────────────────────┤
│  INSERT INTO users (email, name, role)                     │
│  VALUES ('john@example.com', 'John', 'admin');               │
│                                                             │
│  SELECT * FROM users WHERE id = 'uuid-123';             │
│                                                             │
│  ❌ String concatenation is error-prone               │
│  ❌ No type checking                                │
│  ❌ Hard to change schema                         │
│  ❌ Database-specific syntax                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│            SQLAlchemy ORM (Better for Python)             │
├─────────────────────────────────────────────────────────────┤
│  user = User(email='john@example.com', name='John')     │
│  db.add(user)                                       │
│                                                     │
│  user = db.get(User, 'uuid-123')                    │
│                                                     │
│  ✅ Python types                                   │
│  ✅ Auto validation                                │
│  ✅ Easy schema changes                            │
│  ✅ Database agnostic                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Setting Up SQLAlchemy

### The Database Connection

Look at `backend/app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

# This is like the "connection string" to your restaurant
DATABASE_URL = "postgresql+psycopg2://fms:fms@localhost:5432/fms"

# The engine - like establishing the connection
engine = create_engine(DATABASE_URL)

# Session factory - like opening a connection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class - all models inherit from this
Base = declarative_base()

def get_db():
    """Get database session - used as dependency."""
    db = SessionLocal()
    try:
        yield db  # Give to endpoint
    finally:
        db.close()  # Always clean up!
```

---

## 2. Defining Models: The Building Blocks

### What is a Model?

A model is like a **blueprint** for a database table:

```
┌─────────────────────────────────────────────────────────────┐
│                    class User(Base)                          │
│  ┌───────────────────────────────────────────────────┐    │
│  │ __tablename__ = "users"                         │    │
│  ├───────────────────────────────────────────────────┤    │
│  │ id: Mapped[UUID]  →  Column(UUID, PK)          │    │
│  │ email: Mapped[str]→  Column(VARCHAR)            │    │
│  │ name: Mapped[str] →  Column(VARCHAR)            │    │
│  │ role: Mapped[UserRole] → Column(ENUM)          │    │
│  └───────────────────────────────────────────────────┘    │
│                        │                                   │
│                        ▼                                   │
│  ┌───────────────────────────────────────────┐            │
│  │            users table                     │            │
│  │ ┌──────┬──────────────────┬──────────┐  │            │
│  │ │  id  │      email       │  role   │  │            │
│  │ ├──────┼──────────────────┼──────────┤  │            │
│  │ │ UUID │ john@ex.com      │ admin   │  │            │
│  │ └──────┴──────────────────┴──────────┘  │            │
│  └───────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Real Model: The User Model

Look at `backend/app/models/` (domain package; start with `users.py` for `UserRole`):

```python
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

# The base class - all models inherit this
class User(Base):
    __tablename__ = "users"  # Table name in database
    
    # Define columns using type hints + mapped_column
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),  # PostgreSQL UUID type
        primary_key=True,   # This is the PRIMARY KEY
        default=uuid.uuid4  # Auto-generate UUID
    )
    
    email: Mapped[str] = mapped_column(
        String(320),  # VARCHAR(320) - max email length
        nullable=False  # NOT NULL
    )
    
    full_name: Mapped[str] = mapped_column(String(255), default="")
    
    # Enum field - uses Python enum
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),  # Converts enum to string in DB
        nullable=False
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # TIMESTAMP WITH TIME ZONE
        default=lambda: datetime.now(timezone.utc)  # Auto-set current time
    )
```

### Column Types Mapping

```python
# From Python Type → SQLAlchemy → PostgreSQL

str               → String(255)      → VARCHAR(255)
int               → Integer          → INTEGER
bool              → Boolean         → BOOLEAN
datetime         → DateTime        → TIMESTAMP
date              → Date            → DATE
uuid.UUID         → UUID(as_uuid=True)→ UUID
dict (JSON)       → JSONB           → JSONB
list[str]         → ARRAY(String)   → TEXT[]
Decimal          → Numeric(12,2)   → NUMERIC(12,2)
```

---

## 3. Enums: Fixed Choices

### Why Enums?

Enums are like **pre-defined options** for a field:

```
┌─────────────────────────────────────────────────────────────┐
│     class UserRole(str, enum.Enum)                        │
├─────────────────────────────────────────────────────────────┤
│  super_admin     →  "super_admin"                        │
│  company_admin →  "company_admin"                     │
│  client_admin  →  "client_admin"                      │
│  site_manager →  "site_manager"                      │
│  technician   →  "technician"                       │
│  manager       →  "manager"                           │
└─────────────────────────────────────────────────────────────┘
```

### Creating Enums in FMS

```python
import enum

class UserRole(str, enum.Enum):
    """All possible user roles in the system."""
    super_admin = "super_admin"
    company_admin = "company_admin"
    client_admin = "client_admin"
    site_manager = "site_manager"
    technician = "technician"
    manager = "manager"


class WorkOrderStatus(str, enum.Enum):
    """Lifecycle of a work order."""
    created = "created"
    assigned = "assigned"
    in_progress = "in_progress"
    on_hold = "on_hold"
    completed = "completed"
    verified = "verified"
    cancelled = "cancelled"
    closed = "closed"


# Later, using in model:
class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    status: Mapped[WorkOrderStatus] = mapped_column(
        Enum(WorkOrderStatus),
        default=WorkOrderStatus.created
    )
```

---

## 4. Relationships: Tables Talking to Each Other

### What Are Relationships?

Relationships define how **tables connect**:

```
┌─────────────────────────────────────────────────────────────┐
│                    RELATIONSHIPS                          │
├─────────────────────────────────────────────────────────────┤
│  One-to-Many:  1 Parent → Many Children                    │
│  ─────────────────────────────────────────────────────       │
│    Client (1) ──── Many ──── Sites                     │
│                                                     │
│  Many-to-One: Many Children → 1 Parent                  │
│  ─────────────────────────────────────────────────────       │
│    Site (Many) ──── belongs to ──── Client (1)         │
│                                                     │
│  One-to-One:  1 Parent ↔ 1 Child                     ���
���  ─────────────────────────────────────────────────────       │
│    WorkOrder ↔ MaintenanceReport                     │
│                                                     │
│  Self-Referential: Table references itself              │
│  ─────────────────────────────────────────────────────       │
│    Location (parent) ↘                               │
│                         ╰── Location (children)        │
└─────────────────────────────────────────────────────────────┘
```

### One-to-Many: Client → Sites

```python
class Client(Base):
    __tablename__ = "clients"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(255))
    
    # ONE client has MANY sites
    sites: Mapped[list["Site"]] = relationship(
        back_populates="client"  # Matches Site.client
    )


class Site(Base):
    __tablename__ = "sites"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("clients.id")  # Reference to clients table
    )
    name: Mapped[str] = mapped_column(String(255))
    
    # Each site belongs to ONE client
    client: Mapped["Client"] = relationship(
        back_populates="sites"  # Matches Client.sites
    )
```

### One-to-One: WorkOrder → Report

```python
class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    
    # ONE work order has ONE report
    # uselist=False makes it one-to-one
    # cascade="all, delete-orphan" deletes report if WO is deleted
    report: Mapped[Optional["MaintenanceReport"]] = relationship(
        back_populates="work_order",
        uselist=False,
        cascade="all, delete-orphan"
    )


class MaintenanceReport(Base):
    __tablename__ = "maintenance_reports"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    work_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("work_orders.id"),
        unique=True  # This makes it ONE-TO-ONE
    )
    
    work_order: Mapped["WorkOrder"] = relationship(
        back_populates="report"
    )
```

### Self-Referential: Hierarchical Locations

```python
class Location(Base):
    """Locations can have parent locations (Building → Floor → Room)."""
    
    __tablename__ = "locations"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    
    # This location might have a parent
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id")  # References itself!
    )
    
    # Define parent relationship
    parent: Mapped[Optional["Location"]] = relationship(
        remote_side="Location.id",  # "remote" means the other side
        back_populates="children"
    )
    
    # Define children relationship
    children: Mapped[list["Location"]] = relationship(
        "Location",
        back_populates="parent"
    )
```

---

## 5. CRUD Operations

### Create (Insert)

```python
# Create a new user
new_user = User(
    tenant_id=tenant.id,
    email="john@example.com",
    full_name="John Doe",
    role=UserRole.technician,
)
db.add(new_user)
db.commit()
db.refresh(new_user)  # Get the ID and defaults
```

### Read (Select)

```python
# Get by ID
user = db.get(User, user_id)

# Query with filters
technicians = db.scalars(
    select(User)
    .where(User.role == UserRole.technician)
    .where(User.is_active == True)
).all()

# First result or None
user = db.scalars(
    select(User)
    .where(User.email == "john@example.com")
).first()
```

### Update

```python
user = db.get(User, user_id)
user.full_name = "Jane Doe"
user.is_active = False
db.commit()
```

### Delete

```python
user = db.get(User, user_id)
db.delete(user)
db.commit()
```

---

## 6. Querying with Joins

### Loading Related Data

```python
from sqlalchemy.orm import joinedload, selectinload

# Method 1: joinedload (single query with JOIN)
work_orders = db.scalars(
    select(WorkOrder)
    .options(
        joinedload(WorkOrder.client),      # Load client in same query
        joinedload(WorkOrder.assignee_user),  # Load user too
    )
    .where(WorkOrder.tenant_id == tenant_id)
).all()

# Now you can access without N+1 problem!
for wo in work_orders:
    print(wo.client.legal_name)  # Already loaded!
    print(wo.assignee_user.full_name)

# Method 2: selectinload (separate query, faster for collections)
work_orders = db.scalars(
    select(WorkOrder)
    .options(
        selectinload(WorkOrder.comments)  # Loads comments separately
    )
).all()
```

---

## 7. JSONB: Flexible Data Storage

### When to Use JSONB

Use JSONB for **flexible data** that doesn't fit a fixed schema:

```python
class WorkOrder(Base):
    __tablename__ = "work_orders"
    
    # Fixed fields
    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[WorkOrderStatus] = mapped_column(Enum(WorkOrderStatus))
    
    # Flexible JSON data
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict  # Default to empty object
    )
    
    # Array of strings
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list
    )
```

### Writing/Reading JSONB

```python
# Writing
wo.metadata_json = {
    "priority": "high",
    "contact_phone": "+966501234567",
    "preferred_technician": ["tech-1", "tech-2"]
}
wo.tags = ["preventive", "hvac"]

# Reading
priority = wo.metadata_json.get("priority")
all_tags = wo.tags
```

---

## 8. Practice Exercises

### Exercise 1: Create a Comment Model

Add comments to work orders:

```python
class Comment(Base):
    __tablename__ = "comments"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"))
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Add relationship back to WorkOrder!
    # In WorkOrder class:
    # comments: Mapped[list["Comment"]] = relationship(
    #     back_populates="work_order",
    #     cascade="all, delete-orphan"
    # )
```

### Exercise 2: Query with Relationship

```python
def get_work_order_with_details(db: Session, wo_id: UUID):
    """Get a work order with client and site loaded."""
    return db.execute(
        select(WorkOrder)
        .options(
            joinedload(WorkOrder.client),
            joinedload(WorkOrder.site),
            joinedload(WorkOrder.assignee_user),
        )
        .where(WorkOrder.id == wo_id)
    ).scalar_one()
```

### Exercise 3: Add a JSONB Field

Add an `external_ids` field for integration IDs:

```python
class Client(Base):
    # Add this field
    external_ids: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        default=dict
    )

# Usage
client.external_ids = {
    "sap": "SAP-12345",
    "salesforce": "SF-67890"
}
```

---

## 9. Key Takeaways

| Concept | Purpose | FMS Example |
|---------|---------|-------------|
| `Base` | Base class for all models | `database.py` |
| `Mapped[T]` | Type-safe column definition | All models |
| `Enum` | Fixed choices | UserRole, Status |
| `relationship()` | Connect tables | Client.sites |
| `ForeignKey` | Reference another table | site.client_id |
| `JSONB` | Flexible data | metadata_json |
| `joinedload` | Load relations efficiently | queries |

---

## 10. Next Steps

1. **Create migrations**: Learn Alembic for schema changes
2. **Explore more relationships**: Look at all FMS models
3. **Indexes**: Add indexes for query performance

---

## References

- [SQLAlchemy ORM Docs](https://docs.sqlalchemy.org/)
- [FMS Models package](backend/app/models/)
- [FMS Database](backend/app/database.py)