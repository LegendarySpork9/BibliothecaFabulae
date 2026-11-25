# Load libraries
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_db
from backend.models.user import User
from backend.services.source_service import (
    create_source,
    delete_source,
    get_source,
    get_sources,
    get_supported_sites,
    update_source,
    update_source_auth,
    update_source_config,
    validate_source_auth,
)

router = APIRouter(prefix="/api/sources", tags=["sources"])


# Supported site info response
class SupportedSiteItem(BaseModel):
    site_key: str
    label: str
    auth_types: list[str]
    config_fields: dict | None = None
    default_rate_limit: dict


# Source response item
class SourceItem(BaseModel):
    id: int
    site_key: str
    label: str
    is_enabled: bool
    auth_type: str
    auth_configured: bool
    auth_status: str
    auth_last_checked: str | None
    sync_interval_bookmarks: str
    sync_interval_updates: str
    rate_limit_config: dict | None
    config_configured: bool
    config_fields: dict | None = None
    created_at: str | None
    updated_at: str | None
    validation_message: str | None = None


# Create source request body
class CreateSourceRequest(BaseModel):
    site_key: str
    auth_type: str = "none"
    auth_data: str | None = None
    config_data: str | None = None
    sync_interval_bookmarks: str | None = None
    sync_interval_updates: str | None = None
    rate_limit_config: dict | None = None


# Update source request body
class UpdateSourceRequest(BaseModel):
    is_enabled: bool | None = None
    sync_interval_bookmarks: str | None = None
    sync_interval_updates: str | None = None
    rate_limit_config: dict | None = None


# Update source config request body
class UpdateSourceConfigRequest(BaseModel):
    config_data: str


# Update source auth request body
class UpdateSourceAuthRequest(BaseModel):
    auth_type: str
    auth_data: str | None = None


# Generic success response
class SuccessResponse(BaseModel):
    success: bool


# List all supported sites that can be configured
@router.get("/supported", response_model=list[SupportedSiteItem])
async def list_supported_sites(
    _user: User = Depends(get_current_user),
):
    return get_supported_sites()


# List all configured sources
@router.get("", response_model=list[SourceItem])
async def list_sources(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_sources(db)


# Get a single source by ID
@router.get("/{source_id}", response_model=SourceItem)
async def read_source(
    source_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_source(db, source_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Create a new source configuration and validate credentials inline
@router.post("", response_model=SourceItem, status_code=status.HTTP_201_CREATED)
async def add_source(
    body: CreateSourceRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await create_source(
            db,
            site_key=body.site_key,
            auth_type=body.auth_type,
            auth_data=body.auth_data,
            config_data=body.config_data,
            sync_interval_bookmarks=body.sync_interval_bookmarks,
            sync_interval_updates=body.sync_interval_updates,
            rate_limit_config=body.rate_limit_config,
        )

        if body.auth_data and body.auth_type != "none":
            return await validate_source_auth(db, result["id"])

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Update a source's non-auth configuration
@router.patch("/{source_id}", response_model=SourceItem)
async def patch_source(
    source_id: int,
    body: UpdateSourceRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_source(
            db,
            source_id,
            is_enabled=body.is_enabled,
            sync_interval_bookmarks=body.sync_interval_bookmarks,
            sync_interval_updates=body.sync_interval_updates,
            rate_limit_config=body.rate_limit_config,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Update a source's authentication credentials and validate them inline
@router.patch("/{source_id}/auth", response_model=SourceItem)
async def patch_source_auth(
    source_id: int,
    body: UpdateSourceAuthRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await update_source_auth(
            db,
            source_id,
            auth_type=body.auth_type,
            auth_data=body.auth_data,
        )

        if body.auth_data and body.auth_type != "none":
            return await validate_source_auth(db, source_id)

        result = await get_source(db, source_id)
        result["validation_message"] = "Credentials cleared"

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Validate a source's credentials
# Update a source's configuration data (URLs, settings)
@router.patch("/{source_id}/config", response_model=SourceItem)
async def patch_source_config(
    source_id: int,
    body: UpdateSourceConfigRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_source_config(db, source_id, config_data=body.config_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Validate a source's credentials
@router.post("/{source_id}/validate", response_model=SourceItem)
async def validate_auth(
    source_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await validate_source_auth(db, source_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Delete a source configuration
@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source(
    source_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_source(db, source_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Cancel a running sync for a source
@router.post("/{source_id}/cancel-sync")
async def cancel_sync(
    source_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.sync_service import request_sync_cancel

    try:
        source_data = await get_source(db, source_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    request_sync_cancel(source_data["site_key"])

    from sqlalchemy import update
    from backend.models.download_job import DownloadJob
    from backend.core.utils import utcnow

    result = await db.execute(
        update(DownloadJob)
        .where(
            DownloadJob.source_site == source_data["site_key"],
            DownloadJob.status == "queued",
        )
        .values(status="failed", status_message="Cancelled — sync was stopped", completed_at=utcnow())
    )

    return {"status": "cancelling", "message": f"Cancellation requested for {source_data['site_key']}", "queued_cancelled": result.rowcount}


# Trigger a manual bookmark sync for a source
@router.post("/{source_id}/sync")
async def trigger_sync(
    source_id: int,
    background_tasks: BackgroundTasks,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        source_data = await get_source(db, source_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    async def _run():
        from backend.core.database import async_session
        from backend.services.sync_service import run_bookmark_sync

        async with async_session() as session:
            try:
                await run_bookmark_sync(session, source_id)
                await session.commit()
            except Exception:
                await session.rollback()

    background_tasks.add_task(_run)

    return {"status": "syncing", "message": f"Sync started for {source_data['site_key']}"}


# Get the sync state for a source
@router.get("/{source_id}/sync-state")
async def read_sync_state(
    source_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.sync_service import get_sync_state

    try:
        source_data = await get_source(db, source_id)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    state = await get_sync_state(db, source_data["site_key"])

    return state or {"source_site": source_data["site_key"], "last_synced": None, "total_synced": 0}


# List all scheduled jobs
@router.get("/scheduler/jobs")
async def list_scheduled_jobs(
    _user: User = Depends(get_current_user),
):
    from backend.core.scheduler import get_scheduled_jobs

    return get_scheduled_jobs()
