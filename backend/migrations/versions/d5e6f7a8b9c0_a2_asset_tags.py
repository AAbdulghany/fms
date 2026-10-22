"""A2 — asset_tags for opaque public QR tokens.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "asset_tags" in set(insp.get_table_names()):
        return
    op.create_table(
        "asset_tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("token", sa.String(16), nullable=False, unique=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_asset_tags_asset_status", "asset_tags", ["asset_id", "status"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "asset_tags" not in set(insp.get_table_names()):
        return
    op.drop_index("ix_asset_tags_asset_status", table_name="asset_tags")
    op.drop_table("asset_tags")
