# Load libraries
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

import backend.models.notification  # noqa: F401
import backend.models.session  # noqa: F401
import backend.models.settings  # noqa: F401
import backend.models.user  # noqa: F401
import backend.models.fic  # noqa: F401
import backend.models.chapter_version  # noqa: F401
import backend.models.author  # noqa: F401
import backend.models.fandom  # noqa: F401
import backend.models.tag  # noqa: F401
import backend.models.relationship  # noqa: F401
import backend.models.character  # noqa: F401
import backend.models.source  # noqa: F401
import backend.models.download_job  # noqa: F401
from backend.core.config import settings
from backend.models.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite+aiosqlite"),
)

target_metadata = Base.metadata


# Runs migrations without a live database connection
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# Executes migrations using the provided database connection
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


# Creates an async engine and runs migrations
async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# Runs migrations with a live async database connection
def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
    
else:
    run_migrations_online()
