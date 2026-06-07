# Alembic Migrations — Knowledge Hub

> Learn database migrations by studying the FMS codebase.

---

## 1. Alembic Setup

### Configuration

```python
# backend/alembic.ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console
```

### Environment

```python
# backend/migrations/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from alembic.config import Config

# Import models for autogenerate
from app.models import Base
from app.config import get_settings

config = context.config
settings = get_settings()

config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
```

---

## 2. Creating Migrations

### Generate Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add work order tags"

# Empty migration (manual)
alembic revision -m "add custom field"
```

### Example: Add Column

```python
"""add work order tags

Revision ID: abc123
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123'
down_revision = None  # Set to previous revision
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        'work_orders',
        sa.Column(
            'tags',
            sa.ARRAY(sa.String()),
            server_default='{}',
            nullable=False
        )
    )

def downgrade():
    op.drop_column('work_orders', 'tags')
```

### Example: Add Table

```python
"""create user site scopes table

Revision ID: abc123
Revises: previous
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'user_site_scopes',
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['site_id'], ['sites.id']),
        sa.PrimaryKeyConstraint('user_id', 'site_id')
    )

def downgrade():
    op.drop_table('user_site_scopes')
```

---

## 3. Running Migrations

### CLI Commands

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade specific version
alembic upgrade abc123

# Downgrade one step
alembic downgrade -1

# Downgrade to specific
alembic downgrade abc123

# Show migration history
alembic history

# Current version
alembic current

# Stamp version (without running)
alembic stamp abc123
```

### In Code

```python
from alembic import command
from alembic.config import Config

def run_migrations():
    config = Config("alembic.ini")
    command.upgrade(config, "head")
```

---

## 4. Migration Patterns

### Add Enum Column

```python
def upgrade():
    # Create enum type
    work_order_status = postgresql.ENUM(
        'created', 'assigned', 'in_progress', 'on_hold',
        'completed', 'verified', 'cancelled', 'closed',
        name='work_order_status'
    )
    work_order_status.create(op.get_bind(), checkfirst=True)
    
    # Add column with enum
    op.add_column(
        'work_orders',
        sa.Column(
            'status',
            work_order_status,
            server_default='created',
            nullable=False
        )
    )

def downgrade():
    op.drop_column('work_orders', 'status')
```

### Add JSONB Column

```python
def upgrade():
    op.add_column(
        'work_orders',
        sa.Column(
            'metadata_json',
            postgresql.JSONB,
            server_default='{}',
            nullable=False
        )
    )

def downgrade():
    op.drop_column('work_orders', 'metadata_json')
```

### Rename Table

```python
def upgrade():
    op.rename_table('old_name', 'new_name')

def downgrade():
    op.rename_table('new_name', 'old_name')
```

### Add Index

```python
def upgrade():
    op.create_index(
        'ix_work_order_status',
        'work_orders',
        ['tenant_id', 'status']
    )

def downgrade():
    op.drop_index('ix_work_order_status')
```

---

## 5. Best Practices

### 1. Always Downgrade

```python
def upgrade():
    op.add_column('table', sa.Column('field', ...))

def downgrade():
    op.drop_column('table', 'field')
```

### 2. Use Server Defaults

```python
# Good: Provides default for existing rows
sa.Column('status', sa.String(), server_default='created')

# Problematic: Existing rows get NULL
sa.Column('status', sa.String(), nullable=True)
```

### 3. Batch Operations for Large Tables

```python
def upgrade():
    # For large tables, use batch operations
    op.batch_alter_table(
        'large_table',
        changes=[
            op.add_column('field', sa.String())
        ]
    )
```

---

## 6. FMS Migration Examples

### Location Table

```python
# migrations/versions/9a2b3c4d5e6f_milestone4_locations_labor_dashboard.py
"""Milestone 4: Locations, Labor, Dashboard

Revision ID: 9a2b3c4d5e6f
Revises: 7aa62ddc0ef8
Create Date: 2024-04-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '9a2b3c4d5e6f'
down_revision = '7aa62ddc0ef8'

def upgrade():
    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('site_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True)),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('location_type', sa.String(32), server_default='other'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('metadata_json', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Add foreign keys
    op.create_foreign_key(
        'fk_location_tenant',
        'locations', 'tenants',
        ['tenant_id'], ['id']
    )
    
    op.create_foreign_key(
        'fk_location_site',
        'locations', 'sites',
        ['site_id'], ['id']
    )

def downgrade():
    op.drop_table('locations')
```

---

## 7. Practice Exercises

### Exercise 1: Create a Simple Migration

Add a `phone` field to users:

```python
"""Add phone field to users

Revision ID: abc123
Revises: previous
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column(
        'users',
        sa.Column('phone', sa.String(64), nullable=True)
    )

def downgrade():
    op.drop_column('users', 'phone')
```

### Exercise 2: Create a Foreign Key

Add site_id to work_orders:

```python
def upgrade():
    op.add_column(
        'work_orders',
        sa.Column('site_id', postgresql.UUID(as_uuid=True))
    )
    
    op.create_foreign_key(
        'fk_wo_site',
        'work_orders', 'sites',
        ['site_id'], ['id']
    )

def downgrade():
    op.drop_foreign_key('fk_wo_site', 'work_orders')
    op.drop_column('work_orders', 'site_id')
```

---

## References

- [Alembic Docs](https://alembic.sqlalchemy.org/)
- [FMS Migrations](backend/migrations/versions/)
- [FMS env.py](backend/migrations/env.py)