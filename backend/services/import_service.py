# Load libraries
import logging
import os
import re
import tempfile

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.downloader.fanficfare_wrapper import download_fic
from backend.models.fic import Fic
from backend.models.settings import Settings
from backend.models.source import Source
from backend.services.fic_service import store_downloaded_fic
from backend.services.notification_service import create_notification

logger = logging.getLogger(__name__)

URL_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "ao3": [
        (r"archiveofourown\.org/works/(\d+)", r"\1"),
    ],
    "ffnet": [
        (r"fanfiction\.net/s/(\d+)", r"\1"),
    ],
    "wattpad": [
        (r"wattpad\.com/story/(\d+)", r"\1"),
        (r"wattpad\.com/(\d+)", r"\1"),
    ],
    "royalroad": [
        (r"royalroad\.com/fiction/(\d+)", r"\1"),
    ],
    "spacebattles": [
        (r"forums\.spacebattles\.com/threads/[^/]*\.(\d+)", r"\1"),
        (r"forums\.spacebattles\.com/threads/(\d+)", r"\1"),
    ],
    "sufficientvelocity": [
        (r"forums\.sufficientvelocity\.com/threads/[^/]*\.(\d+)", r"\1"),
        (r"forums\.sufficientvelocity\.com/threads/(\d+)", r"\1"),
    ],
    "scribblehub": [
        (r"scribblehub\.com/series/(\d+)", r"\1"),
    ],
    "fimfiction": [
        (r"fimfiction\.net/story/(\d+)", r"\1"),
    ],
    "quotev": [
        (r"quotev\.com/story/(\d+)", r"\1"),
    ],
    "ficwad": [
        (r"ficwad\.com/story/(\d+)", r"\1"),
    ],
    "adultfanfiction": [
        (r"adult-fanfiction\.org/story\.php\?no=(\d+)", r"\1"),
    ],
}


# Identifies the source site and extracts the story ID from a URL
def identify_source_site(url: str) -> tuple[str, str] | None:
    for site_key, patterns in URL_PATTERNS.items():
        for pattern, id_group in patterns:
            match = re.search(pattern, url)

            if match:
                source_id = match.group(1)

                return site_key, source_id

    return None


# Imports a fic from a URL — downloads, stores, and notifies
async def import_fic_from_url(db: AsyncSession, url: str) -> dict:
    identification = identify_source_site(url)

    if identification is None:
        raise ValueError(f"Could not identify source site for URL: {url}")

    site_key, source_id = identification

    existing = await db.execute(
        select(Fic).where(Fic.source_site == site_key, Fic.source_id == source_id)
    )

    if existing.scalar_one_or_none() is not None:
        raise ValueError(f"This fic is already in your archive ({site_key}/{source_id})")

    source_result = await db.execute(
        select(Source).where(Source.site_key == site_key)
    )
    source = source_result.scalar_one_or_none()

    auth_data = None
    auth_type = "none"
    delay_ms = 2000

    if source:
        auth_type = source.auth_type or "none"

        if source.auth_data_encrypted:
            from backend.services.source_service import get_source_auth_data
            auth_data = await get_source_auth_data(db, source.id)

        if source.rate_limit_config:
            import json
            rl = json.loads(source.rate_limit_config)
            delay_ms = rl.get("delay_ms", 2000)

    settings_result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = settings_result.scalar_one_or_none()

    if not settings_row or not settings_row.storage_path:
        raise ValueError("Storage path not configured")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await download_fic(
            url=url,
            output_dir=tmpdir,
            site_key=site_key,
            auth_data=auth_data,
            auth_type=auth_type,
            delay_ms=delay_ms,
        )

        if not result.success:
            raise ValueError(f"Download failed: {result.error}")

        fic = await store_downloaded_fic(
            db, result, site_key, source_id, url, "manual_url"
        )

    if source and source.auth_status != "valid":
        from backend.core.utils import utcnow
        source.auth_status = "valid"
        source.auth_last_checked = utcnow()
        await db.flush()

    await create_notification(
        db,
        type="sync_complete",
        title="Import Complete",
        message=f'"{fic.title}" has been added to your archive.',
        severity="success",
        related_fic_id=fic.id,
    )

    return {
        "fic_id": fic.id,
        "title": fic.title,
        "source_site": fic.source_site,
        "source_id": fic.source_id,
        "chapter_count": fic.chapter_count,
    }
