"""A3 — parts_catalog bilingual names (EN + Egyptian Arabic).

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "parts_catalog" not in set(insp.get_table_names()):
        return
    cols = {c["name"] for c in insp.get_columns("parts_catalog")}
    if "name_en" not in cols:
        op.add_column("parts_catalog", sa.Column("name_en", sa.String(255), nullable=True))
    if "name_ar" not in cols:
        op.add_column("parts_catalog", sa.Column("name_ar", sa.String(255), nullable=True))
    # Backfill from legacy name
    op.execute(
        sa.text(
            "UPDATE parts_catalog SET name_en = COALESCE(NULLIF(name_en, ''), name) "
            "WHERE name_en IS NULL OR name_en = ''"
        )
    )
    op.execute(
        sa.text(
            "UPDATE parts_catalog SET name_ar = COALESCE(NULLIF(name_ar, ''), name) "
            "WHERE name_ar IS NULL OR name_ar = ''"
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "parts_catalog" not in set(insp.get_table_names()):
        return
    cols = {c["name"] for c in insp.get_columns("parts_catalog")}
    if "name_ar" in cols:
        op.drop_column("parts_catalog", "name_ar")
    if "name_en" in cols:
        op.drop_column("parts_catalog", "name_en")
