# Load libraries
import hashlib
import logging
import re
import uuid
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    create_access_token,
    create_temp_token,
    decode_token,
    verify_password,
    verify_totp,
)
from backend.core.config import settings
from backend.core.encryption import decrypt
from backend.core.security import login_attempts
from backend.core.utils import utcnow
from backend.models.session import RefreshToken
from backend.models.settings import Settings
from backend.models.user import User

logger = logging.getLogger(__name__)


# Hashes a raw token string using SHA-256
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


_UA_MAX_LENGTH = 256


# Strips control characters and caps length to prevent injection via User-Agent
def _sanitise_raw_ua(ua: str) -> str:
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", ua)
    return cleaned[:_UA_MAX_LENGTH]


# Extracts a human-readable browser and OS name from a user-agent string
def _parse_user_agent(ua: str | None) -> str:
    if not ua:
        return "Unknown"

    ua = _sanitise_raw_ua(ua)

    browser = "Unknown browser"

    if "Edg/" in ua:
        browser = "Edge"

    elif "Chrome/" in ua:
        browser = "Chrome"

    elif "Firefox/" in ua:
        browser = "Firefox"

    elif "Safari/" in ua:
        browser = "Safari"

    os_name = "Unknown OS"

    if "Windows" in ua:
        os_name = "Windows"

    elif "Mac OS" in ua or "Macintosh" in ua:
        os_name = "macOS"

    elif "Linux" in ua:
        os_name = "Linux"

    elif "Android" in ua:
        os_name = "Android"

    elif "iPhone" in ua or "iPad" in ua:
        os_name = "iOS"

    return f"{browser} on {os_name}"


# Issues a temporary TOTP verification token for the first user
async def get_totp_temp_token(db: AsyncSession) -> str | None:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if user is None:
        return None

    return create_temp_token(user.id)


# Validates username and password then returns a temporary token
async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> tuple[bool, str | None]:
    lockout_key = f"login:{username}"

    if login_attempts.is_locked_out(lockout_key):
        logger.warning("Account locked out due to repeated failures: %s", username)
        return False, None

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        login_attempts.record_failure(lockout_key)
        logger.warning("Failed login attempt for username: %s", username)
        return False, None

    login_attempts.clear(lockout_key)
    temp_token = create_temp_token(user.id)

    return True, temp_token


# Verifies a TOTP code and issues access and refresh tokens
async def verify_totp_and_issue_tokens(
    db: AsyncSession,
    temp_token: str,
    totp_code: str,
    remember_device: bool = False,
    device_name: str | None = None,
) -> tuple[bool, str | None, str | None]:
    try:
        payload = decode_token(temp_token)

    except Exception:
        return False, None, None, False

    if payload.get("scope") != "totp_verification":
        return False, None, None, False

    user_id = int(payload["sub"])
    totp_key = f"totp:{user_id}"

    if login_attempts.is_locked_out(totp_key):
        logger.warning("TOTP locked out due to repeated failures for user_id: %d", user_id)
        return False, None, None, False

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return False, None, None, False

    totp_secret = decrypt(
        user.totp_secret_encrypted,
        settings.ENCRYPTION_KEY,
        settings.ENCRYPTION_KEY_PREVIOUS or None,
    )

    if not verify_totp(totp_secret, totp_code):
        login_attempts.record_failure(totp_key)
        logger.warning("Failed TOTP verification for user_id: %d", user_id)
        return False, None, None, False

    login_attempts.clear(totp_key)
    access_token = create_access_token(user.id)

    refresh_token_raw = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = _hash_token(refresh_token_raw)

    if remember_device:
        expires_at = utcnow() + timedelta(days=7)

    else:
        expires_at = utcnow() + timedelta(hours=24)

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name=_parse_user_agent(device_name),
        remember_device=remember_device,
        expires_at=expires_at,
        last_used_at=utcnow(),
    )
    db.add(refresh)
    await db.flush()

    return True, access_token, refresh_token_raw, remember_device


# Rotates a refresh token and issues a new access token
async def refresh_tokens(
    db: AsyncSession, refresh_token_raw: str, current_ua: str | None = None
) -> tuple[bool, str | None, str | None]:
    token_hash = _hash_token(refresh_token_raw)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()

    if token_row is None or token_row.expires_at < utcnow():
        if token_row:
            await db.delete(token_row)
            await db.flush()

        return False, None, None, False

    if current_ua and token_row.device_name:
        parsed_ua = _parse_user_agent(current_ua)

        if parsed_ua != token_row.device_name:
            logger.warning(
                "Refresh token device mismatch: expected %r, got %r",
                token_row.device_name,
                parsed_ua,
            )
            await db.delete(token_row)
            await db.flush()

            return False, None, None, False

    user_id = token_row.user_id
    remember_device = token_row.remember_device
    device_name = token_row.device_name

    await db.delete(token_row)
    await db.flush()

    access_token = create_access_token(user_id)

    new_refresh_raw = uuid.uuid4().hex + uuid.uuid4().hex
    new_hash = _hash_token(new_refresh_raw)

    if remember_device:
        expires_at = utcnow() + timedelta(days=7)

    else:
        expires_at = utcnow() + timedelta(hours=24)

    new_token = RefreshToken(
        user_id=user_id,
        token_hash=new_hash,
        device_name=device_name,
        remember_device=remember_device,
        expires_at=expires_at,
        last_used_at=utcnow(),
    )
    db.add(new_token)
    await db.flush()

    return True, access_token, new_refresh_raw, remember_device


# Revokes a single refresh token by its raw value
async def logout(db: AsyncSession, refresh_token_raw: str) -> None:
    token_hash = _hash_token(refresh_token_raw)
    await db.execute(
        delete(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    await db.flush()


# Returns all active sessions for a user, flagging the current one
async def get_sessions(
    db: AsyncSession, user_id: int, current_refresh_token: str | None = None
) -> list[dict]:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    tokens = result.scalars().all()

    current_hash = _hash_token(current_refresh_token) if current_refresh_token else None

    sessions = []

    for t in tokens:
        sessions.append({
            "id": t.id,
            "device_name": t.device_name,
            "is_current": t.token_hash == current_hash,
            "remember_device": t.remember_device,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
            "expires_at": t.expires_at.isoformat(),
        })

    return sessions


# Revokes a specific session by its ID for a given user
async def revoke_session(db: AsyncSession, user_id: int, session_id: int) -> bool:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.id == session_id, RefreshToken.user_id == user_id
        )
    )
    token = result.scalar_one_or_none()

    if token is None:
        return False

    await db.delete(token)
    await db.flush()

    return True
