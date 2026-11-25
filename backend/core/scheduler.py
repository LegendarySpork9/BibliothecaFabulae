# Load libraries
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.models.source import Source

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_session_factory: async_sessionmaker | None = None


# Initialises the scheduler and loads existing source jobs
async def init_scheduler(session_factory: async_sessionmaker) -> None:
    global _session_factory
    _session_factory = session_factory

    async with session_factory() as db:
        result = await db.execute(select(Source).where(Source.is_enabled == True))  # noqa: E712
        sources = result.scalars().all()

        await _enforce_minimum_rate_limits(db, sources)

        for source in sources:
            _add_source_jobs(source)

        await db.commit()

    async with session_factory() as db:
        from backend.services.download_job_service import purge_old_jobs

        purged = await purge_old_jobs(db)

        from backend.models.source import BookmarkSyncState

        stuck = await db.execute(
            select(BookmarkSyncState).where(BookmarkSyncState.sync_status == "syncing")
        )

        for state in stuck.scalars().all():
            state.sync_status = "idle"
            state.sync_message = "Reset after restart"
            logger.info("Reset stuck sync state for %s", state.source_site)

        from sqlalchemy import update
        from backend.models.download_job import DownloadJob
        from backend.core.utils import utcnow

        stuck_jobs = await db.execute(
            update(DownloadJob)
            .where(DownloadJob.status.in_(["queued", "downloading"]))
            .values(status="failed", status_message="Interrupted — app restarted", completed_at=utcnow())
        )

        if stuck_jobs.rowcount:
            logger.info("Reset %d stuck download jobs after restart", stuck_jobs.rowcount)

        await db.commit()

        if purged:
            logger.info("Startup purge: removed %d old download jobs", purged)

    _add_job("download_cleanup", _run_download_cleanup, "0 7 * * *")

    logger.info("Scheduler initialised with %d source(s)", len(sources))


# Adds or updates bookmark sync and update check jobs for a source
def schedule_source_jobs(source_id: int, bookmark_cron: str, update_cron: str) -> None:
    _add_job(
        f"bookmark_sync_{source_id}",
        _run_bookmark_sync,
        bookmark_cron,
        args=[source_id],
    )
    _add_job(
        f"update_check_{source_id}",
        _run_update_check,
        update_cron,
        args=[source_id],
    )


# Removes all scheduled jobs for a source
def remove_source_jobs(source_id: int) -> None:
    for prefix in ("bookmark_sync_", "update_check_"):
        job_id = f"{prefix}{source_id}"

        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info("Removed job %s", job_id)


# Returns a list of all scheduled jobs with next run times
def get_scheduled_jobs() -> list[dict]:
    jobs = []

    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return jobs


# Ensures each source's rate limit meets the site-defined minimum
async def _enforce_minimum_rate_limits(db, sources: list[Source]) -> None:
    import json
    from backend.services.source_service import SUPPORTED_SITES

    for source in sources:
        site_info = SUPPORTED_SITES.get(source.site_key)

        if not site_info:
            continue

        min_delay = site_info["default_rate_limit"]["delay_ms"]
        current = {}

        if source.rate_limit_config:
            try:
                current = json.loads(source.rate_limit_config)

            except (json.JSONDecodeError, TypeError):
                pass

        current_delay = current.get("delay_ms", 0)

        if current_delay < min_delay:
            current["delay_ms"] = min_delay
            source.rate_limit_config = json.dumps(current)
            logger.info(
                "Bumped %s rate limit from %dms to %dms (site minimum)",
                source.site_key, current_delay, min_delay,
            )
            await db.flush()


# Registers bookmark sync and update check jobs for a single source
def _add_source_jobs(source: Source) -> None:
    schedule_source_jobs(
        source.id,
        source.sync_interval_bookmarks or "0 2 * * *",
        source.sync_interval_updates or "0 3 * * *",
    )


# Adds or reschedules a single APScheduler cron job
def _add_job(job_id: str, func, cron_expr: str, args: list | None = None) -> None:
    try:
        trigger = CronTrigger.from_crontab(cron_expr)

        if scheduler.get_job(job_id):
            scheduler.reschedule_job(job_id, trigger=trigger)
        else:
            scheduler.add_job(func, trigger, id=job_id, args=args or [], replace_existing=True)

    except Exception:
        logger.exception("Failed to schedule job %s with cron '%s'", job_id, cron_expr)


# Scheduled task: runs bookmark sync for a source
async def _run_bookmark_sync(source_id: int) -> None:
    if _session_factory is None:
        return

    async with _session_factory() as db:
        try:
            from backend.services.sync_service import run_bookmark_sync

            await run_bookmark_sync(db, source_id)
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception("Scheduled bookmark sync failed for source %d", source_id)


# Scheduled task: checks all fics for updates
async def _run_update_check(source_id: int) -> None:
    if _session_factory is None:
        return

    async with _session_factory() as db:
        try:
            from backend.services.update_service import check_all_fic_updates

            await check_all_fic_updates(db)
            await db.commit()

        except Exception:
            await db.rollback()
            logger.exception("Scheduled update check failed for source %d", source_id)


# Scheduled task: purges old completed download jobs
async def _run_download_cleanup() -> None:
    if _session_factory is None:
        return

    async with _session_factory() as db:
        try:
            from backend.services.download_job_service import purge_old_jobs

            purged = await purge_old_jobs(db)
            await db.commit()

            if purged:
                logger.info("Daily purge: removed %d old download jobs", purged)

        except Exception:
            await db.rollback()
            logger.exception("Download cleanup job failed")
