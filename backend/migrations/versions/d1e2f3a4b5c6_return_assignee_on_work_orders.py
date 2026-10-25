"""Remember who to restore after a report is sent for approval.

Revision ID: d1e2f3a4b5c6
Revises: c0d1e2f3a4b5
Create Date: 2026-10-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d1e2f3a4b5c6"
down_revision = "c0d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("return_assignee_user_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_work_orders_return_assignee_user_id",
        "work_orders",
        "users",
        ["return_assignee_user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_work_orders_return_assignee_user_id", "work_orders", type_="foreignkey")
    op.drop_column("work_orders", "return_assignee_user_id")
