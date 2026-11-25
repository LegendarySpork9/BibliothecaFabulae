# Load libraries
from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.utils import utcnow
from backend.models.download_job import DownloadJob
from backend.services.download_job_service import (
    clear_all_jobs,
    clear_completed_jobs,
    create_job,
    get_jobs,
    purge_old_jobs,
    update_job_status,
)


# Test that create_job returns a job with the expected fields
@pytest.mark.asyncio
async def test_create_job(db_session: AsyncSession):
    job = await create_job(
        db_session, url="https://example.com/fic/123", source_site="ao3", source_id="123"
    )

    assert job.id is not None
    assert job.url == "https://example.com/fic/123"
    assert job.source_site == "ao3"
    assert job.source_id == "123"
    assert job.status == "queued"
    assert job.status_message == "Waiting to start"


# Test that updating status to downloading sets download_started_at
@pytest.mark.asyncio
async def test_update_job_status_downloading(db_session: AsyncSession):
    job = await create_job(db_session, url="https://example.com/fic/1")

    await update_job_status(db_session, job.id, "downloading", status_message="Downloading chapters")

    assert job.status == "downloading"
    assert job.download_started_at is not None
    assert job.status_message == "Downloading chapters"


# Test that updating status to complete sets completed_at and download_seconds
@pytest.mark.asyncio
async def test_update_job_status_complete(db_session: AsyncSession):
    job = await create_job(db_session, url="https://example.com/fic/2")

    await update_job_status(db_session, job.id, "downloading")
    await update_job_status(db_session, job.id, "complete", status_message="Done")

    assert job.status == "complete"
    assert job.completed_at is not None
    assert job.download_seconds is not None
    assert job.download_seconds >= 0


# Test that updating a nonexistent job does not raise an error
@pytest.mark.asyncio
async def test_update_job_status_nonexistent(db_session: AsyncSession):
    await update_job_status(db_session, 99999, "complete")


# Test that get_jobs returns an empty list when no jobs exist
@pytest.mark.asyncio
async def test_get_jobs_empty(db_session: AsyncSession):
    result = await get_jobs(db_session)

    assert result["items"] == []
    assert result["total"] == 0


# Test that get_jobs with a status filter returns only matching jobs
@pytest.mark.asyncio
async def test_get_jobs_with_filter(db_session: AsyncSession):
    job_a = await create_job(db_session, url="https://example.com/fic/a", source_site="ao3")
    job_b = await create_job(db_session, url="https://example.com/fic/b", source_site="ao3")

    await update_job_status(db_session, job_a.id, "complete")

    result = await get_jobs(db_session, status="complete")

    assert result["total"] == 1
    assert result["items"][0]["id"] == job_a.id


# Test that clear_completed_jobs only deletes completed jobs
@pytest.mark.asyncio
async def test_clear_completed_jobs(db_session: AsyncSession):
    job_a = await create_job(db_session, url="https://example.com/fic/a")
    job_b = await create_job(db_session, url="https://example.com/fic/b")

    await update_job_status(db_session, job_a.id, "complete")

    deleted = await clear_completed_jobs(db_session)

    assert deleted == 1

    remaining = await get_jobs(db_session)
    assert remaining["total"] == 1
    assert remaining["items"][0]["id"] == job_b.id


# Test that clear_all_jobs deletes every job
@pytest.mark.asyncio
async def test_clear_all_jobs(db_session: AsyncSession):
    await create_job(db_session, url="https://example.com/fic/a")
    await create_job(db_session, url="https://example.com/fic/b")
    await create_job(db_session, url="https://example.com/fic/c")

    deleted = await clear_all_jobs(db_session)

    assert deleted == 3

    remaining = await get_jobs(db_session)
    assert remaining["total"] == 0


# Test that purge_old_jobs removes old completed and failed jobs
@pytest.mark.asyncio
async def test_purge_old_jobs(db_session: AsyncSession):
    old_time = utcnow() - timedelta(days=60)

    # Old completed job
    old_complete = DownloadJob(
        url="https://example.com/fic/old-complete",
        status="complete",
        completed_at=old_time,
    )
    db_session.add(old_complete)

    # Old failed job
    old_failed = DownloadJob(
        url="https://example.com/fic/old-failed",
        status="failed",
        completed_at=old_time,
    )
    db_session.add(old_failed)

    # Recent completed job (should not be purged)
    recent_complete = DownloadJob(
        url="https://example.com/fic/recent-complete",
        status="complete",
        completed_at=utcnow(),
    )
    db_session.add(recent_complete)

    # Queued job (should not be purged)
    queued = DownloadJob(
        url="https://example.com/fic/queued",
        status="queued",
    )
    db_session.add(queued)

    await db_session.flush()

    purged = await purge_old_jobs(db_session, completed_days=7, failed_days=30)

    assert purged == 2

    remaining = await get_jobs(db_session)
    assert remaining["total"] == 2
