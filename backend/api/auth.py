# Load libraries
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.core.database import get_db
from backend.core.security import limiter
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User
from backend.services.auth_service import (
    authenticate_user,
    get_sessions,
    get_totp_temp_token,
    logout,
    refresh_tokens,
    revoke_session,
    verify_totp_and_issue_tokens,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_MAX_AGE = 30 * 24 * 60 * 60


# Login request body
class LoginRequest(BaseModel):
    username: str
    password: str


# Login response with TOTP requirement
class LoginResponse(BaseModel):
    requires_totp: bool
    temp_token: str | None = None
    cloudflare_trust: bool = False


# TOTP-only authentication request body
class TotpOnlyRequest(BaseModel):
    totp_code: str
    remember_device: bool = False
    device_name: str | None = None


# TOTP verification request body
class VerifyTotpRequest(BaseModel):
    temp_token: str
    totp_code: str
    remember_device: bool = False
    device_name: str | None = None


# Token response with access token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Auth mode response indicating Cloudflare trust status
class AuthModeResponse(BaseModel):
    cloudflare_trust: bool


# Set the refresh token as an HTTP-only cookie on the response
def _set_refresh_cookie(response: Response, token: str, remember: bool = False) -> None:
    from backend.core.config import settings as app_settings

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=app_settings.ENVIRONMENT != "development",
        samesite="strict" if app_settings.ENVIRONMENT != "development" else "lax",
        max_age=7 * 24 * 60 * 60 if remember else None,
        path="/api/auth",
    )


# Remove the refresh token cookie from the response
def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
    )


# Return the current authentication mode configuration
@router.get("/mode", response_model=AuthModeResponse)
async def auth_mode(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
    settings_row = result.scalar_one_or_none()

    return AuthModeResponse(
        cloudflare_trust=settings_row.cloudflare_trust_enabled if settings_row else False
    )


# Handle user login and return a temporary token
@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    success, temp_token = await authenticate_user(db, body.username, body.password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    return LoginResponse(requires_totp=True, temp_token=temp_token)


# Authenticate via TOTP only when Cloudflare trust mode is enabled
@router.post("/totp-only", response_model=TokenResponse)
@limiter.limit("5/minute")
async def totp_only(
    request: Request,
    response: Response,
    body: TotpOnlyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SettingsModel).where(SettingsModel.id == 1))
    settings_row = result.scalar_one_or_none()

    if not settings_row or not settings_row.cloudflare_trust_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cloudflare trust mode is not enabled",
        )

    if not request.headers.get("CF-Connecting-IP"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request does not appear to originate from Cloudflare",
        )

    temp_token = await get_totp_temp_token(db)

    if not temp_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user account found",
        )

    success, access_token, refresh_token, _remember = await verify_totp_and_issue_tokens(
        db,
        temp_token,
        body.totp_code,
        body.remember_device,
        body.device_name or request.headers.get("User-Agent", "Unknown"),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )

    _set_refresh_cookie(response, refresh_token, body.remember_device)

    return TokenResponse(access_token=access_token)


# Verify the TOTP code and issue access and refresh tokens
@router.post("/verify-totp", response_model=TokenResponse)
@limiter.limit("5/minute")
async def verify_totp(
    request: Request,
    response: Response,
    body: VerifyTotpRequest,
    db: AsyncSession = Depends(get_db),
):
    success, access_token, refresh_token, _remember = await verify_totp_and_issue_tokens(
        db,
        body.temp_token,
        body.totp_code,
        body.remember_device,
        body.device_name or request.headers.get("User-Agent", "Unknown"),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code or expired token",
        )

    _set_refresh_cookie(response, refresh_token, body.remember_device)

    return TokenResponse(access_token=access_token)


# Rotate the refresh token and return a new access token
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    current_ua = request.headers.get("User-Agent")
    success, access_token, new_refresh, remember = await refresh_tokens(
        db, refresh_token, current_ua
    )

    if not success:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    _set_refresh_cookie(response, new_refresh, remember=remember)

    return TokenResponse(access_token=access_token)


# Revoke the current session and clear the refresh cookie
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
):
    if refresh_token:
        await logout(db, refresh_token)

    _clear_refresh_cookie(response)


# List all active sessions for the current user
@router.get("/sessions")
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
):
    return await get_sessions(db, user.id, refresh_token)


# Revoke a specific session by its ID
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await revoke_session(db, user.id, session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
