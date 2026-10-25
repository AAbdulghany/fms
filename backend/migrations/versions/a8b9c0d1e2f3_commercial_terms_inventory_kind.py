"""Per-client tax on contracts + inventory item kind on parts.

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-10-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column("tax_rate_percent", sa.Numeric(6, 3), nullable=True),
    )
    op.add_column(
        "contracts",
        sa.Column("tax_inclusive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "parts_catalog",
        sa.Column("kind", sa.String(32), nullable=False, server_default="part"),
    )
    op.add_column(
        "parts_catalog",
        sa.Column("qty_on_hand", sa.Numeric(14, 4), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("parts_catalog", "qty_on_hand")
    op.drop_column("parts_catalog", "kind")
    op.drop_column("contracts", "tax_inclusive")
    op.drop_column("contracts", "tax_rate_percent")
