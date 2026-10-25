"""A5: downtime windows + failure/symptom codes on work orders + diagnostic catalog.

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-10-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("downtime_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("downtime_ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("failure_code", sa.String(64), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("symptom_code", sa.String(64), nullable=True),
    )

    op.create_table(
        "diagnostic_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),  # failure | symptom
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name_en", sa.String(255), nullable=False, server_default=""),
        sa.Column("name_ar", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "kind", "code", name="uq_diagnostic_tenant_kind_code"),
    )
    op.create_index("ix_diagnostic_codes_tenant_kind", "diagnostic_codes", ["tenant_id", "kind"])


def downgrade() -> None:
    op.drop_index("ix_diagnostic_codes_tenant_kind", table_name="diagnostic_codes")
    op.drop_table("diagnostic_codes")
    op.drop_column("work_orders", "symptom_code")
    op.drop_column("work_orders", "failure_code")
    op.drop_column("work_orders", "downtime_ended_at")
    op.drop_column("work_orders", "downtime_started_at")
