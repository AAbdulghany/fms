"""A3 — tax_profiles + work_order_parts.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    tables = set(insp.get_table_names())

    if "tax_profiles" not in tables:
        op.create_table(
            "tax_profiles",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("name", sa.String(255), nullable=False, server_default="Standard VAT"),
            sa.Column("rate_percent", sa.Numeric(6, 3), nullable=False, server_default="15"),
            sa.Column("tax_inclusive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("rounding", sa.String(16), nullable=False, server_default="HALF_UP"),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        )
        op.create_index("ix_tax_profiles_tenant_id", "tax_profiles", ["tenant_id"])

    if "work_order_parts" not in tables:
        op.create_table(
            "work_order_parts",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id"), nullable=False),
            sa.Column("work_order_id", sa.Uuid(), sa.ForeignKey("work_orders.id"), nullable=False),
            sa.Column("part_id", sa.Uuid(), sa.ForeignKey("parts_catalog.id"), nullable=False),
            sa.Column("quantity", sa.Numeric(14, 4), nullable=False, server_default="1"),
            sa.Column("unit_cost_sar", sa.Numeric(12, 2), nullable=False, server_default="0"),
        )
        op.create_index("ix_work_order_parts_wo", "work_order_parts", ["work_order_id"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    tables = set(insp.get_table_names())
    if "work_order_parts" in tables:
        op.drop_table("work_order_parts")
    if "tax_profiles" in tables:
        op.drop_table("tax_profiles")
