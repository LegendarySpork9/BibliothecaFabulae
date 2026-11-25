# Load libraries
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_db
from backend.models.user import User
from backend.services.fic_service import (
    delete_fic,
    get_chapter_content,
    get_fic,
    get_fic_chapters,
    get_fics,
    search_fic_content,
)

router = APIRouter(prefix="/api/fics", tags=["fics"])


# Import request body
class ImportRequest(BaseModel):
    url: str


# Import response
class ImportResponse(BaseModel):
    status: str
    message: str


# Fic summary for list views
class FicSummaryItem(BaseModel):
    id: int
    source_site: str
    source_id: str
    title: str
    rating: str | None
    word_count: int | None
    chapter_count: int | None
    is_complete: bool
    is_favourite: bool
    is_source_available: bool
    import_method: str
    date_archived: str | None
    authors: list[dict]


# Paginated fic list response
class FicListResponse(BaseModel):
    items: list[FicSummaryItem]
    total: int


# Generic success response
class SuccessResponse(BaseModel):
    success: bool


# Import a fic from a URL (runs download in background)
@router.post("/import", response_model=ImportResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_fic(
    body: ImportRequest,
    background_tasks: BackgroundTasks,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.import_service import identify_source_site
    from backend.services.download_job_service import create_job

    identification = identify_source_site(body.url)

    if identification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not identify source site for URL: {body.url}",
        )

    site_key, source_id = identification
    job = await create_job(db, body.url, source_site=site_key, source_id=source_id)
    job_id = job.id

    async def _run_import():
        from backend.core.database import async_session
        from backend.services.import_service import import_fic_from_url
        from backend.services.download_job_service import update_job_status
        from backend.services.notification_service import create_notification
        from backend.downloader.fanficfare_wrapper import get_story_metadata
        from backend.models.download_job import DownloadJob
        from sqlalchemy import select
        import logging

        async with async_session() as session:
            try:
                await update_job_status(session, job_id, "downloading", "Fetching metadata...")
                await session.commit()

            except Exception:
                await session.rollback()

        async with async_session() as session:
            try:
                meta = await get_story_metadata(url=body.url, site_key=site_key)
                chapter_count = None

                if isinstance(meta, dict) and "error" not in meta:
                    raw = meta.get("numChapters") or meta.get("numchapters")
                    if raw:
                        try:
                            chapter_count = int(str(raw).replace(",", "").split("/")[0].strip())

                        except (ValueError, TypeError):
                            pass

                if chapter_count:
                    job_row = (await session.execute(
                        select(DownloadJob).where(DownloadJob.id == job_id)
                    )).scalar_one_or_none()
                    if job_row:
                        job_row.chapter_count = chapter_count

                await update_job_status(session, job_id, "downloading", "Downloading from source...")
                await session.commit()

            except Exception:
                await session.rollback()

        async with async_session() as session:
            try:
                result = await import_fic_from_url(session, body.url)

                if result.get("chapter_count"):
                    job_row = (await session.execute(
                        select(DownloadJob).where(DownloadJob.id == job_id)
                    )).scalar_one_or_none()
                    if job_row and not job_row.chapter_count:
                        job_row.chapter_count = result["chapter_count"]

                await update_job_status(
                    session, job_id, "complete", "Import complete",
                    fic_title=result.get("title"), fic_id=result.get("fic_id"),
                )

                await session.commit()

            except Exception as e:
                await session.rollback()
                logging.getLogger(__name__).exception("Background import failed for %s", body.url)

                async with async_session() as err_session:
                    try:
                        await update_job_status(
                            err_session, job_id, "failed", str(e),
                        )
                        await create_notification(
                            err_session,
                            type="sync_failed",
                            title="Import Failed",
                            message=f"Failed to import {body.url}: {e}",
                            severity="error",
                        )
                        await err_session.commit()

                    except Exception:
                        await err_session.rollback()

    background_tasks.add_task(_run_import)

    return {"status": "importing", "message": f"Download started for {body.url}"}


# Get the full supported site directory
@router.get("/sites")
async def list_supported_sites(
    _user: User = Depends(get_current_user),
):
    from backend.services.site_directory import get_site_directory

    return get_site_directory()


# List download jobs with optional filtering
@router.get("/downloads")
async def list_downloads(
    status_filter: str | None = Query(None, alias="status"),
    source_site: str | None = Query(None),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.download_job_service import get_jobs

    return await get_jobs(db, status=status_filter, source_site=source_site, limit=limit, offset=offset)


# Clear completed download jobs
@router.delete("/downloads/completed")
async def clear_completed_downloads(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.download_job_service import clear_completed_jobs

    count = await clear_completed_jobs(db)

    return {"cleared": count}


# Clear all download jobs
@router.delete("/downloads")
async def clear_all_downloads(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.download_job_service import clear_all_jobs

    count = await clear_all_jobs(db)

    return {"cleared": count}


# List fics with optional filtering and sorting
@router.get("", response_model=FicListResponse)
async def list_fics(
    source_site: str | None = Query(None),
    is_complete: bool | None = Query(None),
    is_favourite: bool | None = Query(None),
    is_source_available: bool | None = Query(None),
    import_method: str | None = Query(None),
    sort: str = Query("-date_archived"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_fics(
        db,
        source_site=source_site,
        is_complete=is_complete,
        is_favourite=is_favourite,
        is_source_available=is_source_available,
        import_method=import_method,
        sort=sort,
        limit=limit,
        offset=offset,
    )


# Get update check status
@router.get("/update-status")
async def get_update_status(
    _user: User = Depends(get_current_user),
):
    from backend.services.update_service import get_update_check_status

    return get_update_check_status()


# Get a single fic by ID
@router.get("/{fic_id}")
async def read_fic(
    fic_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_fic(db, fic_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# List chapters for a fic
@router.get("/{fic_id}/chapters")
async def list_chapters(
    fic_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_fic_chapters(db, fic_id)


# Get chapter content
@router.get("/{fic_id}/chapters/{chapter_id}")
async def read_chapter(
    fic_id: int,
    chapter_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_chapter_content(db, chapter_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Delete a fic
@router.delete("/{fic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_fic(
    fic_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_fic(db, fic_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Full-text search across fic content
@router.get("/search/content")
async def search_content(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await search_fic_content(db, q, limit=limit, offset=offset)


# Check a single fic for updates
@router.post("/{fic_id}/check-update")
async def check_update(
    fic_id: int,
    background_tasks: BackgroundTasks,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.update_service import (
        _checking_fic_ids,
        _bulk_check_running,
        check_fic_updates,
    )

    if _bulk_check_running or fic_id in _checking_fic_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An update check is already running for this fic or a bulk check is in progress",
        )

    _checking_fic_ids.add(fic_id)

    async def _run():
        from backend.core.database import async_session
        import logging

        try:
            async with async_session() as session:
                try:
                    result = await check_fic_updates(session, fic_id)
                    await session.commit()

                    logging.getLogger(__name__).info("Update check for fic %d: %s", fic_id, result)

                except Exception:
                    await session.rollback()
                    logging.getLogger(__name__).exception("Update check failed for fic %d", fic_id)

        finally:
            _checking_fic_ids.discard(fic_id)

    background_tasks.add_task(_run)

    return {"status": "checking", "message": f"Update check started for fic {fic_id}"}


# Check all fics for updates
@router.post("/check-updates")
async def check_all_updates(
    background_tasks: BackgroundTasks,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    import backend.services.update_service as update_svc

    if update_svc._bulk_check_running or len(update_svc._checking_fic_ids) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An update check is already running",
        )

    update_svc._bulk_check_running = True

    async def _run():
        from backend.core.database import async_session
        import logging

        try:
            async with async_session() as session:
                try:
                    result = await update_svc.check_all_fic_updates(session)
                    await session.commit()

                    logging.getLogger(__name__).info("Bulk update check: %s", result)

                except Exception:
                    await session.rollback()
                    logging.getLogger(__name__).exception("Bulk update check failed")

        finally:
            update_svc._bulk_check_running = False

    background_tasks.add_task(_run)

    return {"status": "checking", "message": "Update check started for all fics"}


# List version history for a chapter
@router.get("/{fic_id}/chapters/{chapter_id}/versions")
async def list_chapter_versions(
    fic_id: int,
    chapter_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.update_service import get_chapter_versions

    return await get_chapter_versions(db, chapter_id)


# Get a specific chapter version's content
@router.get("/{fic_id}/chapters/{chapter_id}/versions/{version_id}")
async def read_chapter_version(
    fic_id: int,
    chapter_id: int,
    version_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.update_service import get_chapter_version_content

    try:
        content = await get_chapter_version_content(db, version_id)

        return {"version_id": version_id, "content": content}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
