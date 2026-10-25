"""Add job_started_at / job_ended_at for auto labor clock on work orders.

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-10-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("job_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("job_ended_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("work_orders", "job_ended_at")
    op.drop_column("work_orders", "job_started_at")
