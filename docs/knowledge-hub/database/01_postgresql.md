# PostgreSQL — Knowledge Hub

> Learn PostgreSQL by studying the FMS codebase.

---

## 1. PostgreSQL Basics

### Connecting

```bash
# CLI connection
psql -U fms -d fms -h localhost

# With password
psql postgresql://fms:fms@localhost:5432/fms
```

### Basic Commands

```sql
-- List databases
\l

-- Connect to database
\c fms

-- List tables
\dt

-- Describe table
\d users

-- List indexes
\di
```

---

## 2. PostgreSQL Types Used in FMS

### UUID

```sql
-- UUID type (primary key)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
);

-- Foreign key reference
CREATE TABLE work_orders (
    tenant_id UUID REFERENCES tenants(id),
    ...
);
```

### JSONB

```sql
-- JSONB for flexible data
CREATE TABLE work_orders (
    metadata_json JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT '{}',
);

-- Query JSONB
SELECT * FROM work_orders 
WHERE metadata_json->>'priority' = 'high';

-- Update JSONB
UPDATE work_orders 
SET metadata_json = metadata_json || '{"priority": "high"}'
WHERE id = '...';
```

### Arrays

```sql
-- Array of strings
tags TEXT[]

-- Query arrays
SELECT * FROM work_orders 
WHERE 'corrective' = ANY(tags);

-- Overlap query
SELECT * FROM work_orders 
WHERE tags && ARRAY['corrective', 'preventive'];
```

### Enums

```sql
-- Create enum type
CREATE TYPE user_role AS ENUM (
    'super_admin',
    'company_admin', 
    'client_admin',
    'site_manager',
    'technician',
    'manager'
);

-- Use in table
CREATE TABLE users (
    role user_role NOT NULL
);
```

---

## 3. Indexes

### Standard Indexes

```sql
-- Basic index
CREATE INDEX ix_work_order_tenant_id ON work_orders(tenant_id);

-- Composite index (for filtering)
CREATE INDEX ix_work_order_status ON work_orders(tenant_id, status);

-- Partial index (for common queries)
CREATE INDEX ix_work_order_open ON work_orders(tenant_id, opened_at)
WHERE status IN ('created', 'assigned', 'in_progress');
```

### GIN Index (for JSONB/Arrays)

```sql
-- For JSONB queries
CREATE INDEX ix_work_order_metadata_gin ON work_orders USING gin(metadata_json);

-- For array queries
CREATE INDEX ix_work_order_tags_gin ON work_orders USING gin(tags);
```

---

## 4. Constraints

### Unique Constraints

```sql
-- Single column
ALTER TABLE users ADD CONSTRAINT uq_user_email UNIQUE(email);

-- Composite (across tenant)
ALTER TABLE users ADD CONSTRAINT uq_user_tenant_email 
UNIQUE(tenant_id, email);
```

### Check Constraints

```sql
-- Ensure positive numbers
ALTER TABLE invoices 
ADD CONSTRAINT chk_positive_total 
CHECK (total_sar >= 0);

-- Limit values
ALTER TABLE work_orders 
ADD CONSTRAINT chk_valid_status 
CHECK (status IN ('created', 'assigned', 'in_progress', ...));
```

---

## 5. Row-Level Security (RLS)

### Enable RLS

```sql
-- Enable RLS on table
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;

-- Create policy
CREATE POLICY tenant_isolation_policy ON work_orders
USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

### Set Tenant Context

```sql
-- In Python before query
SET app.tenant_id = 'tenant-uuid';

-- All queries automatically filter by tenant
SELECT * FROM work_orders;  -- Only returns user's tenant
```

---

## 6. Common Queries

### Pagination

```sql
-- Offset-based
SELECT * FROM work_orders
ORDER BY opened_at DESC
LIMIT 20 OFFSET 0;

-- Cursor-based (better performance)
SELECT * FROM work_orders
WHERE opened_at < 'cursor-timestamp'
ORDER BY opened_at DESC
LIMIT 20;
```

### Joins

```sql
-- Join with related tables
SELECT 
    wo.*,
    c.legal_name AS client_name,
    s.name AS site_name,
    u.full_name AS assignee_name
FROM work_orders wo
JOIN clients c ON wo.client_id = c.id
JOIN sites s ON wo.site_id = s.id
LEFT JOIN users u ON wo.assignee_user_id = u.id
WHERE wo.tenant_id = 'tenant-uuid'
ORDER BY wo.opened_at DESC
LIMIT 20;
```

### Aggregation

```sql
-- Count by status
SELECT status, COUNT(*) 
FROM work_orders 
WHERE tenant_id = 'tenant-uuid'
GROUP BY status;

-- Sum invoices by client
SELECT 
    c.legal_name,
    SUM(i.total_sar) AS total
FROM invoices i
JOIN clients c ON i.client_id = c.id
WHERE i.tenant_id = 'tenant-uuid'
GROUP BY c.id
ORDER BY total DESC;
```

---

## 7. Migrations with Alembic

### Create Migration

```bash
# Generate migration
alembic revision --autogenerate -m "add new field"

# Edit migration file
```

### Migration Template

```python
# migrations/versions/abc123_add_field.py
"""add new field

Revision ID: abc123
Revises: previous_revision
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'abc123'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add column
    op.add_column(
        'work_orders',
        sa.Column('new_field', sa.String(64), nullable=True)
    )

def downgrade():
    op.drop_column('work_orders', 'new_field')
```

### Run Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one
alembic downgrade -1

# Check current
alembic current
```

---

## 8. Practice Exercises

### Exercise 1: Write a Query

Get all open work orders for a tenant with client and site info:

```sql
SELECT 
    wo.id,
    wo.title,
    wo.status,
    wo.urgency,
    c.legal_name AS client,
    s.name AS site,
    u.full_name AS assignee
FROM work_orders wo
JOIN clients c ON wo.client_id = c.id
JOIN sites s ON wo.site_id = s.id
LEFT JOIN users u ON wo.assignee_user_id = u.id
WHERE wo.tenant_id = 'tenant-uuid'
  AND wo.status IN ('created', 'assigned', 'in_progress')
ORDER BY 
    CASE wo.urgency
        WHEN 'emergency' THEN 1
        WHEN 'urgent' THEN 2
        ELSE 3
    END,
    wo.opened_at DESC
LIMIT 50;
```

### Exercise 2: Create an Index

Create an index for efficient filtering by status:

```sql
CREATE INDEX ix_wo_status_tenant 
ON work_orders(status, tenant_id)
WHERE status NOT IN ('closed', 'cancelled');
```

---

## References

- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [FMS Database](backend/app/database.py)
- [FMS Migrations](backend/migrations/)