"""Extend user_role column to support longer role names

Revision ID: extend_user_role_enum
Revises: b3c4d5e6f7a8
Create Date: 2026-06-27

"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text


revision = "extend_user_role_enum"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Extend the role column to support longer enum values."""
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    if dialect == "postgresql":
        # Change the role column to use unlimited VARCHAR
        # This removes the 13 character limit
        op.execute(text("""
            ALTER TABLE users ALTER COLUMN role TYPE VARCHAR;
        """))


def downgrade() -> None:
    """Restore the original character limit (not recommended)."""
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    if dialect == "postgresql":
        op.execute(text("""
            ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(13);
        """))
