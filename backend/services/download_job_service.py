# Load libraries
import logging
from datetime import timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.utils import utcnow
from backend.models.download_job import DownloadJob

logger = logging.getLogger(__name__)


# Creates a new download job record
async def create_job(
    db: AsyncSession,
    url: str,
    source_site: str | None = None,
    source_id: str | None = None,
) -> DownloadJob:
    job = DownloadJob(
        url=url,
        source_site=source_site,
        source_id=source_id,
        status="queued",
        status_message="Waiting to start",
    )
    db.add(job)
    await db.flush()

    return job


# Updates a job's status
async def update_job_status(
    db: AsyncSession,
    job_id: int,
    status: str,
    status_message: str | None = None,
    fic_title: str | None = None,
    fic_id: int | None = None,
) -> None:
    result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        return

    job.status = status

    if status_message is not None:
        job.status_message = status_message

    if fic_title is not None:
        job.fic_title = fic_title

    if fic_id is not None:
        job.fic_id = fic_id

    if status == "downloading" and job.download_started_at is None:
        job.download_started_at = utcnow()

    if status == "complete" and job.download_started_at:
        elapsed = (utcnow() - job.download_started_at).total_seconds()
        job.download_seconds = elapsed

    if status in ("complete", "failed"):
        job.completed_at = utcnow()

    await db.flush()


# Returns download jobs with optional filtering, ordered by most recent first
async def get_jobs(
    db: AsyncSession,
    status: str | None = None,
    source_site: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    query = select(DownloadJob)
    count_query = select(func.count(DownloadJob.id))

    if status:
        query = query.where(DownloadJob.status == status)
        count_query = count_query.where(DownloadJob.status == status)

    if source_site:
        query = query.where(DownloadJob.source_site == source_site)
        count_query = count_query.where(DownloadJob.source_site == source_site)

    query = query.order_by(DownloadJob.started_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return {
        "items": [
            {
                "id": j.id,
                "url": j.url,
                "source_site": j.source_site,
                "source_id": j.source_id,
                "fic_title": j.fic_title,
                "status": j.status,
                "status_message": j.status_message,
                "fic_id": j.fic_id,
                "chapter_count": j.chapter_count,
                "download_seconds": j.download_seconds,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "download_started_at": j.download_started_at.isoformat() if j.download_started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "eta_seconds": _calc_eta(j),
            }
            for j in jobs
        ],
        "total": total,
        "avg_seconds_per_chapter": await _get_avg_seconds_per_chapter(db),
    }


# Deletes all completed download jobs
async def clear_completed_jobs(db: AsyncSession) -> int:
    result = await db.execute(
        delete(DownloadJob).where(DownloadJob.status == "complete")
    )
    await db.flush()

    return result.rowcount


# Deletes all download jobs
async def clear_all_jobs(db: AsyncSession) -> int:
    result = await db.execute(delete(DownloadJob))
    await db.flush()

    return result.rowcount


# Purges old jobs based on age
async def purge_old_jobs(
    db: AsyncSession,
    completed_days: int = 7,
    failed_days: int = 30,
) -> int:
    now = utcnow()
    total_purged = 0

    completed_cutoff = now - timedelta(days=completed_days)
    result = await db.execute(
        delete(DownloadJob).where(
            DownloadJob.status == "complete",
            DownloadJob.completed_at < completed_cutoff,
        )
    )
    total_purged += result.rowcount

    failed_cutoff = now - timedelta(days=failed_days)
    result = await db.execute(
        delete(DownloadJob).where(
            DownloadJob.status == "failed",
            DownloadJob.completed_at < failed_cutoff,
        )
    )
    total_purged += result.rowcount

    await db.flush()

    if total_purged > 0:
        logger.info("Purged %d old download jobs", total_purged)

    return total_purged


# Calculates estimated time remaining for a downloading job
def _calc_eta(job: DownloadJob) -> float | None:
    if job.status != "downloading":
        return None

    if not job.download_started_at:
        return None

    elapsed = (utcnow() - job.download_started_at).total_seconds()

    return elapsed


# Computes average download seconds per chapter, grouped by source site
async def _get_avg_seconds_per_chapter(db: AsyncSession) -> dict:
    from sqlalchemy import func as sqlfunc

    result = await db.execute(
        select(
            DownloadJob.source_site,
            sqlfunc.avg(DownloadJob.download_seconds / DownloadJob.chapter_count),
        )
        .where(
            DownloadJob.status == "complete",
            DownloadJob.download_seconds.is_not(None),
            DownloadJob.chapter_count.is_not(None),
            DownloadJob.chapter_count > 0,
        )
        .group_by(DownloadJob.source_site)
    )

    return {row[0]: round(row[1], 1) for row in result.all() if row[0]}
