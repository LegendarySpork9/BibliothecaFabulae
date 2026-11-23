# Load libraries
import pyotp
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_temp_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.core.security import login_attempts
from backend.models.user import User
from backend.services.auth_service import (
    authenticate_user,
    refresh_tokens,
    verify_totp_and_issue_tokens,
)

VALID_PASSWORD = "SecureP@ss123!"


# Create a user with known password and encrypted TOTP secret, return (user, totp_secret)
async def _create_user_with_totp(db: AsyncSession) -> tuple[User, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="authuser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)
    await db.flush()

    return user, totp_secret


# Test that verify_totp_and_issue_tokens succeeds with valid temp token and correct TOTP code
@pytest.mark.asyncio
async def test_verify_totp_valid(db_session: AsyncSession):
    login_attempts.reset()
    user, totp_secret = await _create_user_with_totp(db_session)

    temp_token = create_temp_token(user.id)
    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    success, access_token, refresh_token = await verify_totp_and_issue_tokens(
        db_session, temp_token, code
    )

    assert success is True
    assert access_token is not None
    assert refresh_token is not None
    assert len(access_token) > 0
    assert len(refresh_token) > 0


# Test that verify_totp_and_issue_tokens fails with invalid temp token
@pytest.mark.asyncio
async def test_verify_totp_invalid_temp_token(db_session: AsyncSession):
    login_attempts.reset()

    success, access_token, refresh_token = await verify_totp_and_issue_tokens(
        db_session, "invalid-token", "123456"
    )

    assert success is False
    assert access_token is None
    assert refresh_token is None


# Test that verify_totp_and_issue_tokens fails with wrong TOTP code
@pytest.mark.asyncio
async def test_verify_totp_wrong_code(db_session: AsyncSession):
    login_attempts.reset()
    user, totp_secret = await _create_user_with_totp(db_session)

    temp_token = create_temp_token(user.id)

    success, access_token, refresh_token = await verify_totp_and_issue_tokens(
        db_session, temp_token, "000000"
    )

    assert success is False
    assert access_token is None
    assert refresh_token is None


# Test that verify_totp_and_issue_tokens fails with non-totp scope token
@pytest.mark.asyncio
async def test_verify_totp_wrong_scope(db_session: AsyncSession):
    login_attempts.reset()
    user, totp_secret = await _create_user_with_totp(db_session)

    # Create an access token instead of a temp token
    from backend.core.auth import create_access_token

    access_token = create_access_token(user.id)

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    success, at, rt = await verify_totp_and_issue_tokens(
        db_session, access_token, code
    )

    assert success is False
    assert at is None
    assert rt is None


# Test that verify_totp_and_issue_tokens with remember_device sets longer expiry
@pytest.mark.asyncio
async def test_verify_totp_remember_device(db_session: AsyncSession):
    login_attempts.reset()
    user, totp_secret = await _create_user_with_totp(db_session)

    temp_token = create_temp_token(user.id)
    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    success, access_token, refresh_token = await verify_totp_and_issue_tokens(
        db_session,
        temp_token,
        code,
        remember_device=True,
        device_name="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    )

    assert success is True
    assert access_token is not None
    assert refresh_token is not None


# Test that refresh_tokens updates last_used_at
@pytest.mark.asyncio
async def test_refresh_tokens_updates_last_used(db_session: AsyncSession):
    login_attempts.reset()
    user, totp_secret = await _create_user_with_totp(db_session)

    temp_token = create_temp_token(user.id)
    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    # First issue tokens via TOTP verification
    success, _, refresh_raw = await verify_totp_and_issue_tokens(
        db_session, temp_token, code
    )
    assert success is True

    # Now refresh
    success2, new_access, new_refresh = await refresh_tokens(db_session, refresh_raw)
    assert success2 is True
    assert new_access is not None
    assert new_refresh is not None
    assert new_refresh != refresh_raw


# Test that authenticate_user succeeds with valid credentials
@pytest.mark.asyncio
async def test_authenticate_user_valid(db_session: AsyncSession):
    login_attempts.reset()
    await _create_user_with_totp(db_session)

    success, temp_token = await authenticate_user(
        db_session, "authuser", VALID_PASSWORD
    )

    assert success is True
    assert temp_token is not None
    assert len(temp_token) > 0


# Test that authenticate_user fails with invalid password
@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession):
    login_attempts.reset()
    await _create_user_with_totp(db_session)

    success, temp_token = await authenticate_user(
        db_session, "authuser", "WrongP@ssword123!"
    )

    assert success is False
    assert temp_token is None


# Test that authenticate_user fails with nonexistent user
@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_user(db_session: AsyncSession):
    login_attempts.reset()

    success, temp_token = await authenticate_user(
        db_session, "nonexistent", VALID_PASSWORD
    )

    assert success is False
    assert temp_token is None


# Test that authenticate_user locks out after repeated failures
@pytest.mark.asyncio
async def test_authenticate_user_lockout(db_session: AsyncSession):
    login_attempts.reset()
    await _create_user_with_totp(db_session)

    # Fail 5 times to trigger lockout
    for _ in range(5):
        await authenticate_user(db_session, "authuser", "WrongP@ss123!")

    # Next attempt should be locked out even with correct password
    success, temp_token = await authenticate_user(
        db_session, "authuser", VALID_PASSWORD
    )

    assert success is False
    assert temp_token is None

    login_attempts.reset()
