# Load libraries
import asyncio
import json
import logging
import tempfile
import time
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.fic import Fic
from backend.models.settings import Settings
from backend.models.source import BookmarkSyncState, Source
from backend.services.notification_service import create_notification
from backend.services.source_service import get_source_auth_data

logger = logging.getLogger(__name__)


# Tracks aggregate results of a bookmark sync operation
@dataclass
class SyncResult:
    total_found: int = 0
    total_new: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


# Performs a full AO3 bookmark sync for a configured source
async def sync_ao3_bookmarks(db: AsyncSession, source_id: int) -> SyncResult:
    result = SyncResult()

    source_row = await db.execute(select(Source).where(Source.id == source_id))
    source = source_row.scalar_one_or_none()

    if source is None or source.site_key != "ao3":
        result.success = False
        result.errors.append("AO3 source not found")

        return result

    if not source.is_enabled:
        result.success = False
        result.errors.append("AO3 source is disabled")

        return result

    auth_data = await get_source_auth_data(db, source_id)

    if not auth_data:
        source.auth_status = "expired"
        await db.flush()

        await create_notification(
            db, type="auth_required",
            title="AO3 Authentication Required",
            message="AO3 credentials are not configured. Please update your auth settings.",
            severity="warning",
        )
        result.success = False
        result.errors.append("No auth data configured")

        return result

    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = settings_result.scalar_one_or_none()

    if not settings_row or not settings_row.storage_path:
        result.success = False
        result.errors.append("Storage path not configured")

        return result

    rl_config = json.loads(source.rate_limit_config) if source.rate_limit_config else {}
    delay_ms = rl_config.get("delay_ms", 5000)

    sync_state = await _get_or_create_sync_state(db, "ao3")
    sync_state.sync_status = "syncing"
    sync_state.sync_progress_current = 0
    sync_state.sync_progress_total = None
    sync_state.sync_message = "Fetching bookmarks from AO3..."
    await db.flush()
    await db.commit()

    try:
        bookmarks = await asyncio.to_thread(
            _fetch_ao3_bookmarks_sync,
            auth_data, source.auth_type, delay_ms,
        )
        result.total_found = len(bookmarks)

        sync_state.sync_progress_total = result.total_found
        sync_state.sync_message = f"Found {result.total_found} bookmarks"
        await db.flush()
        await db.commit()

        for i, bookmark in enumerate(bookmarks):
            from backend.services.sync_service import is_sync_cancelled

            if is_sync_cancelled("ao3"):
                sync_state.sync_status = "idle"
                sync_state.sync_message = f"Cancelled — {result.total_new} new, {result.total_skipped} skipped"
                await db.flush()
                await db.commit()
                break

            work_url = bookmark.get("url", "")
            work_id = bookmark.get("work_id", "")

            if not work_url or not work_id:
                continue

            existing = await db.execute(
                select(Fic).where(Fic.source_site == "ao3", Fic.source_id == work_id)
            )

            if existing.scalar_one_or_none() is not None:
                result.total_skipped += 1
                sync_state.sync_progress_current = i + 1

                if (i + 1) % 5 == 0:
                    sync_state.sync_message = f"Processing {i + 1}/{result.total_found} — {result.total_new} new, {result.total_skipped} skipped"
                    await db.flush()
                    await db.commit()

                continue

            from backend.services.download_job_service import create_job, update_job_status

            job = await create_job(db, work_url, source_site="ao3", source_id=work_id)
            await db.flush()
            await db.commit()

            try:
                await update_job_status(db, job.id, "downloading", f"Downloading {work_url}")
                await db.flush()
                await db.commit()

                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    from backend.downloader.fanficfare_wrapper import download_fic
                    from backend.services.fic_service import store_downloaded_fic

                    dl_result = await download_fic(
                        url=work_url, output_dir=tmpdir,
                        site_key="ao3", auth_data=auth_data,
                        auth_type=source.auth_type, delay_ms=delay_ms,
                    )

                    if dl_result.success:
                        fic = await store_downloaded_fic(
                            db, dl_result, "ao3", work_id, work_url, "bookmark_sync",
                        )
                        await update_job_status(
                            db, job.id, "complete", "Import complete",
                            fic_title=fic.title, fic_id=fic.id,
                        )
                        result.total_new += 1

                    else:
                        await update_job_status(
                            db, job.id, "failed", dl_result.error or "Download failed",
                        )
                        result.total_failed += 1
                        result.errors.append(f"Failed: {work_url}: {dl_result.error}")

            except Exception as e:
                await update_job_status(db, job.id, "failed", str(e))
                result.total_failed += 1
                result.errors.append(f"Error: {work_url}: {str(e)}")

            sync_state.sync_progress_current = i + 1
            sync_state.sync_message = f"Processing {i + 1}/{result.total_found} — {result.total_new} new, {result.total_skipped} skipped"
            await db.flush()
            await db.commit()

        from backend.core.utils import utcnow

        sync_state.total_bookmarks = result.total_found
        sync_state.total_synced += result.total_new
        sync_state.last_synced = utcnow()
        sync_state.sync_status = "idle"
        sync_state.sync_message = f"Complete: {result.total_new} new, {result.total_skipped} skipped, {result.total_failed} failed"

        if bookmarks:
            sync_state.last_bookmark_id = bookmarks[-1].get("work_id")

        if source.auth_status != "valid":
            source.auth_status = "valid"
            source.auth_last_checked = utcnow()

        await db.flush()

        await create_notification(
            db, type="sync_complete",
            title="AO3 Bookmark Sync Complete",
            message=f"Found {result.total_found} bookmarks: {result.total_new} new, {result.total_skipped} already archived.",
            severity="success",
        )

        from backend.services.update_service import check_all_fic_updates

        await check_all_fic_updates(db, source_site="ao3")

    except Exception as e:
        logger.exception("AO3 bookmark sync failed")
        result.success = False
        result.errors.append(str(e))

        sync_state.sync_status = "failed" if "cloudflare" not in str(e).lower() else "blocked"
        sync_state.sync_message = str(e)
        await db.flush()

        await create_notification(
            db, type="sync_failed",
            title="AO3 Bookmark Sync Failed",
            message=str(e),
            severity="error",
        )

    return result


# Fetches bookmarks from AO3 using ao3-py (synchronous, run via asyncio.to_thread)
def _fetch_ao3_bookmarks_sync(
    auth_data: str, auth_type: str, delay_ms: int
) -> list[dict]:
    from ao3 import AO3Client

    cookies = None
    username = None
    password = None

    if auth_type == "credentials":
        creds = json.loads(auth_data)
        username = creds.get("username", "")
        password = creds.get("password", "")

    elif auth_type == "cookies":
        cookies = {}

        for pair in auth_data.split(";"):
            pair = pair.strip()

            if "=" in pair:
                key, _, value = pair.partition("=")
                cookies[key.strip()] = value.strip()

    with AO3Client(timeout=60, cookies=cookies) as client:
        if username and password:
            client.login(username, password)

        user = client.user(username or "me")
        bookmarks = []
        page = user.bookmarks_page

        while page:
            for bookmark in page:
                work = bookmark.bookmarkable

                if work is None:
                    continue

                work_id = str(work.id)
                bookmarks.append({
                    "work_id": work_id,
                    "url": f"https://archiveofourown.org/works/{work_id}",
                    "bookmark_tags": [t.name for t in bookmark.tags] if hasattr(bookmark, "tags") and bookmark.tags else [],
                    "private": getattr(bookmark, "private", False),
                    "recommended": getattr(bookmark, "recommended", False),
                })

            if page.page < page.page_count:
                time.sleep(delay_ms / 1000)
                page = user.copy(page=page.page + 1).bookmarks_page
                
            else:
                break

        return bookmarks


# Gets or creates a BookmarkSyncState for a site
async def _get_or_create_sync_state(
    db: AsyncSession, source_site: str
) -> BookmarkSyncState:
    result = await db.execute(
        select(BookmarkSyncState).where(BookmarkSyncState.source_site == source_site)
    )
    state = result.scalar_one_or_none()

    if state is None:
        state = BookmarkSyncState(source_site=source_site)
        db.add(state)
        await db.flush()

    return state
