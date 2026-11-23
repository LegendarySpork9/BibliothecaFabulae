# Load libraries
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token
from backend.core.database import get_db
from backend.core.security import limiter
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User
from backend.services.auth_service import _hash_token
from backend.services.email_service import test_smtp_connection, test_smtp_with_values
from backend.services.setup_service import (
    complete_setup,
    configure_smtp,
    configure_storage,
    create_account,
    get_setup_status,
    verify_setup_totp,
)

router = APIRouter(prefix="/api/setup", tags=["setup"])


# Setup status response with current step
class SetupStatusResponse(BaseModel):
    setup_complete: bool
    current_step: int
    storage_path: str = ""
    smtp_configured: bool = False


# Account creation request body
class CreateAccountRequest(BaseModel):
    username: str
    password: str
    password_confirm: str


# Account creation response with TOTP provisioning data
class CreateAccountResponse(BaseModel):
    totp_secret: str
    totp_uri: str
    qr_code_base64: str


# TOTP verification request body
class VerifyTotpRequest(BaseModel):
    totp_code: str


# TOTP verification result
class VerifyTotpResponse(BaseModel):
    verified: bool


# Storage path configuration request body
class StorageRequest(BaseModel):
    storage_path: str


# Storage path validation response with disk info
class StorageResponse(BaseModel):
    valid: bool
    total_bytes: int
    free_bytes: int


# SMTP configuration request body
class SmtpRequest(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_from_address: str
    smtp_to_address: str


# SMTP configuration result
class SmtpResponse(BaseModel):
    configured: bool


# SMTP connection test result
class SmtpTestResponse(BaseModel):
    success: bool
    message: str


# SMTP connection test request body
class SmtpTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool = True


# Setup completion response with initial access token
class CompleteResponse(BaseModel):
    success: bool
    access_token: str


# Reject the request if setup has already been completed
async def _guard_setup_complete(db: AsyncSession) -> None:
    result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row and settings_row.setup_complete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup already complete",
        )


# Return the current setup wizard progress
@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(db: AsyncSession = Depends(get_db)):
    return await get_setup_status(db)


# Create the admin account and generate TOTP provisioning data
@router.post("/account", response_model=CreateAccountResponse)
@limiter.limit("3/minute")
async def setup_account(
    request: Request,
    body: CreateAccountRequest,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    if body.password != body.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    try:
        result = await create_account(db, body.username, body.password)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


# Verify the TOTP code during setup
@router.post("/verify-totp", response_model=VerifyTotpResponse)
@limiter.limit("5/minute")
async def setup_verify_totp(
    request: Request,
    body: VerifyTotpRequest,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    try:
        result = await verify_setup_totp(db, body.totp_code)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


# Validate and configure the storage path
@router.post("/storage", response_model=StorageResponse)
@limiter.limit("5/minute")
async def setup_storage(
    request: Request,
    body: StorageRequest,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    try:
        result = await configure_storage(db, body.storage_path)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return result


# Configure SMTP email settings
@router.post("/smtp", response_model=SmtpResponse)
@limiter.limit("5/minute")
async def setup_smtp(
    request: Request,
    body: SmtpRequest,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    try:
        result = await configure_smtp(
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

    return result


# Test the provided SMTP connection settings
@router.post("/smtp/test", response_model=SmtpTestResponse)
@limiter.limit("3/minute")
async def setup_smtp_test(
    request: Request,
    body: SmtpTestRequest,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    return test_smtp_with_values(
        host=body.smtp_host,
        port=body.smtp_port,
        username=body.smtp_username,
        password=body.smtp_password,
        use_tls=body.smtp_use_tls,
    )


# Finalise setup and issue the first access token
@router.post("/complete", response_model=CompleteResponse)
@limiter.limit("3/minute")
async def setup_complete(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    await _guard_setup_complete(db)

    try:
        await complete_setup(db)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one()
    access_token = create_access_token(user.id)

    import hashlib
    import uuid
    from datetime import timedelta
    from backend.core.utils import utcnow
    from backend.models.session import RefreshToken

    refresh_token_raw = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = hashlib.sha256(refresh_token_raw.encode()).hexdigest()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name="Setup",
        remember_device=False,
        expires_at=utcnow() + timedelta(days=7),
        last_used_at=utcnow(),
    )
    db.add(refresh)
    await db.flush()

    from backend.core.config import settings as app_settings

    response.set_cookie(
        key="refresh_token",
        value=refresh_token_raw,
        httponly=True,
        secure=app_settings.ENVIRONMENT != "development",
        samesite="strict" if app_settings.ENVIRONMENT != "development" else "lax",
        max_age=30 * 24 * 60 * 60,
        path="/api/auth",
    )

    return CompleteResponse(success=True, access_token=access_token)
