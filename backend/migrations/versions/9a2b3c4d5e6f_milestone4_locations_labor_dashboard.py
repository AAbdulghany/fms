"""Milestone 4: locations, labor, optional location on assets/work orders

Revision ID: 9a2b3c4d5e6f
Revises: 7aa62ddc0ef8
Create Date: 2026-04-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a2b3c4d5e6f"
down_revision = "7aa62ddc0ef8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("site_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location_type", sa.String(length=32), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "technician_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("hourly_rate_sar", sa.Numeric(12, 2), nullable=False),
        sa.Column("overtime_multiplier", sa.Numeric(6, 4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("skills_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tech_profile_tenant_user"),
    )
    op.create_table(
        "labor_entries",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("work_order_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours_regular", sa.Numeric(8, 2), nullable=False),
        sa.Column("hours_overtime", sa.Numeric(8, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "technician_schedules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(length=8), nullable=False),
        sa.Column("end_time", sa.String(length=8), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "day_of_week", name="uq_tech_schedule_day"),
    )
    op.add_column("assets", sa.Column("location_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_assets_location_id_locations",
        "assets",
        "locations",
        ["location_id"],
        ["id"],
    )
    op.add_column("work_orders", sa.Column("location_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_work_orders_location_id_locations",
        "work_orders",
        "locations",
        ["location_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_work_orders_location_id_locations", "work_orders", type_="foreignkey")
    op.drop_column("work_orders", "location_id")
    op.drop_constraint("fk_assets_location_id_locations", "assets", type_="foreignkey")
    op.drop_column("assets", "location_id")
    op.drop_table("technician_schedules")
    op.drop_table("labor_entries")
    op.drop_table("technician_profiles")
    op.drop_table("locations")
