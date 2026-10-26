"""Hot-path composite indexes for list/filter queries (P19).

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-10-26
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None

# (index_name, table_name, columns)
_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_work_orders_tenant_status", "work_orders", ["tenant_id", "status"]),
    ("ix_work_orders_tenant_opened", "work_orders", ["tenant_id", "opened_at"]),
    ("ix_work_orders_tenant_site", "work_orders", ["tenant_id", "site_id"]),
    ("ix_work_orders_tenant_assignee", "work_orders", ["tenant_id", "assignee_user_id"]),
    ("ix_work_orders_tenant_client", "work_orders", ["tenant_id", "client_id"]),
    ("ix_audit_logs_tenant_entity", "audit_logs", ["tenant_id", "entity_type", "entity_id"]),
    ("ix_audit_logs_tenant_created", "audit_logs", ["tenant_id", "created_at"]),
    (
        "ix_maintenance_schedules_tenant_due",
        "maintenance_schedules",
        ["tenant_id", "is_active", "next_due_at"],
    ),
    ("ix_maintenance_schedules_asset", "maintenance_schedules", ["asset_id"]),
    ("ix_invoices_tenant_status", "invoices", ["tenant_id", "status"]),
    ("ix_invoices_tenant_issued", "invoices", ["tenant_id", "issued_at"]),
    ("ix_invoices_tenant_client", "invoices", ["tenant_id", "client_id"]),
    ("ix_assets_tenant_site", "assets", ["tenant_id", "site_id"]),
    ("ix_assets_tenant_lifecycle", "assets", ["tenant_id", "lifecycle_status"]),
]


def _existing_index_names(insp, table: str) -> set[str]:
    if table not in set(insp.get_table_names()):
        return set()
    return {ix["name"] for ix in insp.get_indexes(table)}


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    for name, table, cols in _INDEXES:
        if name in _existing_index_names(insp, table):
            continue
        if table not in set(insp.get_table_names()):
            continue
        op.create_index(name, table, cols)


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    for name, table, _cols in reversed(_INDEXES):
        if name not in _existing_index_names(insp, table):
            continue
        op.drop_index(name, table_name=table)
