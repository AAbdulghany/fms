"""One-off role migration for dev and demo databases.

Maps legacy platform super_admin → super_user and ensures company_engineer enum exists.

Usage:
  cd backend
  DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:5432/fms_demo python -m scripts.migrate_roles
  DATABASE_URL=postgresql+psycopg2://fms:fms@localhost:5432/fms python -m scripts.migrate_roles
"""

from __future__ import annotations

from sqlalchemy import text

from app.database import SessionLocal, engine
from app.schema_ensure import ensure_schema


def migrate() -> None:
    ensure_schema(engine)
    with SessionLocal() as db:
        result = db.execute(
            text(
                """
                UPDATE users
                SET role = 'super_user'
                WHERE is_platform_admin = true AND role = 'super_admin'
                """
            )
        )
        db.commit()
        print(f"Updated {result.rowcount} platform super_admin -> super_user")


if __name__ == "__main__":
    migrate()
