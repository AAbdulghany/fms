# FastAPI Basics — Learning by Doing

> **Goal**: Build a REST API like FMS developers do. Understand FastAPI through real FMS code.

---

## Why FastAPI?

FastAPI is like a **smart waiter** in a restaurant:

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI                                │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐                  │
│  │ Take    │───>│ Cook    │───>│ Serve   │                  │
│  │ Order   │    │ (Logic) │    │ Response│                  │
│  └─────────┘    └─────────┘    └─────────┘                  │
│      │                                      │               │
│      └────────────── HTTP Request ───────────┘               │
│                                                             │
│  - Fast (async/await built-in)                               │
│  - Validates automatically (Pydantic)                      │
│  - Documents auto-generated (Swagger)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Your First FastAPI App

### The Main App (How FMS Sets It Up)

Look at `backend/app/main.py`:

```python
# This is the entry point - the restaurant building
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Create the app with a name
app = FastAPI(title="NexTask FMS API")

# 2. Add CORS (Cross-Origin Resource Sharing)
# This allows frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include routers (different "sections" of the restaurant)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(work_orders.router, prefix="/api/v1")
```

### Try It Yourself

```python
# Save as first_app.py
from fastapi import FastAPI

app = FastAPI(title="My First API")

@app.get("/")
def root():
    return {"message": "Hello, World!"}

# Run: uvicorn first_app:app --reload
# Open: http://localhost:8000/docs
```

---

## 2. Creating API Endpoints

### What is an Endpoint?

An endpoint is like a **specific table** in the restaurant - it has a specific purpose:

```
┌─────────────────────────────────────────────────────────────┐
│  HTTP Method    │  Purpose              │  SQL Equivalent    │
├─────────────────────────────────────────────────────────────┤
│  GET           │  Read/list data       │  SELECT            │
│  POST          │  Create new data    │  INSERT            │
│  PATCH         │  Update partial     │  UPDATE            │
│  PUT           │  Replace entirely  │  UPDATE            │
│  DELETE        │  Remove data        │  DELETE            │
└─────────────────────────────────────────────────────────────┘
```

### Real Example: Work Orders in FMS

Look at `backend/app/api/routes/work_orders.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Annotated

# Create a router - like opening a new section
router = APIRouter(prefix="/work-orders", tags=["work-orders"])

# ──────────────────────────────────────────────────────
# GET /api/v1/work-orders - List all work orders
# ──────────────────────────────────────────────────────
@router.get("")  # Empty string because prefix is "/work-orders"
def list_work_orders(
    db: Annotated[Session, Depends(get_db)],  # Database connection
    current: Annotated[User, Depends(get_current_user)],  # Who's asking?
    page: int = 1,  # Query parameter (defaults to 1)
    page_size: int = 20  # How many per page
):
    """List work orders for the current user's tenant."""
    
    # Build the query
    query = select(WorkOrder).where(
        WorkOrder.tenant_id == current.tenant_id  # Filter by tenant!
    )
    
    # Get total count for pagination
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    
    # Apply pagination
    query = query.order_by(WorkOrder.opened_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Execute and return
    work_orders = list(db.scalars(query).all())
    
    return {
        "data": work_orders,
        "meta": {"page": page, "page_size": page_size, "total": total}
    }

# ──────────────────────────────────────────────────────
# POST /api/v1/work-orders - Create a work order
# ──────────────────────────────────────────────────────
@router.post("", response_model=WorkOrderOut)
def create_work_order(
    body: WorkOrderCreate,  # Request body (validated automatically!)
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
):
    """Create a new work order."""
    
    # Create the work order
    wo = WorkOrder(
        tenant_id=current.tenant_id,  # Always use current user's tenant!
        client_id=body.client_id,
        site_id=body.site_id,
        title=body.title,
        description=body.description,
        status=WorkOrderStatus.created,
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    
    return wo

# ──────────────────────────────────────────────────────
# GET /api/v1/work-orders/{id} - Get one work order
# ──────────────────────────────────────────────────────
@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: UUID,  # This comes from the URL!
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
):
    """Get a specific work order by ID."""
    
    # Find it
    wo = db.get(WorkOrder, work_order_id)
    
    # Check if exists AND belongs to current tenant
    if not wo or wo.tenant_id != current.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT_FOUND"
        )
    
    return wo
```

### Understanding the Syntax

```python
# @router.get("")  →  @router.method("path")

# {} in path  →  URL parameter (dynamic)
# default=...  →  Query parameter (optional)
# response_model=  →  What the API returns (validates output)
# Annotated[T, Depends(...)]  →  Inject dependencies
```

---

## 3. Dependencies: The Magic Behind Authentication

### What Are Dependencies?

Dependencies are like **staff members** who do tasks for you:

```
┌─────────────────────────────────────────────────────────────┐
│                   Your Endpoint                             │
│  @router.get("/work-orders")                              │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────┐            │
│  │   Depends(get_current_user)              │            │
│  │   - Verify JWT token                   │            │
│  │   - Get user from database             │            │
│  │   - Return User object                │            │
│  └─────────────────────────────────────────┘            │
│         │                                               │
│         ▼                                               │
│         User (with tenant_id!)                           │
└─────────────────────────────────────────────────────────────┘
```

### Real Example: Get Current User

Look at `backend/app/api/deps.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jwt import decode, InvalidTokenError

# This is what the frontend sends: "Authorization: Bearer <token>"
security = HTTPBearer()

def get_current_user(
    request: Request,  # The HTTP request
    token: str = Depends(security),  # Extract the token
    db: Session = Depends(get_db),  # Get database session
) -> User:
    """Verify JWT token and return the current user."""
    
    # 1. Decode the token
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # "sub" = subject = user ID
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # 2. Get user from database
    user = db.get(User, UUID(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # 3. Return the user - now available in your endpoint!
    return user


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db  # "yield" = give this to the endpoint, then cleanup
    finally:
        db.close()  # Always close!
```

### Using Dependencies

```python
# Without dependencies - anyone can access!
def list_work_orders():
    ...

# With dependencies - authenticated users only
def list_work_orders(
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Now you know WHO is making the request!
    print(f"User {current.email} from tenant {current.tenant_id}")
```

---

## 4. Error Handling

### Why Error Handling Matters

When something goes wrong, you need to tell the client **nicely**:

```
┌─────────────────────────────────────────────────────────────┐
│   HTTP Status Codes                                  │
├─────────────────────────────────────────────────────────────┤
│   200  │  OK            │  Success!              │
│   201  │  Created       │  Created successfully  │
│   400  │  Bad Request  │  Invalid input         │
│   401  │  Unauthorized │  Not logged in        │
│   403  │  Forbidden    │  No permission        │
│   404  │  Not Found    │  Doesn't exist        │
│   500  │  Server Error │  Oops!               │
└─────────────────────────────────────────────────────────────┘
```

### Real Examples from FMS

```python
from fastapi import HTTPException, status

# Not Found - but don't reveal why!
if not wo or wo.tenant_id != current.tenant_id:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="NOT_FOUND"  # Generic message
    )

# Bad Input
if body.tags:
    invalid = set(body.tags) - VALID_TAGS
    if invalid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tags: {', '.join(invalid)}"
        )

# Permission Denied
if current.role == UserRole.technician and wo.assignee_user_id != current.id:
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")
```

---

## 5. Request Bodies: Pydantic Validation

### What is Pydantic?

Pydantic is like a **bouncer** - it checks if your request is valid before letting it in:

```python
from pydantic import BaseModel, Field
from uuid import UUID

class WorkOrderCreate(BaseModel):
    """What a client must send to create a work order."""
    
    # Required fields - no default value
    title: str = Field(..., min_length=1, max_length=512)
    client_id: UUID
    site_id: UUID
    
    # Optional fields - have defaults
    description: str = ""
    urgency: Urgency = Urgency.normal
    category: str = "general"
    tags: list[str] = []
```

**This means:**
- `title` - must be 1-512 characters
- `client_id` and `site_id` - required UUIDs
- Everything else - optional with defaults

### Auto-Validation in Action

```python
# Client sends:
# {
#   "title": "",           # ❌ Error! Too short
#   "client_id": "not-uuid" # ❌ Error! Not valid UUID
# }

# FastAPI automatically returns:
# {
#   "detail": [
#     {"loc": ["body", "title"], "msg": "String should have at least 1 character"}
#   ]
# }
```

---

## 6. Practice Exercises

### Exercise 1: Create a Simple Endpoint

Create `/api/v1/users/me` that returns the current user's info:

```python
# Hint: Use get_current_user dependency!
@router.get("/users/me")
def get_me(current: Annotated[User, Depends(get_current_user)]):
    return {
        "id": current.id,
        "email": current.email,
        "name": current.full_name,
        "role": current.role.value,
    }
```

### Exercise 2: Add a Filter

Add a query parameter to filter work orders by status:

```python
@router.get("/work-orders")
def list_work_orders(
    # Add this parameter
    status: str | None = Query(None),
    ...
):
    query = select(WorkOrder).where(...)
    
    if status:
        query = query.where(WorkOrder.status == status)
    
    return db.scalars(query).all()
```

### Exercise 3: Create a New Route

Create a `/health` endpoint that returns server status:

```python
@router.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

---

## 7. Key Takeaways

| Concept | Purpose | FMS Example |
|---------|---------|-------------|
| `FastAPI()` | Create the app | `app/main.py` |
| `APIRouter()` | Group endpoints | `routes/work_orders.py` |
| `@router.get/post/patch` | Define HTTP methods | CRUD operations |
| `Depends()` | Inject dependencies | Auth, DB |
| `HTTPException()` | Return errors | 404, 403, 400 |
| `BaseModel` | Validate requests | `schemas.py` |

---

## 8. Next Steps

1. **Read more routes**: Check `backend/app/api/routes/` for more examples
2. **Try the API**: Run `uvicorn` and visit `/docs`
3. **Add background tasks**: Learn about `BackgroundTasks` for async work
4. **WebSockets**: Explore `backend/app/realtime.py`

---

## References

- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [FMS Main App](backend/app/main.py)
- [FMS Work Orders](backend/app/api/routes/work_orders.py)
- [FMS Dependencies](backend/app/api/deps.py)