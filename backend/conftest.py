"""
Pytest configuration and fixtures for FMS backend tests.
"""

import sys
from pathlib import Path

# Add backend directory to Python path so 'app' module can be imported
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from sqlalchemy import create_engine, event, JSON, Text, String
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import sqlalchemy

# Import and patch before importing Base
from sqlalchemy.dialects import postgresql

# Create SQLite-compatible versions of PostgreSQL types
_original_JSONB = postgresql.JSONB
_original_ARRAY = sqlalchemy.ARRAY


class JSONBCompat(JSON):
    """JSONB compatibility for SQLite."""
    __visit_name__ = "JSON"


class ARRAYCompat(JSON):
    """ARRAY compatibility for SQLite - stores as JSON."""
    __visit_name__ = "JSON"
    
    def __init__(self, item_type=None, *args, **kwargs):
        # Accept item_type parameter but ignore it since SQLite stores as JSON
        super().__init__(*args, **kwargs)


# Monkey-patch for tests - patch both import locations
postgresql.JSONB = JSONBCompat
postgresql.base.JSONB = JSONBCompat
postgresql.ARRAY = ARRAYCompat
postgresql.base.ARRAY = ARRAYCompat
# Also patch the main sqlalchemy.ARRAY which is used in models.py
sqlalchemy.ARRAY = ARRAYCompat


from app.database import Base


@pytest.fixture(scope="function")
def db_session():
    """
    Create an in-memory SQLite database for testing.
    Each test gets a fresh database.
    """
    # Use in-memory SQLite for fast tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign keys in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def sample_tenant(db_session):
    """Create a test tenant."""
    from uuid import uuid4
    from app.models import Tenant
    
    tenant = Tenant(id=uuid4(), name="Test Tenant", status="active")
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def sample_client(db_session, sample_tenant):
    """Create a test client."""
    from uuid import uuid4
    from app.models import Client
    
    client = Client(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        legal_name="Test Client Corp",
        code="TST001",
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client


@pytest.fixture
def sample_site(db_session, sample_tenant, sample_client):
    """Create a test site."""
    from uuid import uuid4
    from app.models import Site
    
    site = Site(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        name="Test Site",
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture
def sample_user(db_session, sample_tenant):
    """Create a test user with super_admin role."""
    from uuid import uuid4
    from app.models import User, UserRole
    from app.core.security import hash_password
    
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="admin@test.com",
        password_hash=hash_password("password123"),
        full_name="Test Admin",
        role=UserRole.super_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def api_client(db_session):
    from fastapi.testclient import TestClient

    from app.database import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
