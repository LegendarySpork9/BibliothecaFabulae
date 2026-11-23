# Load libraries
import hashlib
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.core.utils import utcnow
from backend.models.session import RefreshToken
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User


# Create a test user with TOTP configured and setup marked complete
async def _create_test_user(db: AsyncSession) -> User:
    import pyotp

    totp_secret = pyotp.random_base32()
    user = User(
        username="testuser",
        password_hash=hash_password("SecureP@ss123!"),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db.add(app_settings)
    await db.flush()

    return user


# Test that login with valid credentials returns 200 and a temp token
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    await _create_test_user(db_session)

    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "SecureP@ss123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["requires_totp"] is True
    assert data["temp_token"] is not None


# Test that login with wrong password returns 401
@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    await _create_test_user(db_session)

    response = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


# Test that login with a nonexistent username returns 401
@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient, db_session: AsyncSession):
    await _create_test_user(db_session)

    response = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "password"},
    )
    assert response.status_code == 401


# Test the complete login, TOTP verify, and token issuance flow
@pytest.mark.asyncio
async def test_full_auth_flow(client: AsyncClient, db_session: AsyncSession):
    import pyotp

    totp_secret = pyotp.random_base32()
    user = User(
        username="flowuser",
        password_hash=hash_password("SecureP@ss123!"),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db_session.add(user)
    app_settings = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db_session.add(app_settings)
    await db_session.flush()

    login_resp = await client.post(
        "/api/auth/login",
        json={"username": "flowuser", "password": "SecureP@ss123!"},
    )
    assert login_resp.status_code == 200
    temp_token = login_resp.json()["temp_token"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    totp_resp = await client.post(
        "/api/auth/verify-totp",
        json={
            "temp_token": temp_token,
            "totp_code": code,
            "remember_device": False,
            "device_name": "Test Client",
        },
    )
    assert totp_resp.status_code == 200
    access_token = totp_resp.json()["access_token"]
    assert access_token is not None

    cookies = totp_resp.cookies
    assert "refresh_token" in cookies


# Test that TOTP verification with a wrong code returns 401
@pytest.mark.asyncio
async def test_verify_totp_wrong_code(client: AsyncClient, db_session: AsyncSession):
    await _create_test_user(db_session)

    login_resp = await client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "SecureP@ss123!"},
    )
    temp_token = login_resp.json()["temp_token"]

    totp_resp = await client.post(
        "/api/auth/verify-totp",
        json={"temp_token": temp_token, "totp_code": "000000"},
    )
    assert totp_resp.status_code == 401


# Test that the setup guard blocks protected endpoints when setup is incomplete
@pytest.mark.asyncio
async def test_setup_guard_blocks_when_incomplete(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/api/auth/sessions")
    assert response.status_code in (401, 403)


# Test that the health endpoint is accessible regardless of setup state
@pytest.mark.asyncio
async def test_health_always_accessible(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/api/health")
    assert response.status_code == 200


# Test that POST /api/auth/refresh with a valid refresh token returns a new access token
@pytest.mark.asyncio
async def test_refresh_with_valid_token(
    client: AsyncClient, db_session: AsyncSession
):
    user = await _create_test_user(db_session)

    raw_token = "test-refresh-token-value-for-rotation"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name="Unknown browser on Unknown OS",
        remember_device=False,
        expires_at=utcnow() + timedelta(days=7),
        last_used_at=utcnow(),
    )
    db_session.add(refresh)
    await db_session.flush()

    response = await client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": raw_token},
    )
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# Test that POST /api/auth/refresh without a cookie returns 401
@pytest.mark.asyncio
async def test_refresh_without_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_test_user(db_session)

    response = await client.post("/api/auth/refresh")
    assert response.status_code == 401


# Test that POST /api/auth/logout clears the session and returns 204
@pytest.mark.asyncio
async def test_logout_clears_session(
    client: AsyncClient, db_session: AsyncSession
):
    user = await _create_test_user(db_session)

    raw_token = "logout-test-token-value"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name="Test Client",
        remember_device=False,
        expires_at=utcnow() + timedelta(days=7),
        last_used_at=utcnow(),
    )
    db_session.add(refresh)
    await db_session.flush()

    response = await client.post(
        "/api/auth/logout",
        cookies={"refresh_token": raw_token},
    )
    assert response.status_code == 204


# Test that POST /api/auth/logout without a cookie still returns 204
@pytest.mark.asyncio
async def test_logout_without_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_test_user(db_session)

    response = await client.post("/api/auth/logout")
    assert response.status_code == 204


# Test that GET /api/auth/sessions returns a session list for an authenticated user
@pytest.mark.asyncio
async def test_get_sessions_returns_list(
    client: AsyncClient, db_session: AsyncSession
):
    user = await _create_test_user(db_session)

    raw_token = "sessions-list-test-token"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name="Test Client",
        remember_device=False,
        expires_at=utcnow() + timedelta(days=7),
        last_used_at=utcnow(),
    )
    db_session.add(refresh)
    await db_session.flush()

    access_token = create_access_token(user.id)

    response = await client.get(
        "/api/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"refresh_token": raw_token},
    )
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "device_name" in data[0]
    assert "is_current" in data[0]


# Test that DELETE /api/auth/sessions/{id} revokes a session
@pytest.mark.asyncio
async def test_delete_session_revokes(
    client: AsyncClient, db_session: AsyncSession
):
    user = await _create_test_user(db_session)

    raw_token = "revoke-session-test-token"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    refresh = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        device_name="Test Client",
        remember_device=False,
        expires_at=utcnow() + timedelta(days=7),
        last_used_at=utcnow(),
    )
    db_session.add(refresh)
    await db_session.flush()

    session_id = refresh.id
    access_token = create_access_token(user.id)

    response = await client.delete(
        f"/api/auth/sessions/{session_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 204


# Test that DELETE /api/auth/sessions/{id} returns 404 for nonexistent session
@pytest.mark.asyncio
async def test_delete_session_not_found(
    client: AsyncClient, db_session: AsyncSession
):
    user = await _create_test_user(db_session)
    access_token = create_access_token(user.id)

    response = await client.delete(
        "/api/auth/sessions/99999",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404


# Test that GET /api/auth/mode returns cloudflare_trust status
@pytest.mark.asyncio
async def test_auth_mode_returns_cloudflare_trust(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_test_user(db_session)

    response = await client.get("/api/auth/mode")
    assert response.status_code == 200

    data = response.json()
    assert "cloudflare_trust" in data
    assert data["cloudflare_trust"] is False


# Test that POST /api/auth/totp-only returns 403 when cloudflare trust is disabled
@pytest.mark.asyncio
async def test_totp_only_blocked_without_cloudflare_trust(
    client: AsyncClient, db_session: AsyncSession
):
    await _create_test_user(db_session)

    response = await client.post(
        "/api/auth/totp-only",
        json={
            "totp_code": "123456",
            "remember_device": False,
        },
    )
    assert response.status_code == 403
