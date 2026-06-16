"""Apply lightweight DDL so existing DB volumes match current models (no Alembic required)."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.models import (
    Notification,
    PlatformSettings,
    SubscriptionPackage,
    TenantSubscription,
)


def ensure_schema(engine: Engine) -> None:
    """Add columns/tables introduced after initial deploys; safe to run every startup."""
    try:
        insp = inspect(engine)
    except Exception:
        return

    dialect = engine.dialect.name

    with engine.begin() as conn:
        if not insp.has_table("notifications"):
            Notification.__table__.create(conn, checkfirst=True)

        for model in (SubscriptionPackage, TenantSubscription, PlatformSettings):
            if not insp.has_table(model.__tablename__):
                model.__table__.create(conn, checkfirst=True)

        if insp.has_table("users"):
            cols = {c["name"] for c in insp.get_columns("users")}
            if "username" not in cols:
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(64)"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"))
                try:
                    conn.execute(
                        text(
                            "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tenant_username "
                            "ON users (tenant_id, username)"
                        )
                    )
                except Exception:
                    pass

        if insp.has_table("clients"):
            cols = {c["name"] for c in insp.get_columns("clients")}
            if "status" not in cols:
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE clients ADD COLUMN status VARCHAR(32) NOT NULL DEFAULT 'active'")
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(32) "
                            "NOT NULL DEFAULT 'active'"
                        )
                    )

        if insp.has_table("assets"):
            cols = {c["name"] for c in insp.get_columns("assets")}
            if "label_code" not in cols:
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE assets ADD COLUMN label_code VARCHAR(64)"))
                else:
                    conn.execute(
                        text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS label_code VARCHAR(64)")
                    )
