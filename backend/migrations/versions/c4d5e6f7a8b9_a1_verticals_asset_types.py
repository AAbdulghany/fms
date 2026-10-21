"""A1 — Add verticals, asset type catalog + tenant library; expand clients and assets.

Revision ID: c4d5e6f7a8b9
Revises: extend_user_role_enum
Create Date: 2026-10-22

Phase E (expand): all new columns are nullable; no data is written.
Catalog seed and backfill are separate steps (see §6.2 and §6.3 of the tech design).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision = "c4d5e6f7a8b9"
down_revision = "extend_user_role_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    dialect = conn.dialect.name
    existing_tables = set(insp.get_table_names())

    # ------------------------------------------------------------------
    # 1. verticals
    # ------------------------------------------------------------------
    if "verticals" not in existing_tables:
        op.create_table(
            "verticals",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(32), nullable=False, unique=True),
            sa.Column("name_en", sa.String(128), nullable=False),
            sa.Column("name_ar", sa.String(128), nullable=False),
            sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )

    # ------------------------------------------------------------------
    # 2. asset_type_templates
    # ------------------------------------------------------------------
    if "asset_type_templates" not in existing_tables:
        op.create_table(
            "asset_type_templates",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("code", sa.String(64), nullable=False, unique=True),
            sa.Column("name_en", sa.String(128), nullable=False),
            sa.Column("name_ar", sa.String(128), nullable=False),
            sa.Column("default_max_age_years", sa.Integer, nullable=True),
            sa.Column("default_max_repair_count", sa.Integer, nullable=True),
            sa.Column("default_criticality", sa.String(32), nullable=True),
            sa.Column("default_frequency", sa.String(32), nullable=True),
            sa.Column("default_report_template_code", sa.String(64), nullable=True),
            sa.Column("version", sa.Integer, nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # ------------------------------------------------------------------
    # 3. asset_type_template_verticals (join)
    # ------------------------------------------------------------------
    if "asset_type_template_verticals" not in existing_tables:
        op.create_table(
            "asset_type_template_verticals",
            sa.Column(
                "template_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("asset_type_templates.id"),
                primary_key=True,
            ),
            sa.Column(
                "vertical_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("verticals.id"),
                primary_key=True,
            ),
        )

    # ------------------------------------------------------------------
    # 4. asset_types (tenant library)
    # ------------------------------------------------------------------
    if "asset_types" not in existing_tables:
        op.create_table(
            "asset_types",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "tenant_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tenants.id"),
                nullable=False,
            ),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("name_en", sa.String(128), nullable=False),
            sa.Column("name_ar", sa.String(128), nullable=False),
            sa.Column("default_max_age_years", sa.Integer, nullable=True),
            sa.Column("default_max_repair_count", sa.Integer, nullable=True),
            sa.Column("default_criticality", sa.String(32), nullable=True),
            sa.Column("default_frequency", sa.String(32), nullable=True),
            sa.Column(
                "default_report_template_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("report_templates.id"),
                nullable=True,
            ),
            sa.Column("origin", sa.String(16), nullable=False, server_default="custom"),
            sa.Column(
                "source_template_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("asset_type_templates.id"),
                nullable=True,
            ),
            sa.Column("source_version", sa.Integer, nullable=True),
            sa.Column("adopted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("tenant_id", "code", name="uq_asset_type_tenant_code"),
            sa.UniqueConstraint(
                "tenant_id", "source_template_id", name="uq_asset_type_tenant_source"
            ),
        )
        op.create_index(
            "ix_asset_types_tenant_active", "asset_types", ["tenant_id", "is_active"]
        )

    # ------------------------------------------------------------------
    # 5. asset_type_verticals (join, tenant)
    # ------------------------------------------------------------------
    if "asset_type_verticals" not in existing_tables:
        op.create_table(
            "asset_type_verticals",
            sa.Column(
                "asset_type_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("asset_types.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                "vertical_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("verticals.id"),
                primary_key=True,
            ),
        )

    # ------------------------------------------------------------------
    # 6. clients.vertical_id (nullable FK, expand only)
    # ------------------------------------------------------------------
    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "vertical_id" not in client_cols:
        op.add_column(
            "clients",
            sa.Column(
                "vertical_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("verticals.id"),
                nullable=True,
            ),
        )

    # ------------------------------------------------------------------
    # 7. assets.asset_type_id (nullable FK + index)
    # ------------------------------------------------------------------
    asset_cols = {c["name"] for c in insp.get_columns("assets")}
    if "asset_type_id" not in asset_cols:
        op.add_column(
            "assets",
            sa.Column(
                "asset_type_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("asset_types.id"),
                nullable=True,
            ),
        )
        # Postgres: use CONCURRENTLY so it doesn't lock the table
        if dialect == "postgresql":
            with op.get_context().autocommit_block():
                op.execute(
                    text(
                        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_assets_tenant_asset_type"
                        " ON assets (tenant_id, asset_type_id)"
                    )
                )
        else:
            op.create_index(
                "ix_assets_tenant_asset_type", "assets", ["tenant_id", "asset_type_id"]
            )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    dialect = conn.dialect.name
    existing_tables = set(insp.get_table_names())

    # Drop index on assets
    if dialect == "postgresql":
        op.execute(text("DROP INDEX IF EXISTS ix_assets_tenant_asset_type"))
    else:
        asset_idxs = {i["name"] for i in insp.get_indexes("assets")}
        if "ix_assets_tenant_asset_type" in asset_idxs:
            op.drop_index("ix_assets_tenant_asset_type", table_name="assets")

    # Drop assets.asset_type_id
    asset_cols = {c["name"] for c in insp.get_columns("assets")}
    if "asset_type_id" in asset_cols:
        op.drop_column("assets", "asset_type_id")

    # Drop clients.vertical_id
    client_cols = {c["name"] for c in insp.get_columns("clients")}
    if "vertical_id" in client_cols:
        op.drop_column("clients", "vertical_id")

    # Drop tables in reverse dependency order
    for tbl in (
        "asset_type_verticals",
        "asset_types",
        "asset_type_template_verticals",
        "asset_type_templates",
        "verticals",
    ):
        if tbl in existing_tables:
            op.drop_table(tbl)
