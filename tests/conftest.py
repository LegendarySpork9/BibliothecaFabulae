# Load libraries
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

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
from backend.core.database import get_db
from backend.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


# Provide a fresh database session with tables created and torn down per test
@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            __import__("sqlalchemy").text(
                "CREATE VIRTUAL TABLE IF NOT EXISTS fic_content_fts USING fts5("
                "fic_id UNINDEXED, chapter_id UNINDEXED, title, content, "
                "tokenize='porter unicode61')"
            )
        )

    async with test_session() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("DROP TABLE IF EXISTS fic_content_fts")
        )
        await conn.run_sync(Base.metadata.drop_all)


# Provide an async HTTP client wired to the FastAPI app with the test database
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from backend.core.security import limiter, login_attempts
    from backend.main import app

    # Override the database dependency to use the test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    limiter.reset()
    login_attempts.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
