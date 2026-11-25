# Load libraries
import logging
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from backend.downloader.fanficfare_wrapper import download_fic
from backend.models.download_job import DownloadJob
from backend.services.download_job_service import create_job, update_job_status
from backend.services.fic_service import store_downloaded_fic

logger = logging.getLogger(__name__)


# Downloads multiple fics sequentially, respecting cancellation
async def download_fics_sequential(
    db: AsyncSession,
    works: list[dict],
    site_key: str,
    source_id: int | None = None,
    auth_data: str | None = None,
    auth_type: str = "none",
    delay_ms: int = 5000,
    on_progress=None,
) -> dict:
    from backend.services.sync_service import is_sync_cancelled
    from backend.models.source import Source

    total_new = 0
    auth_status_updated = False
    total_failed = 0
    total_cancelled = 0
    errors = []

    job_ids = []

    for work in works:
        work_url = work.get("url", "")
        work_id = work.get("work_id") or work.get("story_id", "")

        if not work_url or not work_id:
            continue

        job = await create_job(db, work_url, source_site=site_key, source_id=work_id)
        work["_job_id"] = job.id
        job_ids.append(job.id)

    await db.flush()
    await db.commit()

    for i, work in enumerate(works):
        job_id = work.get("_job_id")

        if not job_id:
            continue

        if is_sync_cancelled(site_key):
            total_cancelled += 1
            continue

        work_url = work.get("url", "")
        work_id = work.get("work_id") or work.get("story_id", "")

        try:
            from backend.downloader.fanficfare_wrapper import get_story_metadata

            await update_job_status(db, job_id, "downloading", f"Fetching metadata for {work_url}")
            await db.flush()
            await db.commit()

            meta = await get_story_metadata(
                url=work_url, site_key=site_key,
                auth_data=auth_data, auth_type=auth_type, delay_ms=delay_ms,
            )

            chapter_count = None

            if isinstance(meta, dict) and "error" not in meta:
                raw = meta.get("numChapters") or meta.get("numchapters") or meta.get("chapterslashtotal")

                if raw:
                    try:
                        clean = str(raw).replace(",", "").split("/")[0].strip()
                        chapter_count = int(clean) if clean and clean != "?" else None

                    except (ValueError, TypeError):
                        pass

            if chapter_count:
                result = await db.execute(
                    select(DownloadJob).where(DownloadJob.id == job_id)
                )
                job_row = result.scalar_one_or_none()

                if job_row:
                    job_row.chapter_count = chapter_count

            await update_job_status(db, job_id, "downloading", f"Downloading {work_url}")
            await db.flush()
            await db.commit()

            with tempfile.TemporaryDirectory() as tmpdir:
                dl_result = await download_fic(
                    url=work_url, output_dir=tmpdir,
                    site_key=site_key, auth_data=auth_data,
                    auth_type=auth_type, delay_ms=delay_ms,
                )

                if dl_result.success:
                    fic = await store_downloaded_fic(
                        db, dl_result, site_key, work_id, work_url, "bookmark_sync",
                    )

                    if not chapter_count and fic.chapter_count:
                        job_row = (await db.execute(
                            select(DownloadJob).where(DownloadJob.id == job_id)
                        )).scalar_one_or_none()

                        if job_row:
                            job_row.chapter_count = fic.chapter_count

                    await update_job_status(
                        db, job_id, "complete", "Import complete",
                        fic_title=fic.title, fic_id=fic.id,
                    )
                    total_new += 1

                    if not auth_status_updated and source_id:
                        from backend.core.utils import utcnow

                        src = (await db.execute(select(Source).where(Source.id == source_id))).scalar_one_or_none()

                        if src and src.auth_status != "valid":
                            src.auth_status = "valid"
                            src.auth_last_checked = utcnow()

                        auth_status_updated = True
                else:
                    await update_job_status(
                        db, job_id, "failed", dl_result.error or "Download failed",
                    )
                    total_failed += 1
                    errors.append(f"Failed: {work_url}: {dl_result.error}")

                    if not auth_status_updated and source_id:
                        err = (dl_result.error or "").lower()

                        if "403" in err or "401" in err or "auth" in err or "login" in err:
                            from backend.core.utils import utcnow

                            src = (await db.execute(select(Source).where(Source.id == source_id))).scalar_one_or_none()

                            if src:
                                src.auth_status = "expired"
                                src.auth_last_checked = utcnow()

                            auth_status_updated = True

        except Exception as e:
            await update_job_status(db, job_id, "failed", str(e))
            total_failed += 1
            errors.append(f"Error: {work_url}: {str(e)}")

        await db.flush()
        await db.commit()

        if on_progress:
            await on_progress(i + 1, total_new, total_failed)

    return {
        "total_new": total_new,
        "total_failed": total_failed,
        "total_cancelled": total_cancelled,
        "errors": errors,
    }
