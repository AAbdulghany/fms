"""add_work_order_documents_table

Revision ID: cff59fe5d61e
Revises: 6ce5b3822c48
Create Date: 2026-04-18 04:44:41.929254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cff59fe5d61e'
down_revision = '6ce5b3822c48'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'work_order_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('work_order_id', sa.UUID(), nullable=False),
        sa.Column('uploaded_by_user_id', sa.UUID(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_type', sa.String(length=100), nullable=False),
        sa.Column('file_url', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['work_order_id'], ['work_orders.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('work_order_documents')
