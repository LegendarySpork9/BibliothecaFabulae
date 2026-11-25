# Load libraries
import asyncio
import json
import logging
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

logger = logging.getLogger(__name__)


# Tracks aggregate results of a favourites sync operation
@dataclass
class SyncResult:
    total_found: int = 0
    total_new: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    errors: list[str] = field(default_factory=list)
    success: bool = True


# Fetches favourite story URLs from an FFNet user profile using FanFicFare
def _fetch_ffnet_favourites_sync(profile_url: str, delay_ms: int, cookies: str | None = None) -> list[dict]:
    import os
    import re
    import subprocess
    import tempfile

    ini_lines = [
        "[defaults]",
        f"slow_down_sleep_time={delay_ms / 1000:.1f}",
        "is_adult=true",
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

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write("\n".join(ini_lines) + "\n")
        ini_path = f.name

    try:
        result = subprocess.run(
            ["fanficfare", "--non-interactive", "--config", ini_path,
             "--normalize-list", profile_url],
            capture_output=True, text=True, timeout=120,
        )

    finally:
        os.remove(ini_path)

    if result.returncode != 0:
        raise RuntimeError(f"FanFicFare list failed: {result.stderr or result.stdout}")

    urls = []

    for line in result.stdout.strip().splitlines():
        line = line.strip()

        if not line:
            continue

        match = re.search(r"fanfiction\.net/s/(\d+)", line)

        if match:
            story_id = match.group(1)
            urls.append({
                "url": line,
                "story_id": story_id,
            })

    return urls


# Performs an FFNet favourites sync for a configured source
async def sync_ffnet_favourites(db: AsyncSession, source_id: int) -> SyncResult:
    result = SyncResult()

    source_row = await db.execute(select(Source).where(Source.id == source_id))
    source = source_row.scalar_one_or_none()

    if source is None or source.site_key != "ffnet":
        result.success = False
        result.errors.append("FFNet source not found")

        return result

    if not source.is_enabled:
        result.success = False
        result.errors.append("FFNet source is disabled")

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

    if source.config_data_encrypted:
        from backend.services.source_service import get_source_config_data
        config_data = await get_source_config_data(db, source.id)

    if source.auth_data_encrypted and source.auth_type == "cookies":
        from backend.services.source_service import get_source_auth_data
        auth_cookies = await get_source_auth_data(db, source.id)

    profile_url = None

    if config_data:
        try:
            config = json.loads(config_data)
            profile_url = config.get("profile_url", "").strip()

        except (json.JSONDecodeError, AttributeError):
            pass

    if not profile_url:
        result.success = False
        result.errors.append(
            "No FFNet profile URL configured. Set auth data to: "
            '{"profile_url": "https://www.fanfiction.net/u/YOUR_ID/YOUR_NAME"}'
        )

        await create_notification(
            db, type="sync_failed",
            title="FFNet Sync Failed",
            message="No profile URL configured. Update your FFNet auth settings with your profile URL.",
            severity="error",
        )

        return result

    sync_state_result = await db.execute(
        select(BookmarkSyncState).where(BookmarkSyncState.source_site == "ffnet")
    )
    sync_state = sync_state_result.scalar_one_or_none()

    if sync_state is None:
        sync_state = BookmarkSyncState(source_site="ffnet")
        db.add(sync_state)
        await db.flush()

    sync_state.sync_status = "syncing"
    sync_state.sync_progress_current = 0
    sync_state.sync_progress_total = None
    sync_state.sync_message = "Fetching favourites from FFNet..."
    await db.flush()
    await db.commit()

    try:
        favourites = await asyncio.to_thread(
            _fetch_ffnet_favourites_sync, profile_url, delay_ms, auth_cookies,
        )

        result.total_found = len(favourites)
        sync_state.sync_progress_total = result.total_found
        sync_state.sync_message = f"Found {result.total_found} favourites"
        await db.flush()
        await db.commit()

        to_download = []

        for fav in favourites:
            work_url = fav.get("url", "")
            work_id = fav.get("story_id", "")

            if not work_url or not work_id:
                continue

            existing = await db.execute(
                select(Fic).where(Fic.source_site == "ffnet", Fic.source_id == work_id)
            )

            if existing.scalar_one_or_none() is not None:
                result.total_skipped += 1
                continue

            to_download.append(fav)

        sync_state.sync_message = f"Downloading {len(to_download)} new fics ({result.total_skipped} already archived)"
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
            db, to_download, site_key="ffnet", source_id=source_id,
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

        if result.total_found > 0 or result.total_new > 0:
            await create_notification(
                db, type="sync_complete",
                title="FFNet Favourites Sync Complete",
                message=f"Found {result.total_found}: {result.total_new} new, {result.total_skipped} already archived.",
                severity="success",
            )

    except Exception as e:
        logger.exception("FFNet favourites sync failed")
        result.success = False
        result.errors.append(str(e))

        sync_state.sync_status = "failed"
        sync_state.sync_message = str(e)
        await db.flush()

        await create_notification(
            db, type="sync_failed",
            title="FFNet Favourites Sync Failed",
            message=str(e),
            severity="error",
        )

    return result
