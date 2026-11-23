# Load libraries
import tempfile

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.notification import NotificationPreference
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User

VALID_PASSWORD = "SecureP@ss123!"


# Create a user with setup complete and return authorisation headers
async def _authenticated_headers(db: AsyncSession) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="settingsuser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db.add(app_settings)

    for ntype in [
        "fic_updated",
        "sync_complete",
        "sync_failed",
        "auth_required",
        "storage_low",
        "fic_unavailable",
        "scanner_new_works",
        "audio_ready",
    ]:
        db.add(
            NotificationPreference(
                notification_type=ntype,
                ui_enabled=True,
                email_enabled=False,
            )
        )

    await db.flush()

    access_token = create_access_token(user.id)

    return {"Authorization": f"Bearer {access_token}"}


# Test that GET /api/settings returns settings for an authenticated user
@pytest.mark.asyncio
async def test_get_settings(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/settings", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "storage_path" in data
    assert "theme" in data
    assert data["setup_complete"] is True


# Test that GET /api/settings returns theme and storage path values
@pytest.mark.asyncio
async def test_get_settings_contains_expected_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/settings", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["storage_path"] == "/tmp/test"
    assert data["theme"] == "dark"
    assert data["remember_device_days"] == 30
    assert data["smtp_password_configured"] is False


# Test that patching theme to dark succeeds
@pytest.mark.asyncio
async def test_patch_theme_dark(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/theme",
        json={"theme": "dark"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "dark"


# Test that patching theme to light succeeds
@pytest.mark.asyncio
async def test_patch_theme_light(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/theme",
        json={"theme": "light"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "light"


# Test that patching theme with an invalid value returns 400
@pytest.mark.asyncio
async def test_patch_theme_invalid(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/theme",
        json={"theme": "blue"},
        headers=headers,
    )
    assert response.status_code == 400


# Test that GET /api/account returns the username
@pytest.mark.asyncio
async def test_get_account(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/account", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["username"] == "settingsuser"
    assert data["totp_enabled"] is True


# Test that GET /api/storage returns storage information
@pytest.mark.asyncio
async def test_get_storage(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    with tempfile.TemporaryDirectory() as tmp_dir:
        from sqlalchemy import select

        result = await db_session.execute(
            select(SettingsModel).where(SettingsModel.id == 1)
        )
        settings_row = result.scalar_one()
        settings_row.storage_path = tmp_dir
        await db_session.flush()

        response = await client.get("/api/storage", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "storage_path" in data
        assert data["disk_total_bytes"] > 0
        assert data["disk_free_bytes"] > 0
        assert "breakdown" in data


# Test that GET /api/settings without auth returns 401 or 403
@pytest.mark.asyncio
async def test_get_settings_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/api/settings")
    assert response.status_code in (401, 403)


# Test that PATCH /api/settings/theme without auth returns 401 or 403
@pytest.mark.asyncio
async def test_patch_theme_unauthenticated(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.patch(
        "/api/settings/theme",
        json={"theme": "dark"},
    )
    assert response.status_code in (401, 403)


# Test that patching theme persists across subsequent reads
@pytest.mark.asyncio
async def test_patch_theme_persists(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    await client.patch(
        "/api/settings/theme",
        json={"theme": "light"},
        headers=headers,
    )

    response = await client.get("/api/settings", headers=headers)
    assert response.status_code == 200
    assert response.json()["theme"] == "light"


# Test that GET /api/account returns created_at timestamp
@pytest.mark.asyncio
async def test_get_account_has_created_at(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/account", headers=headers)
    assert response.status_code == 200
    assert "created_at" in response.json()


# Test that GET /api/storage with unconfigured path returns 400
@pytest.mark.asyncio
async def test_get_storage_unconfigured_path(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    from sqlalchemy import select

    result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = result.scalar_one()
    settings_row.storage_path = ""
    await db_session.flush()

    response = await client.get("/api/storage", headers=headers)
    assert response.status_code == 400
