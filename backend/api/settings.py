# Load libraries
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_db
from backend.core.security import limiter
from backend.models.user import User
from backend.services.email_service import test_smtp_connection
from backend.services.settings_service import (
    change_password,
    confirm_new_totp,
    get_account,
    get_settings,
    regenerate_totp,
    update_backup,
    update_remember_device,
    update_smtp,
    update_storage_path,
    update_theme,
)
from backend.services.storage_service import get_storage_info, get_storage_warnings

router = APIRouter(prefix="/api", tags=["settings"])


# Storage path update request body
class StoragePathRequest(BaseModel):
    storage_path: str


# Theme selection request body
class ThemeRequest(BaseModel):
    theme: str


# SMTP configuration update request body
class SmtpUpdateRequest(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str
    smtp_to_address: str


# Backup configuration request body
class BackupRequest(BaseModel):
    backup_location: str
    backup_schedule: str


# Cloudflare trust toggle request body
class CloudflareTrustRequest(BaseModel):
    enabled: bool


# Remember device duration request body
class RememberDeviceRequest(BaseModel):
    days: int


# Password change request body
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str


# TOTP confirmation request body
class TotpConfirmRequest(BaseModel):
    totp_code: str
    pending_secret: str


# TOTP regeneration response with provisioning data
class TotpRegenerateResponse(BaseModel):
    totp_secret: str
    totp_uri: str
    qr_code_base64: str


# SMTP connection test result
class SmtpTestResponse(BaseModel):
    success: bool
    message: str


# Return all application settings
@router.get("/settings")
async def read_settings(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_settings(db)


# Update the storage path
@router.patch("/settings/storage")
@limiter.limit("5/minute")
async def patch_storage(
    request: Request,
    body: StoragePathRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_storage_path(db, body.storage_path)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Update the UI theme preference
@router.patch("/settings/theme")
async def patch_theme(
    body: ThemeRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_theme(db, body.theme)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Update the SMTP email configuration
@router.patch("/settings/smtp")
@limiter.limit("5/minute")
async def patch_smtp(
    request: Request,
    body: SmtpUpdateRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_smtp(
            db,
            host=body.smtp_host,
            port=body.smtp_port,
            username=body.smtp_username,
            password=body.smtp_password,
            use_tls=body.smtp_use_tls,
            from_address=body.smtp_from_address,
            to_address=body.smtp_to_address,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Test the saved SMTP connection settings
@router.post("/settings/smtp/test", response_model=SmtpTestResponse)
async def settings_smtp_test(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await test_smtp_connection(db)


# Update backup location and schedule
@router.patch("/settings/backup")
async def patch_backup(
    body: BackupRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_backup(db, body.backup_location, body.backup_schedule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Toggle Cloudflare trust mode on or off
@router.patch("/settings/cloudflare-trust")
@limiter.limit("3/minute")
async def patch_cloudflare_trust(
    request: Request,
    body: CloudflareTrustRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from backend.models.settings import Settings as SettingsModel

    result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row:
        settings_row.cloudflare_trust_enabled = body.enabled
        await db.flush()

    return {"cloudflare_trust_enabled": body.enabled}


# Update the remember device duration in days
@router.patch("/settings/remember-device")
async def patch_remember_device(
    body: RememberDeviceRequest,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await update_remember_device(db, body.days)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Return the current user account details
@router.get("/account")
async def read_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_account(db, user.id)


# Change the current user password
@router.patch("/account/password")
@limiter.limit("3/minute")
async def patch_password(
    request: Request,
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.new_password != body.new_password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    try:
        return await change_password(db, user.id, body.current_password, body.new_password)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Regenerate the TOTP secret and return new provisioning data
@router.post("/account/totp/regenerate", response_model=TotpRegenerateResponse)
@limiter.limit("3/minute")
async def totp_regenerate(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await regenerate_totp(db, user.id)


# Confirm the new TOTP secret with a valid code
@router.post("/account/totp/confirm")
@limiter.limit("5/minute")
async def totp_confirm(
    request: Request,
    body: TotpConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await confirm_new_totp(db, user.id, body.totp_code, body.pending_secret)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Return storage usage and capacity information
@router.get("/storage")
async def read_storage(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_storage_info(db)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# Return any active storage warnings
@router.get("/storage/warnings")
async def read_storage_warnings(
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_storage_warnings(db)
