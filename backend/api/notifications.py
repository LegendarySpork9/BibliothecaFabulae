# Load libraries
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_db
from backend.models.user import User
from backend.services.notification_service import (
    delete_notification,
    get_notifications,
    get_preferences,
    get_unread_count,
    mark_all_read,
    mark_read,
    update_preference,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# Single notification item response
class NotificationItem(BaseModel):
    id: int
    type: str
    title: str
    message: str
    severity: str
    is_read: bool
    related_fic_id: int | None
    email_sent: bool
    created_at: str | None


# Paginated notification list response
class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int


# Unread notification count response
class UnreadCountResponse(BaseModel):
    unread_count: int


# Generic success response
class SuccessResponse(BaseModel):
    success: bool


# Notification preference item
class PreferenceItem(BaseModel):
    id: int
    notification_type: str
    ui_enabled: bool
    email_enabled: bool


# Notification preference update request body
class UpdatePreferenceRequest(BaseModel):
    ui_enabled: bool | None = None
    email_enabled: bool | None = None


# Notification preference update response
class UpdatePreferenceResponse(BaseModel):
    notification_type: str
    ui_enabled: bool
    email_enabled: bool


# List notifications with optional filtering and pagination
@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_notifications(
        db,
        unread_only=unread_only,
        type_filter=type,
        limit=limit,
        offset=offset,
    )


# Return the count of unread notifications
@router.get("/unread-count", response_model=UnreadCountResponse)
async def read_unread_count(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await get_unread_count(db)

    return {"unread_count": count}


# Mark a single notification as read
@router.patch("/{notification_id}/read", response_model=SuccessResponse)
async def patch_mark_read(
    notification_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await mark_read(db, notification_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# Mark all notifications as read
@router.post("/mark-all-read", response_model=SuccessResponse)
async def post_mark_all_read(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await mark_all_read(db)


# Delete a single notification
@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_notification(
    notification_id: int,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await delete_notification(db, notification_id)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# List all notification preferences
@router.get("/preferences", response_model=list[PreferenceItem])
async def read_preferences(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_preferences(db)


# Update a notification preference by type
@router.patch(
    "/preferences/{notification_type}",
    response_model=UpdatePreferenceResponse,
)
async def patch_preference(
    notification_type: str,
    body: UpdatePreferenceRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_preference(
            db,
            notification_type=notification_type,
            ui_enabled=body.ui_enabled,
            email_enabled=body.email_enabled,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
