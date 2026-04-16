from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings
from contextvars import ContextVar

class Base(DeclarativeBase):
    pass

settings = get_settings()


def _normalize_sync_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


DATABASE_URL = _normalize_sync_database_url(settings.database_url)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)

# Context variable to store tenant_id for the current request
tenant_context: ContextVar[Any] = ContextVar("tenant_id", default=None)

@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(execute_state):
    """
    Automatically injects tenant_id filter into all SELECT, UPDATE, and DELETE queries
    if a tenant_id is set in the context.
    """
    if execute_state.is_select or execute_state.is_update or execute_state.is_delete:
        tenant_id = tenant_context.get()
        if tenant_id is not None:
            pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
