# Load libraries
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.source import Source
from backend.services.sync_service import (
    clear_sync_cancel,
    is_sync_cancelled,
    request_sync_cancel,
    run_bookmark_sync,
)


# Test the full lifecycle of the cancel flag: set, check, clear
@pytest.mark.asyncio
async def test_cancel_flag_lifecycle():
    request_sync_cancel("test_site")

    assert is_sync_cancelled("test_site") is True

    clear_sync_cancel("test_site")

    assert is_sync_cancelled("test_site") is False


# Test that is_sync_cancelled returns False for a site that was never flagged
@pytest.mark.asyncio
async def test_is_sync_cancelled_default():
    assert is_sync_cancelled("unknown_site_xyz") is False


# Test that run_bookmark_sync raises ValueError when the source does not exist
@pytest.mark.asyncio
async def test_run_bookmark_sync_source_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Source not found"):
        await run_bookmark_sync(db_session, source_id=99999)


# Test that run_bookmark_sync raises ValueError when the source is disabled
@pytest.mark.asyncio
async def test_run_bookmark_sync_disabled(db_session: AsyncSession):
    source = Source(
        site_key="ao3",
        is_enabled=False,
        auth_type="none",
        auth_status="ok",
    )
    db_session.add(source)
    await db_session.flush()

    with pytest.raises(ValueError, match="disabled"):
        await run_bookmark_sync(db_session, source_id=source.id)


# Test that run_bookmark_sync raises ValueError when auth has expired
@pytest.mark.asyncio
async def test_run_bookmark_sync_expired_auth(db_session: AsyncSession):
    source = Source(
        site_key="ffnet",
        is_enabled=True,
        auth_type="cookie",
        auth_status="expired",
    )
    db_session.add(source)
    await db_session.flush()

    with pytest.raises(ValueError, match="expired authentication"):
        await run_bookmark_sync(db_session, source_id=source.id)
