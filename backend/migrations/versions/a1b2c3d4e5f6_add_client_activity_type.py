"""Add clients.activity_type (Phase 3 MVP).

Revision ID: a1b2c3d4e5f6
Revises: f8a1b2c3d4e5
Create Date: 2026-06-07

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "a1b2c3d4e5f6"
down_revision = "cff59fe5d61e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "activity_type" not in client_cols:
        op.add_column(
            "clients",
            sa.Column("activity_type", sa.String(length=64), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "activity_type" in client_cols:
        op.drop_column("clients", "activity_type")
