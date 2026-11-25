# Load libraries
import json
import logging
import os
import tempfile
import zlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_checking_fic_ids: set[int] = set()
_bulk_check_running = False


# Returns the current update check status
def get_update_check_status() -> dict:
    return {
        "bulk_running": _bulk_check_running,
        "checking_fic_ids": list(_checking_fic_ids),
    }


# Returns True if an update check can be started for the given fic
def can_check_fic(fic_id: int) -> bool:
    return not _bulk_check_running and fic_id not in _checking_fic_ids


# Returns True if a bulk update check can be started
def can_check_bulk() -> bool:
    return not _bulk_check_running and len(_checking_fic_ids) == 0

from backend.core.utils import utcnow
from backend.downloader.fanficfare_wrapper import update_fic
from backend.downloader.html_generator import save_chapters_as_html
from backend.models.chapter_version import ChapterVersion
from backend.models.fic import Chapter, Fic
from backend.models.settings import Settings
from backend.models.source import Source
from backend.services import fts_service
from backend.services.notification_service import create_notification
from backend.services.source_service import get_source_auth_data

logger = logging.getLogger(__name__)


# Checks a single fic for updates and applies them if found
async def check_fic_updates(db: AsyncSession, fic_id: int) -> dict:
    fic_result = await db.execute(select(Fic).where(Fic.id == fic_id))
    fic = fic_result.scalar_one_or_none()

    if fic is None:
        raise ValueError("Fic not found")

    if not fic.epub_path or not os.path.exists(fic.epub_path):
        return {"fic_id": fic_id, "has_updates": False, "error": "No EPUB file found"}

    source_result = await db.execute(
        select(Source).where(Source.site_key == fic.source_site)
    )
    source = source_result.scalar_one_or_none()

    auth_data = None
    auth_type = "none"
    delay_ms = 2000

    if source:
        auth_type = source.auth_type or "none"

        if source.auth_data_encrypted:
            auth_data = await get_source_auth_data(db, source.id)

        if source.rate_limit_config:
            rl = json.loads(source.rate_limit_config)
            delay_ms = rl.get("delay_ms", 2000)

    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = settings_result.scalar_one_or_none()

    if not settings_row or not settings_row.storage_path:
        return {"fic_id": fic_id, "has_updates": False, "error": "Storage not configured"}

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await update_fic(
            url=fic.source_url,
            existing_epub=fic.epub_path,
            output_dir=tmpdir,
            site_key=fic.source_site,
            auth_data=auth_data,
            auth_type=auth_type,
            delay_ms=delay_ms,
        )

        if not result.success:
            if "404" in (result.error or "") or "403" in (result.error or ""):
                fic.is_source_available = False
                await db.flush()

                await create_notification(
                    db, type="fic_unavailable",
                    title="Fic Unavailable",
                    message=f'"{fic.title}" is no longer available at the source.',
                    severity="warning",
                    related_fic_id=fic.id,
                )

                return {"fic_id": fic_id, "has_updates": False, "source_unavailable": True}

            is_rate_limited = "429" in (result.error or "") or "rate limit" in (result.error or "").lower()

            await create_notification(
                db, type="sync_failed",
                title="Update Check Failed",
                message=f'Could not check "{fic.title}" for updates: {result.error}',
                severity="warning" if is_rate_limited else "error",
                related_fic_id=fic.id,
            )

            return {"fic_id": fic_id, "has_updates": False, "error": result.error}

        if not result.has_updates:
            fic.date_last_synced = utcnow()
            await db.flush()

            return {"fic_id": fic_id, "has_updates": False}

        await _apply_update(db, fic, result, settings_row.storage_path)

    return {"fic_id": fic_id, "has_updates": True}


# Applies a downloaded update to an existing fic
async def _apply_update(db, fic, update_result, storage_path) -> None:
    existing_chapters = await db.execute(
        select(Chapter).where(Chapter.fic_id == fic.id).order_by(Chapter.chapter_number)
    )
    existing = {c.chapter_number: c for c in existing_chapters.scalars().all()}

    for ch_data in update_result.new_chapters:
        ch_num = ch_data["chapter_number"]
        old_chapter = existing.get(ch_num)

        if old_chapter and old_chapter.html_path and os.path.exists(old_chapter.html_path):
            with open(old_chapter.html_path, "r", encoding="utf-8") as f:
                old_content = f.read()

            if old_content.strip():
                compressed = zlib.compress(old_content.encode("utf-8"), level=9)
                version = ChapterVersion(
                    chapter_id=old_chapter.id,
                    content=compressed,
                    version_date=utcnow(),
                    word_count=old_chapter.word_count,
                )
                db.add(version)

    html_dir = os.path.join(
        storage_path, "fics_html", fic.source_site, fic.source_id
    )
    chapter_paths = save_chapters_as_html(update_result.new_chapters, html_dir)

    import re
    strip_tags = re.compile(r"<[^>]+>")

    for i, ch_data in enumerate(update_result.new_chapters):
        ch_num = ch_data["chapter_number"]
        old_chapter = existing.get(ch_num)

        if old_chapter:
            old_chapter.title = ch_data.get("title")
            old_chapter.html_path = chapter_paths[i] if i < len(chapter_paths) else old_chapter.html_path
            old_chapter.word_count = ch_data.get("word_count")

            plain_text = strip_tags.sub(" ", ch_data.get("html_content", ""))
            await fts_service.index_chapter(
                db, fic.id, old_chapter.id, ch_data.get("title", ""), plain_text
            )
            
        else:
            new_chapter = Chapter(
                fic_id=fic.id,
                chapter_number=ch_num,
                title=ch_data.get("title"),
                html_path=chapter_paths[i] if i < len(chapter_paths) else None,
                word_count=ch_data.get("word_count"),
            )
            db.add(new_chapter)
            await db.flush()

            plain_text = strip_tags.sub(" ", ch_data.get("html_content", ""))
            await fts_service.index_chapter(
                db, fic.id, new_chapter.id, ch_data.get("title", ""), plain_text
            )

    metadata = update_result.metadata
    fic.chapter_count = len(update_result.new_chapters)
    fic.word_count = int(metadata.get("numWords", 0)) or fic.word_count
    fic.is_complete = metadata.get("status", "").lower() in ("complete", "completed")
    fic.date_last_synced = utcnow()
    fic.is_source_available = True

    if update_result.epub_path and os.path.exists(update_result.epub_path):
        import shutil

        if fic.epub_path:
            os.makedirs(os.path.dirname(fic.epub_path), exist_ok=True)
            shutil.copy2(update_result.epub_path, fic.epub_path)

    await db.flush()

    await create_notification(
        db, type="fic_updated",
        title="Fic Updated",
        message=f'"{fic.title}" has been updated with new content.',
        severity="info",
        related_fic_id=fic.id,
    )


# Checks all fics for updates
async def check_all_fic_updates(
    db: AsyncSession, source_site: str | None = None
) -> dict:
    query = select(Fic).where(Fic.is_source_available == True)  # noqa: E712

    if source_site:
        query = query.where(Fic.source_site == source_site)

    result = await db.execute(query)
    fics = result.scalars().all()

    total_checked = 0
    total_updated = 0
    total_unavailable = 0

    for fic in fics:
        try:
            update_result = await check_fic_updates(db, fic.id)
            total_checked += 1

            if update_result.get("has_updates"):
                total_updated += 1

            if update_result.get("source_unavailable"):
                total_unavailable += 1

        except Exception:
            logger.exception("Error checking updates for fic %d", fic.id)

    return {
        "total_checked": total_checked,
        "total_updated": total_updated,
        "total_unavailable": total_unavailable,
    }


# Returns the version history for a chapter
async def get_chapter_versions(db: AsyncSession, chapter_id: int) -> list[dict]:
    result = await db.execute(
        select(ChapterVersion)
        .where(ChapterVersion.chapter_id == chapter_id)
        .order_by(ChapterVersion.version_date.desc())
    )
    versions = result.scalars().all()

    return [
        {
            "id": v.id,
            "chapter_id": v.chapter_id,
            "version_date": v.version_date.isoformat() if v.version_date else None,
            "word_count": v.word_count,
        }
        for v in versions
    ]


# Decompresses and returns a specific version's content
async def get_chapter_version_content(db: AsyncSession, version_id: int) -> str:
    result = await db.execute(
        select(ChapterVersion).where(ChapterVersion.id == version_id)
    )
    version = result.scalar_one_or_none()

    if version is None:
        raise ValueError("Version not found")

    return zlib.decompress(version.content).decode("utf-8")
