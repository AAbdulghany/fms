# JWT Authentication — Learning How Auth Works

> **Goal**: Understand how FMS handles authentication. Learn to secure your API like a pro.

---

## The Authentication Problem

### How Do We Know Who You Are?

```
┌─────────────────────────────────────────────────────────────┐
│          WITHOUT Authentication (Unsafe)                    │
├─────────────────────────────────────────────────────────────┤
│  Client: "Give me all work orders!"                       │
│  Server: "Here you go!" 😱                                │
│                                                             │
│  Problem: Anyone can access any data!                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          WITH Authentication (Safe)                       │
├─────────────────────────────────────────────────────────────┤
│  Client: "Here's my token: eyJhbGciOiJIUzI1NiIs..."      │
│  Server: ✅ Token valid! You're John, tenant ABC         │
│  Server: "Here are YOUR work orders."                      │
│                                                             │
│  ✅ Only see data for your tenant                        │
│  ✅ Actions are attributed to you                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. JWT: The Token Format

### What is a JWT?

JWT (JSON Web Token) is like an **ID card** - it contains information and can't be forged:

```
┌─────────────────────────────────────────────────────────────┐
│                JWT Structure                              │
├─────────────────────────────────────────────────────────────┤
│  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9          │
│  .eyJzdWIiOiJjNTlmNWU3MTMtNzM5NS00...             │
│  .SflKxwRJSMeKKF2QT4fwpMeJf36POk6tS8Y               │
│      │                                                      │
│      ├── Header: What type of token it is                  │
│      ├── Payload: What's in the token                       │
│      └── Signature: Verify it's not fake                   │
└─────────────────────────────────────────────────────────────┘
```

### The Three Parts

```
1. HEADER:
{
  "alg": "HS256",   ← Algorithm to sign
  "typ": "JWT"      ← Type
}

2. PAYLOAD (the data):
{
  "sub": "user-uuid-123",     ← Subject (user ID)
  "tenant_id": "tenant-uuid",  ← Which tenant
  "role": "company_admin",    ← Permission level
  "exp": 1700000000         ← Expiration timestamp
}

3. SIGNATURE:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  SECRET_KEY
)
```

---

## 2. Password Hashing: Never Store Plain Text

### The Problem

```
┌─────────────────────────────────────────────────────────────┐
│          NEVER store passwords in plain text!               │
├─────────────────────────────────────────────────────────────┤
│  Database:                                │                  │
│  ┌──────────────────────────────────┐ │                  │
│  │ email: john@example.com           │ │                  │
│  │ password: supersecret123  ← OOPS! │ │                  │
│  └──────────────────────────────────┘ │                  │
│                                          │                  │
│  If hacker steals DB:                      │                  │
│  → They have EVERY password 😱           │                  │
└─────────────────────────────────────────────────────────────┘
```

### Solution: Hashing

Hashing is like a **one-way blender** - you can turn fruit into smoothie, but can't turn smoothie back into fruit:

```python
from passlib.hash import bcrypt

# Hash a password (one-way!)
password_hash = bcrypt.hash("supersecret123")
# Result: $2b$12$LQv3c1eUr5... (60 char string)

# Verify (check if match)
bcrypt.verify("supersecret123", password_hash)  # ✅ True
bcrypt.verify("wrongpassword", password_hash)  # ❌ False
```

### How FMS Does It

Look at `backend/app/core/security.py`:

```python
from passlib.hash import bcrypt

def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return bcrypt.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.verify(plain_password, hashed_password)
```

---

## 3. Creating Tokens

### The Login Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LOGIN FLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Client sends: {email, password}                        │
│         │                                                  │
│         ▼                                                  │
│  2. Server finds user by email                            │
│         │                                                  │
│         ▼                                                  │
│  3. Server verifies password with bcrypt                 │
│         │                                                  │
│         ▼                                                  │
│  4. Server creates JWT with:                            │
│     - sub: user.id                                        ��
│     - tenant_id: user.tenant_id                          │
│     - role: user.role                                   │
│     - exp: now + 30 minutes                             │
│         │                                                  │
│         ▼                                                  │
│  5. Server returns: {access_token, user}                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Real Code: Login Endpoint

Look at `backend/app/api/routes/auth.py`:

```python
from datetime import datetime, timedelta, timezone
from jwt import encode

SECRET_KEY = "change-me-in-production-openssl-rand-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    # Add expiration
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Sign and return
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    
    # 1. Find user by email or username
    user = db.scalar(
        select(User)
        .where(
            (User.email == body.identifier) | 
            (User.username == body.identifier)
        )
    )
    
    # 2. Verify credentials
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # 3. Create tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
    })
    
    refresh_token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(days=7)
    )
    
    # 4. Return
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )
```

---

## 4. Validating Tokens: The Gatekeeper

### The get_current_user Dependency

This is the **most important** security component - it runs on every protected endpoint:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jwt import decode, InvalidTokenError
from sqlalchemy.orm import Session

# This extracts "Bearer <token>" from the request
security = HTTPBearer()

def get_current_user(
    request: Request,  # The HTTP request
    token: str = Depends(security),  # Extract token from header
    db: Session = Depends(get_db),   # Database connection
) -> User:
    """Validate JWT and return the current user."""
    
    # 1. Decode the token
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        if not user_id:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED)
            
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # 2. Get user from database
    # Always verify user exists and is active!
    user = db.get(User, UUID(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # 3. Also verify tenant matches
    if str(user.tenant_id) != tenant_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # 4. Return user - now available in endpoint!
    return user
```

### Using in Endpoints

```python
from typing import Annotated

@router.get("/work-orders")
def list_work_orders(
    # This is magic! The dependency injects the user
    current: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Now we KNOW who is making this request
    print(f"User: {current.email}")
    print(f"Tenant: {current.tenant_id}")
    print(f"Role: {current.role}")
    
    # Always filter by tenant!
    work_orders = db.scalars(
        select(WorkOrder)
        .where(WorkOrder.tenant_id == current.tenant_id)
    ).all()
    
    return work_orders
```

---

## 5. Token Refresh: Staying Logged In

### Why Refresh?

```
┌─────────────────────────────────────────────────────────────┐
│                   TOKEN EXPIRY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Access Token: 30 minutes                                  │
│  - Short-lived for security                                  │
│  - If stolen, limited damage                               │
│                                                             │
│  Refresh Token: 7 days                                    │
│  - Long-lived for convenience                             │
│  - Used to get new access tokens                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Refresh Endpoint

```python
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """Get new access token using refresh token."""
    
    try:
        payload = decode(
            body.refresh_token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
    except InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # Get user
    user = db.get(User, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    # Create new access token
    access_token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
    })
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=body.refresh_token,  # Keep same refresh
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )
```

---

## 6. Security Best Practices

### 1. Return 404, Not 403

```python
# ❌ Wrong - tells attacker "this exists"
if wo.tenant_id != current.tenant_id:
    raise HTTPException(status.HTTP_403_FORBIDDEN)

# ✅ Correct - hides existence
if not wo or wo.tenant_id != current.tenant_id:
    raise HTTPException(status.HTTP_404_NOT_FOUND)
```

### 2. Never Reveal Email in Errors

```python
# ❌ Wrong - reveals email exists
if not user:
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail=f"No user with email {email}"
    )

# ✅ Correct - same error for all failures
if not user or not verify_password(password, user.password_hash):
    raise HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )
```

### 3. Store Secrets Securely

```bash
# .env file (never commit to git!)
SECRET_KEY=your-32-character-secret-key
DATABASE_URL=postgresql://...
```

### 4. HTTPS in Production

```bash
# Development: HTTP
uvicorn main:app --host 0.0.0.0 --port 8000

# Production: HTTPS
uvicorn main:app --ssl-certfile=cert.pem --ssl-keyfile=key.pem
```

---

## 7. Role-Based Access Control (RBAC)

### Adding Role Checks

```python
def require_roles(*allowed_roles: UserRole):
    """Dependency that requires specific roles."""
    def role_checker(
        current: User = Depends(get_current_user)
    ):
        if current.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current
    return role_checker


# Using in endpoint
@router.post("/work-orders", response_model=WorkOrderOut)
def create_work_order(
    body: WorkOrderCreate,
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
    db: Session = Depends(get_db),
):
    # Only admins can create work orders
    ...
```

---

## 8. Practice Exercises

### Exercise 1: Test Login

Run this in Python:

```python
from app.core.security import verify_password

# Create a hash
hashed = get_password_hash("mypassword")
print(hashed)  # Long string

# Verify
print(verify_password("mypassword", hashed))  # True
print(verify_password("wrong", hashed))  # False
```

### Exercise 2: Decode a Token

```python
import jwt

# Create a token
token = create_access_token({"sub": "user-123", "tenant_id": "tenant-456"})

# Decode without verification (for debugging)
payload = jwt.decode(token, options={"verify_signature": False})
print(payload)  # {sub, tenant_id, exp, ...}
```

### Exercise 3: Add Last Login Tracking

```python
@router.post("/login")
def login(...):
    # After successful login:
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
```

---

## 9. Key Takeaways

| Concept | Purpose | FMS Example |
|---------|---------|-------------|
| `bcrypt` | Hash passwords safely | `security.py` |
| JWT | Stateless auth token | `auth.py` |
| `sub` claim | User identity | Token payload |
| `tenant_id` | Data isolation | Token payload |
| `role` | Permissions | Token payload |
| Access token | Short-lived | 30 min |
| Refresh token | Long-lived | 7 days |
| `Depends()` | Auth injection | All routes |

---

## 10. Next Steps

1. **Add 2FA**: Time-based one-time passwords
2. **OAuth**: Google/Microsoft login
3. **Rate limiting**: Prevent brute force

---

## References

- [PyJWT Docs](https://pyjwt.readthedocs.io/)
- [Passlib Docs](https://passlib.readthedocs.io/)
- [FMS Auth Route](backend/app/api/routes/auth.py)
- [FMS Security](backend/app/core/security.py)