# Load libraries
import asyncio
import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.downloader.fanficfare_wrapper import download_fic
from backend.models.fic import Fic
from backend.models.settings import Settings
from backend.models.source import BookmarkSyncState, Source
from backend.services.download_job_service import create_job, update_job_status
from backend.services.fic_service import store_downloaded_fic
from backend.services.notification_service import create_notification
from backend.services.source_service import get_source_auth_data

logger = logging.getLogger(__name__)


# Tracks aggregate results of a bookshelf sync operation
@dataclass
class SyncResult:
    total_found: int = 0
    total_new: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


# Fetches story URLs from a Fimfiction bookshelf using FanFicFare
def _fetch_fimfiction_bookshelf_sync(bookshelf_url: str, delay_ms: int, cookies: str | None = None) -> list[dict]:
    ini_lines = [
        "[defaults]",
        f"slow_down_sleep_time={delay_ms / 1000:.1f}",
        "is_adult=true",
        "scrape_bookshelf=true",
    ]

    if cookies:
        ini_lines.append(f"cookie={cookies}")
        ini_lines.append("use_cloudscraper=true")

    from backend.core.config import settings as app_settings

    if app_settings.FLARESOLVERR_URL:
        from urllib.parse import urlparse

        parsed = urlparse(app_settings.FLARESOLVERR_URL)
        ini_lines.append("use_flaresolverr_proxy=true")
        ini_lines.append(f"flaresolverr_proxy_address={parsed.hostname or 'localhost'}")
        ini_lines.append(f"flaresolverr_proxy_port={parsed.port or 8191}")
        ini_lines.append("flaresolverr_proxy_timeout=59000")

    ini_content = "\n".join(ini_lines) + "\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(ini_content)
        ini_path = f.name

    try:
        result = subprocess.run(
            ["fanficfare", "--non-interactive", "--config", ini_path,
             "--normalize-list", bookshelf_url],
            capture_output=True, text=True, timeout=300,
        )

    finally:
        import os

        os.remove(ini_path)

    if result.returncode != 0:
        raise RuntimeError(f"FanFicFare list failed: {result.stderr or result.stdout}")

    urls = []

    for line in result.stdout.strip().splitlines():
        line = line.strip()

        if not line:
            continue

        match = re.search(r"fimfiction\.net/story/(\d+)", line)

        if match:
            urls.append({"url": line, "story_id": match.group(1)})

    return urls


# Performs a Fimfiction bookshelf sync
async def sync_fimfiction_bookshelf(db: AsyncSession, source_id: int) -> SyncResult:
    return await _sync_via_fanficfare_list(
        db, source_id,
        site_key="fimfiction",
        display_name="Fimfiction",
        url_pattern=r"fimfiction\.net/story/(\d+)",
        fetch_fn=_fetch_fimfiction_bookshelf_sync,
        auth_field="bookshelf_url",
        auth_help='{"bookshelf_url": "https://www.fimfiction.net/bookshelf/YOUR_ID/name"}',
    )


# Generic sync using FanFicFare --normalize-list for any site
async def _sync_via_fanficfare_list(
    db: AsyncSession,
    source_id: int,
    site_key: str,
    display_name: str,
    url_pattern: str,
    fetch_fn,
    auth_field: str,
    auth_help: str,
) -> SyncResult:
    result = SyncResult()

    source_row = await db.execute(select(Source).where(Source.id == source_id))
    source = source_row.scalar_one_or_none()

    if source is None or source.site_key != site_key:
        result.success = False
        result.errors.append(f"{display_name} source not found")

        return result

    if not source.is_enabled:
        result.success = False
        result.errors.append(f"{display_name} source is disabled")

        return result

    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = settings_result.scalar_one_or_none()

    if not settings_row or not settings_row.storage_path:
        result.success = False
        result.errors.append("Storage path not configured")

        return result

    rl_config = json.loads(source.rate_limit_config) if source.rate_limit_config else {}
    delay_ms = rl_config.get("delay_ms", 5000)

    config_data = None
    auth_cookies = None
    list_url = None

    if source.config_data_encrypted:
        from backend.services.source_service import get_source_config_data
        config_data = await get_source_config_data(db, source_id)

    if source.auth_data_encrypted and source.auth_type == "cookies":
        auth_cookies = await get_source_auth_data(db, source_id)

    if config_data:
        try:
            config = json.loads(config_data)
            list_url = config.get(auth_field, "").strip()

        except (json.JSONDecodeError, AttributeError):
            pass

    if not list_url:
        result.success = False
        result.errors.append(f"No {display_name} list URL configured. Set auth data to: {auth_help}")

        await create_notification(
            db, type="sync_failed",
            title=f"{display_name} Sync Failed",
            message=f"No list URL configured. Update your {display_name} auth settings.",
            severity="error",
        )

        return result

    sync_state = await _get_or_create_sync_state(db, site_key)
    sync_state.sync_status = "syncing"
    sync_state.sync_progress_current = 0
    sync_state.sync_progress_total = None
    sync_state.sync_message = f"Fetching list from {display_name}..."
    await db.flush()
    await db.commit()

    try:
        stories = await asyncio.to_thread(fetch_fn, list_url, delay_ms, auth_cookies)
        result.total_found = len(stories)

        sync_state.sync_progress_total = result.total_found
        sync_state.sync_message = f"Found {result.total_found} stories"
        await db.flush()
        await db.commit()

        to_download = []

        for story in stories:
            work_url = story.get("url", "")
            work_id = story.get("story_id", "")

            if not work_url or not work_id:
                continue

            existing = await db.execute(
                select(Fic).where(Fic.source_site == site_key, Fic.source_id == work_id)
            )

            if existing.scalar_one_or_none() is not None:
                result.total_skipped += 1
                continue

            to_download.append(story)

        sync_state.sync_message = f"Downloading {len(to_download)} new stories ({result.total_skipped} already archived)"
        await db.flush()
        await db.commit()

        from backend.downloader.parallel import download_fics_sequential

        # Updates sync state progress after each fic is processed
        async def _on_progress(processed, new, failed):
            sync_state.sync_progress_current = result.total_skipped + processed
            sync_state.sync_message = f"Downloading {processed}/{len(to_download)} — {new} complete, {failed} failed"
            await db.flush()
            await db.commit()

        dl_result = await download_fics_sequential(
            db, to_download, site_key=site_key, source_id=source_id,
            auth_data=auth_cookies, auth_type="cookies" if auth_cookies else "none",
            delay_ms=delay_ms, on_progress=_on_progress,
        )

        result.total_new = dl_result["total_new"]
        result.total_failed = dl_result["total_failed"]
        result.errors.extend(dl_result["errors"])

        from backend.core.utils import utcnow

        sync_state.total_bookmarks = result.total_found
        sync_state.total_synced += result.total_new
        sync_state.last_synced = utcnow()
        sync_state.sync_status = "idle"
        sync_state.sync_message = f"Complete: {result.total_new} new, {result.total_skipped} skipped, {result.total_failed} failed"

        await db.flush()

        await create_notification(
            db, type="sync_complete",
            title=f"{display_name} Sync Complete",
            message=f"Found {result.total_found}: {result.total_new} new, {result.total_skipped} already archived.",
            severity="success",
        )

    except Exception as e:
        logger.exception("%s sync failed", display_name)
        result.success = False
        result.errors.append(str(e))

        sync_state.sync_status = "failed"
        sync_state.sync_message = str(e)
        await db.flush()

        await create_notification(
            db, type="sync_failed",
            title=f"{display_name} Sync Failed",
            message=str(e),
            severity="error",
        )

    return result


# Gets or creates a BookmarkSyncState for a site
async def _get_or_create_sync_state(db: AsyncSession, source_site: str) -> BookmarkSyncState:
    result = await db.execute(
        select(BookmarkSyncState).where(BookmarkSyncState.source_site == source_site)
    )
    state = result.scalar_one_or_none()

    if state is None:
        state = BookmarkSyncState(source_site=source_site)
        db.add(state)
        await db.flush()

    return state
