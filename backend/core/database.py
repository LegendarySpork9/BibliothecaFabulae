# Load libraries
import os
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import settings

os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")) or ".", exist_ok=True)

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Enables WAL mode and foreign keys on each SQLite connection
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Yields an async database session with automatic commit and rollback
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise


# Creates all database tables from registered models
async def init_db() -> None:
    from backend.models.base import Base
    import backend.models.user  # noqa: F401
    import backend.models.settings  # noqa: F401
    import backend.models.notification  # noqa: F401
    import backend.models.session  # noqa: F401
    import backend.models.fic  # noqa: F401
    import backend.models.chapter_version  # noqa: F401
    import backend.models.author  # noqa: F401
    import backend.models.fandom  # noqa: F401
    import backend.models.tag  # noqa: F401
    import backend.models.relationship  # noqa: F401
    import backend.models.character  # noqa: F401
    import backend.models.source  # noqa: F401
    import backend.models.download_job  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
