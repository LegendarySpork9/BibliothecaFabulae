# Load libraries
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.source import BookmarkSyncState, Source

logger = logging.getLogger(__name__)

_cancel_requested: set[str] = set()


# Requests cancellation of a sync for a source site
def request_sync_cancel(site_key: str) -> None:
    _cancel_requested.add(site_key)


# Checks if cancellation has been requested for a site
def is_sync_cancelled(site_key: str) -> bool:
    return site_key in _cancel_requested


# Clears the cancellation flag
def clear_sync_cancel(site_key: str) -> None:
    _cancel_requested.discard(site_key)


# Dispatches a bookmark sync to the appropriate site-specific handler
async def run_bookmark_sync(db: AsyncSession, source_id: int) -> dict:
    source_result = await db.execute(select(Source).where(Source.id == source_id))
    source = source_result.scalar_one_or_none()

    if source is None:
        raise ValueError("Source not found")

    if not source.is_enabled:
        raise ValueError(f"Source {source.site_key} is disabled")

    if source.auth_status == "expired":
        raise ValueError(f"Source {source.site_key} has expired authentication")

    clear_sync_cancel(source.site_key)

    if source.site_key == "ao3":
        from backend.downloader.ao3_sync import sync_ao3_bookmarks
        result = await sync_ao3_bookmarks(db, source_id)

    elif source.site_key == "ffnet":
        from backend.downloader.ffnet_sync import sync_ffnet_favourites
        result = await sync_ffnet_favourites(db, source_id)

    elif source.site_key == "fimfiction":
        from backend.downloader.fimfiction_sync import sync_fimfiction_bookshelf
        result = await sync_fimfiction_bookshelf(db, source_id)

    elif source.site_key == "spacebattles":
        from backend.downloader.generic_list_sync import sync_spacebattles_watched
        result = await sync_spacebattles_watched(db, source_id)

    elif source.site_key == "sufficientvelocity":
        from backend.downloader.generic_list_sync import sync_sufficientvelocity_watched
        result = await sync_sufficientvelocity_watched(db, source_id)

    elif source.site_key == "royalroad":
        from backend.downloader.generic_list_sync import sync_royalroad_readlist
        result = await sync_royalroad_readlist(db, source_id)

    else:
        raise ValueError(f"Bookmark sync not supported for {source.site_key}")

    return {
        "success": result.success,
        "total_found": result.total_found,
        "total_new": result.total_new,
        "total_skipped": result.total_skipped,
        "total_failed": result.total_failed,
        "errors": result.errors,
    }


# Returns the current sync state for a source site
async def get_sync_state(db: AsyncSession, source_site: str) -> dict | None:
    result = await db.execute(
        select(BookmarkSyncState).where(BookmarkSyncState.source_site == source_site)
    )
    state = result.scalar_one_or_none()

    if state is None:
        return None

    return {
        "source_site": state.source_site,
        "last_synced": state.last_synced.isoformat() if state.last_synced else None,
        "last_bookmark_id": state.last_bookmark_id,
        "total_bookmarks": state.total_bookmarks,
        "total_synced": state.total_synced,
        "sync_status": state.sync_status or "idle",
        "sync_progress_current": state.sync_progress_current or 0,
        "sync_progress_total": state.sync_progress_total,
        "sync_message": state.sync_message,
    }
