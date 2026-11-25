# Load libraries
import logging
import os
import re
import subprocess
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from backend.downloader.fimfiction_sync import SyncResult, _sync_via_fanficfare_list

logger = logging.getLogger(__name__)


# Generic FanFicFare list fetcher for any site
def _fetch_list_sync(list_url: str, delay_ms: int, url_pattern: str, cookies: str | None = None) -> list[dict]:
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

    ini_content = "\n".join(ini_lines) + "\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
        f.write(ini_content)
        ini_path = f.name

    try:
        result = subprocess.run(
            ["fanficfare", "--non-interactive", "--config", ini_path,
             "--normalize-list", list_url],
            capture_output=True, text=True, timeout=300,
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

        match = re.search(url_pattern, line)

        if match:
            urls.append({"url": line, "story_id": match.group(1)})

    return urls


# SpaceBattles watched threads sync
async def sync_spacebattles_watched(db: AsyncSession, source_id: int) -> SyncResult:
    # Wraps _fetch_list_sync with SpaceBattles URL pattern
    def fetch(url, delay, cookies=None):
        return _fetch_list_sync(url, delay, r"forums\.spacebattles\.com/threads/[^/]*?\.?(\d+)", cookies)

    return await _sync_via_fanficfare_list(
        db, source_id,
        site_key="spacebattles",
        display_name="SpaceBattles",
        url_pattern=r"forums\.spacebattles\.com/threads/[^/]*?\.?(\d+)",
        fetch_fn=fetch,
        auth_field="watched_url",
        auth_help='{"watched_url": "https://forums.spacebattles.com/watched/threads"}',
    )


# Sufficient Velocity watched threads sync
async def sync_sufficientvelocity_watched(db: AsyncSession, source_id: int) -> SyncResult:
    # Wraps _fetch_list_sync with Sufficient Velocity URL pattern
    def fetch(url, delay, cookies=None):
        return _fetch_list_sync(url, delay, r"forums\.sufficientvelocity\.com/threads/[^/]*?\.?(\d+)", cookies)

    return await _sync_via_fanficfare_list(
        db, source_id,
        site_key="sufficientvelocity",
        display_name="Sufficient Velocity",
        url_pattern=r"forums\.sufficientvelocity\.com/threads/[^/]*?\.?(\d+)",
        fetch_fn=fetch,
        auth_field="watched_url",
        auth_help='{"watched_url": "https://forums.sufficientvelocity.com/watched/threads"}',
    )


# Royal Road reading list sync
async def sync_royalroad_readlist(db: AsyncSession, source_id: int) -> SyncResult:
    # Wraps _fetch_list_sync with Royal Road URL pattern
    def fetch(url, delay, cookies=None):
        return _fetch_list_sync(url, delay, r"royalroad\.com/fiction/(\d+)", cookies)

    return await _sync_via_fanficfare_list(
        db, source_id,
        site_key="royalroad",
        display_name="Royal Road",
        url_pattern=r"royalroad\.com/fiction/(\d+)",
        fetch_fn=fetch,
        auth_field="readlist_url",
        auth_help='{"readlist_url": "https://www.royalroad.com/my/readlater"}',
    )
