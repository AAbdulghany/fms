-- Run against existing PostgreSQL DB if tables were created before this feature.
-- New installs get these columns from SQLAlchemy metadata.create_all / fresh deploys.

ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_tenant_username ON users (tenant_id, username)
  WHERE username IS NOT NULL;

ALTER TABLE clients ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'active';
