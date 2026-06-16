import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add parent directory to path so 'app' module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, _normalize_sync_database_url
from app.models import *
from app.config import get_settings

# this is necessary for alembic to see the models
target_metadata = Base.metadata

config = context.config

if config.get_main_option("script_location") is None:
    config.set_main_option("script_location", context.get_context().config_file_name)

fileConfig(config.config_file_name)


def _database_url() -> str:
    return _normalize_sync_database_url(get_settings().database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
