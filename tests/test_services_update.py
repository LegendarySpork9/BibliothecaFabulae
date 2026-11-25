# Load libraries
import zlib

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.utils import utcnow
from backend.models.chapter_version import ChapterVersion
from backend.models.fic import Chapter, Fic
from backend.services.update_service import (
    can_check_bulk,
    can_check_fic,
    get_chapter_version_content,
    get_chapter_versions,
    get_update_check_status,
)


# Test that the initial status shows nothing running
@pytest.mark.asyncio
async def test_get_update_check_status_initial():
    status = get_update_check_status()

    assert status["bulk_running"] is False
    assert status["checking_fic_ids"] == []


# Test that can_check_fic returns True when nothing is running
@pytest.mark.asyncio
async def test_can_check_fic_true():
    assert can_check_fic(1) is True


# Test that can_check_bulk returns True when nothing is running
@pytest.mark.asyncio
async def test_can_check_bulk_true():
    assert can_check_bulk() is True


# Test that get_chapter_versions returns an empty list for a chapter with no versions
@pytest.mark.asyncio
async def test_get_chapter_versions_empty(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3",
        source_id="999",
        source_url="https://archiveofourown.org/works/999",
        title="Test Fic",
        import_method="url",
    )
    db_session.add(fic)
    await db_session.flush()

    chapter = Chapter(
        fic_id=fic.id,
        chapter_number=1,
        title="Chapter 1",
    )
    db_session.add(chapter)
    await db_session.flush()

    versions = await get_chapter_versions(db_session, chapter.id)

    assert versions == []


# Test that a compressed ChapterVersion can be created and its content retrieved
@pytest.mark.asyncio
async def test_get_chapter_version_content(db_session: AsyncSession):
    fic = Fic(
        source_site="ao3",
        source_id="888",
        source_url="https://archiveofourown.org/works/888",
        title="Versioned Fic",
        import_method="url",
    )
    db_session.add(fic)
    await db_session.flush()

    chapter = Chapter(
        fic_id=fic.id,
        chapter_number=1,
        title="Chapter 1",
    )
    db_session.add(chapter)
    await db_session.flush()

    original_html = "<p>This is the original chapter content.</p>"
    compressed = zlib.compress(original_html.encode("utf-8"), level=9)

    version = ChapterVersion(
        chapter_id=chapter.id,
        content=compressed,
        version_date=utcnow(),
        word_count=7,
    )
    db_session.add(version)
    await db_session.flush()

    # Verify get_chapter_versions returns the version metadata
    versions = await get_chapter_versions(db_session, chapter.id)

    assert len(versions) == 1
    assert versions[0]["id"] == version.id
    assert versions[0]["chapter_id"] == chapter.id
    assert versions[0]["word_count"] == 7

    # Verify get_chapter_version_content decompresses correctly
    content = await get_chapter_version_content(db_session, version.id)

    assert content == original_html


# Test that get_chapter_version_content raises ValueError for a nonexistent version
@pytest.mark.asyncio
async def test_get_chapter_version_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Version not found"):
        await get_chapter_version_content(db_session, 99999)
