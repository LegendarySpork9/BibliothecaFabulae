# Load libraries
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
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
