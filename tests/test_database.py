# Load libraries
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# Test that all expected tables exist after migration
@pytest.mark.asyncio
async def test_tables_created(db_session: AsyncSession):
    result = await db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    )
    tables = {row[0] for row in result.fetchall()}
    assert "users" in tables
    assert "settings" in tables
    assert "notifications" in tables
    assert "notification_preferences" in tables
    assert "refresh_tokens" in tables
