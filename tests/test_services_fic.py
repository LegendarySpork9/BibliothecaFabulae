# Load libraries
import os
import tempfile

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.downloader.fanficfare_wrapper import DownloadResult
from backend.models.fic import Fic
from backend.models.settings import Settings
from backend.services.fic_service import (
    delete_fic,
    get_fic,
    get_fic_chapters,
    get_fics,
    store_downloaded_fic,
)


async def _setup_storage(db: AsyncSession, path: str) -> None:
    settings = Settings(id=1, storage_path=path, setup_complete=True)
    db.add(settings)
    await db.flush()


def _make_download_result(tmpdir: str) -> DownloadResult:
    epub_path = os.path.join(tmpdir, "test.epub")

    with open(epub_path, "w") as f:
        f.write("fake epub")

    return DownloadResult(
        epub_path=epub_path,
        metadata={
            "title": "Test Story",
            "description": "A test summary",
            "language": "en",
            "rating": "Teen And Up",
            "numWords": "5000",
            "status": "Complete",
            "creators": ["Author One", "Author Two"],
            "fandoms": ["Marvel (Comics)"],
            "ships": ["Character A/Character B"],
            "characters": ["Character A", "Character B"],
            "freeformtags": ["Fantasy", "Adventure"],
        },
        chapters=[
            {
                "chapter_number": 1,
                "title": "The Beginning",
                "html_content": "<p>Once upon a time there was a hero.</p>",
                "word_count": 8,
            },
            {
                "chapter_number": 2,
                "title": "The End",
                "html_content": "<p>And they lived happily ever after.</p>",
                "word_count": 7,
            },
        ],
    )


@pytest.mark.asyncio
async def test_store_downloaded_fic(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        result = _make_download_result(tmpdir)
        fic = await store_downloaded_fic(
            db_session, result, "ao3", "12345",
            "https://archiveofourown.org/works/12345", "manual_url",
        )

        assert fic.title == "Test Story"
        assert fic.word_count == 5000
        assert fic.chapter_count == 2
        assert fic.is_complete is True
        assert fic.import_method == "manual_url"
        assert fic.html_path is not None
        assert fic.epub_path is not None
        assert os.path.isdir(fic.html_path)


@pytest.mark.asyncio
async def test_store_downloaded_fic_duplicate(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        result = _make_download_result(tmpdir)
        await store_downloaded_fic(
            db_session, result, "ao3", "12345",
            "https://archiveofourown.org/works/12345", "manual_url",
        )

        with pytest.raises(ValueError, match="already archived"):
            await store_downloaded_fic(
                db_session, result, "ao3", "12345",
                "https://archiveofourown.org/works/12345", "manual_url",
            )


@pytest.mark.asyncio
async def test_get_fic_detail(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        result = _make_download_result(tmpdir)
        fic = await store_downloaded_fic(
            db_session, result, "ao3", "12345",
            "https://archiveofourown.org/works/12345", "manual_url",
        )

        detail = await get_fic(db_session, fic.id)

        assert detail["title"] == "Test Story"
        assert len(detail["authors"]) == 2
        assert len(detail["fandoms"]) == 1
        assert len(detail["relationships"]) == 1
        assert len(detail["characters"]) == 2
        assert len(detail["tags"]) == 2
        assert len(detail["chapters"]) == 2


@pytest.mark.asyncio
async def test_get_fic_not_found(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Fic not found"):
        await get_fic(db_session, 9999)


@pytest.mark.asyncio
async def test_get_fics_paginated(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        for i in range(3):
            epub_path = os.path.join(tmpdir, f"test{i}.epub")

            with open(epub_path, "w") as f:
                f.write("fake")

            result = DownloadResult(
                epub_path=epub_path,
                metadata={"title": f"Story {i}", "creators": [], "subjects": []},
                chapters=[{"chapter_number": 1, "title": "Ch1",
                           "html_content": f"<p>Content {i}</p>", "word_count": 2}],
            )
            await store_downloaded_fic(
                db_session, result, "ao3", str(i),
                f"https://archiveofourown.org/works/{i}", "manual_url",
            )

        fics = await get_fics(db_session, limit=2, offset=0)

        assert fics["total"] == 3
        assert len(fics["items"]) == 2


@pytest.mark.asyncio
async def test_get_fic_chapters(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        result = _make_download_result(tmpdir)
        fic = await store_downloaded_fic(
            db_session, result, "ao3", "12345",
            "https://archiveofourown.org/works/12345", "manual_url",
        )

        chapters = await get_fic_chapters(db_session, fic.id)

        assert len(chapters) == 2
        assert chapters[0]["title"] == "The Beginning"
        assert chapters[1]["title"] == "The End"


@pytest.mark.asyncio
async def test_delete_fic(db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        await _setup_storage(db_session, storage_dir)

        result = _make_download_result(tmpdir)
        fic = await store_downloaded_fic(
            db_session, result, "ao3", "12345",
            "https://archiveofourown.org/works/12345", "manual_url",
        )

        delete_result = await delete_fic(db_session, fic.id)
        assert delete_result["success"] is True

        db_result = await db_session.execute(select(Fic).where(Fic.id == fic.id))
        assert db_result.scalar_one_or_none() is None
