"""Add users.username and clients.status (Phase 3).

Revision ID: f8a1b2c3d4e5
Revises: 9a2b3c4d5e6f
Create Date: 2026-04-18

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "f8a1b2c3d4e5"
down_revision = "9a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    dialect = conn.dialect.name

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "username" not in user_cols:
        op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
        if dialect == "postgresql":
            op.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tenant_username "
                    "ON users (tenant_id, username)"
                )
            )
        else:
            op.create_unique_constraint("uq_user_tenant_username", "users", ["tenant_id", "username"])

    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "status" not in client_cols:
        op.add_column(
            "clients",
            sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    dialect = conn.dialect.name

    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "status" in client_cols:
        op.drop_column("clients", "status")

    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "username" in user_cols:
        if dialect == "postgresql":
            op.execute(text("DROP INDEX IF EXISTS uq_user_tenant_username"))
        else:
            try:
                op.drop_constraint("uq_user_tenant_username", "users", type_="unique")
            except Exception:
                pass
        op.drop_column("users", "username")
