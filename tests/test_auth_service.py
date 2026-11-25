# Load libraries
from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.core.utils import utcnow
from backend.models.session import RefreshToken
from backend.models.user import User
from backend.services.auth_service import (
    _hash_token,
    _parse_user_agent,
    _sanitise_raw_ua,
    get_sessions,
    logout,
    refresh_tokens,
    revoke_session,
)

VALID_PASSWORD = "SecureP@ss123!"


# Create a user and return the model instance
async def _create_user(db: AsyncSession) -> User:
    import pyotp

    totp_secret = pyotp.random_base32()
    user = User(
        username="authuser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)
    await db.flush()

    return user


# Create a refresh token row in the database and return the raw token
async def _create_refresh_token(
    db: AsyncSession,
    user_id: int,
    *,
    device_name: str = "Chrome on Windows",
    remember_device: bool = False,
    expired: bool = False,
) -> str:
    import uuid

    raw_token = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = _hash_token(raw_token)

    if expired:
        expires_at = utcnow() - timedelta(hours=1)

    else:
        expires_at = utcnow() + timedelta(hours=24)

    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        device_name=device_name,
        remember_device=remember_device,
        expires_at=expires_at,
        last_used_at=utcnow(),
    )
    db.add(token)
    await db.flush()

    return raw_token


# Test that _parse_user_agent identifies Chrome on Windows
def test_parse_user_agent_chrome_windows():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    result = _parse_user_agent(ua)
    assert result == "Chrome on Windows"


# Test that _parse_user_agent identifies Firefox on Linux
def test_parse_user_agent_firefox_linux():
    ua = "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
    result = _parse_user_agent(ua)
    assert result == "Firefox on Linux"


# Test that _parse_user_agent identifies Edge on macOS
def test_parse_user_agent_edge_macos():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    result = _parse_user_agent(ua)
    assert result == "Edge on macOS"


# Test that _parse_user_agent identifies Safari on iOS
def test_parse_user_agent_safari_ios():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    result = _parse_user_agent(ua)
    assert result == "Safari on macOS"


# Test that _parse_user_agent identifies Android
def test_parse_user_agent_android():
    ua = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    result = _parse_user_agent(ua)
    assert result == "Chrome on Linux"


# Test that _parse_user_agent returns Unknown for an empty string
def test_parse_user_agent_empty_string():
    result = _parse_user_agent("")
    assert result == "Unknown"


# Test that _parse_user_agent returns Unknown for None
def test_parse_user_agent_none():
    result = _parse_user_agent(None)
    assert result == "Unknown"


# Test that _hash_token returns a consistent 64-character hex SHA-256 digest
def test_hash_token_consistent_hex():
    token = "test-token-value"
    hashed = _hash_token(token)
    assert len(hashed) == 64
    assert all(c in "0123456789abcdef" for c in hashed)

    second_hash = _hash_token(token)
    assert hashed == second_hash


# Test that _sanitise_raw_ua strips control characters
def test_sanitise_raw_ua_strips_control_chars():
    ua = "Mozilla/5.0\x00\x01\x1f\x7f (Windows)"
    result = _sanitise_raw_ua(ua)
    assert "\x00" not in result
    assert "\x01" not in result
    assert "\x1f" not in result
    assert "\x7f" not in result
    assert "Mozilla/5.0 (Windows)" == result


# Test that _sanitise_raw_ua caps length at 256 characters
def test_sanitise_raw_ua_caps_length():
    ua = "A" * 500
    result = _sanitise_raw_ua(ua)
    assert len(result) == 256


# Test that refreshing a valid token succeeds and rotates it
@pytest.mark.asyncio
async def test_refresh_tokens_valid(db_session: AsyncSession):
    user = await _create_user(db_session)
    raw_token = await _create_refresh_token(db_session, user.id)

    success, access_token, new_refresh, _remember = await refresh_tokens(db_session, raw_token)
    assert success is True
    assert access_token is not None
    assert new_refresh is not None
    assert new_refresh != raw_token


# Test that refreshing an expired token fails
@pytest.mark.asyncio
async def test_refresh_tokens_expired(db_session: AsyncSession):
    user = await _create_user(db_session)
    raw_token = await _create_refresh_token(db_session, user.id, expired=True)

    success, access_token, new_refresh, _remember = await refresh_tokens(db_session, raw_token)
    assert success is False
    assert access_token is None
    assert new_refresh is None


# Test that logout deletes the token from the database
@pytest.mark.asyncio
async def test_logout_deletes_token(db_session: AsyncSession):
    user = await _create_user(db_session)
    raw_token = await _create_refresh_token(db_session, user.id)

    await logout(db_session, raw_token)

    success, _, _, _remember = await refresh_tokens(db_session, raw_token)
    assert success is False


# Test that get_sessions returns a list with the is_current flag set
@pytest.mark.asyncio
async def test_get_sessions_returns_list_with_current_flag(
    db_session: AsyncSession,
):
    user = await _create_user(db_session)
    raw_token = await _create_refresh_token(db_session, user.id)
    await _create_refresh_token(db_session, user.id, device_name="Firefox on Linux")

    sessions = await get_sessions(db_session, user.id, raw_token)
    assert len(sessions) == 2

    current_sessions = [s for s in sessions if s["is_current"]]
    assert len(current_sessions) == 1
    assert current_sessions[0]["device_name"] == "Chrome on Windows"


# Test that revoking a valid session succeeds
@pytest.mark.asyncio
async def test_revoke_session_valid(db_session: AsyncSession):
    user = await _create_user(db_session)
    raw_token = await _create_refresh_token(db_session, user.id)

    sessions = await get_sessions(db_session, user.id)
    session_id = sessions[0]["id"]

    result = await revoke_session(db_session, user.id, session_id)
    assert result is True

    remaining = await get_sessions(db_session, user.id)
    assert len(remaining) == 0


# Test that revoking an invalid session ID returns False
@pytest.mark.asyncio
async def test_revoke_session_invalid_id(db_session: AsyncSession):
    user = await _create_user(db_session)

    result = await revoke_session(db_session, user.id, 99999)
    assert result is False
