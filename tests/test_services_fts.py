# Load libraries
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.fts_service import index_chapter, remove_fic_index, search


@pytest.mark.asyncio
async def test_index_and_search(db_session: AsyncSession):
    await index_chapter(db_session, 1, 10, "Chapter One", "The hero walked into the dark forest")
    await index_chapter(db_session, 1, 11, "Chapter Two", "The villain appeared from the shadows")
    await db_session.flush()

    results = await search(db_session, "dark forest")

    assert len(results) == 1
    assert results[0]["fic_id"] == 1
    assert results[0]["chapter_id"] == 10


@pytest.mark.asyncio
async def test_search_multiple_results(db_session: AsyncSession):
    await index_chapter(db_session, 1, 10, "Ch1", "The magic sword gleamed")
    await index_chapter(db_session, 2, 20, "Ch1", "The ancient magic awakened")
    await db_session.flush()

    results = await search(db_session, "magic")

    assert len(results) == 2


@pytest.mark.asyncio
async def test_remove_fic_index(db_session: AsyncSession):
    await index_chapter(db_session, 1, 10, "Ch1", "Content for fic one")
    await index_chapter(db_session, 1, 11, "Ch2", "More content for fic one")
    await index_chapter(db_session, 2, 20, "Ch1", "Content for fic two")
    await db_session.flush()

    await remove_fic_index(db_session, 1)
    await db_session.flush()

    results = await search(db_session, "content")

    assert len(results) == 1
    assert results[0]["fic_id"] == 2


@pytest.mark.asyncio
async def test_search_no_results(db_session: AsyncSession):
    await index_chapter(db_session, 1, 10, "Ch1", "Nothing relevant here")
    await db_session.flush()

    results = await search(db_session, "xyznonexistent")

    assert len(results) == 0


@pytest.mark.asyncio
async def test_index_chapter_updates(db_session: AsyncSession):
    await index_chapter(db_session, 1, 10, "Ch1", "Original content about dragons")
    await db_session.flush()

    await index_chapter(db_session, 1, 10, "Ch1", "Updated content about wizards")
    await db_session.flush()

    dragon_results = await search(db_session, "dragons")
    wizard_results = await search(db_session, "wizards")

    assert len(dragon_results) == 0
    assert len(wizard_results) == 1
