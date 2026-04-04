"""Alembic environment configuration for CartSnitch."""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from cartsnitch_api.models import Base  # noqa: F401 — imports all models for autogenerate

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = os.environ.get("CARTSNITCH_DATABASE_URL_SYNC")
if not db_url:
    raise RuntimeError(
        "CARTSNITCH_DATABASE_URL_SYNC must be set. "
        "Example: postgresql://user:pass@localhost:5432/cartsnitch"
    )
config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_column_width=128,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, version_table_column_width=128)
        with context.begin_transaction():
            context.run_migrations()
        # Create any tables defined in models but not yet created by migrations.
        # This bootstraps fresh databases that have no legacy schema.
        # checkfirst=True ensures this is a no-op on existing databases.
        try:
            Base.metadata.create_all(bind=connection, checkfirst=True)
            connection.commit()
        except Exception as exc:
            import logging
            logging.getLogger("alembic.env").warning(
                "create_all failed (non-fatal, migrations should handle table creation): %s", exc
            )


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
