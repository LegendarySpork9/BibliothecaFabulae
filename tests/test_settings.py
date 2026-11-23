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


# Test that PATCH /api/settings/smtp saves SMTP configuration
@pytest.mark.asyncio
async def test_patch_smtp(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/smtp",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_password": "secret",
            "smtp_use_tls": True,
            "smtp_from_address": "from@example.com",
            "smtp_to_address": "to@example.com",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["configured"] is True


# Test that PATCH /api/settings/backup saves backup configuration
@pytest.mark.asyncio
async def test_patch_backup(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/backup",
        json={
            "backup_location": "/tmp/backups",
            "backup_schedule": "daily",
        },
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["backup_location"] == "/tmp/backups"
    assert data["backup_schedule"] == "daily"


# Test that PATCH /api/settings/remember-device with valid days succeeds
@pytest.mark.asyncio
async def test_patch_remember_device_valid(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/remember-device",
        json={"days": 14},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["remember_device_days"] == 14


# Test that PATCH /api/settings/remember-device with 0 days returns 400
@pytest.mark.asyncio
async def test_patch_remember_device_zero(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/remember-device",
        json={"days": 0},
        headers=headers,
    )
    assert response.status_code == 400


# Test that PATCH /api/settings/remember-device with 400 days returns 400
@pytest.mark.asyncio
async def test_patch_remember_device_too_high(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/remember-device",
        json={"days": 400},
        headers=headers,
    )
    assert response.status_code == 400


# Test that PATCH /api/account/password with correct current password succeeds
@pytest.mark.asyncio
async def test_patch_password_success(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/account/password",
        json={
            "current_password": VALID_PASSWORD,
            "new_password": "NewSecureP@ss456!",
            "new_password_confirm": "NewSecureP@ss456!",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


# Test that PATCH /api/account/password with wrong current password returns 400
@pytest.mark.asyncio
async def test_patch_password_wrong_current(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/account/password",
        json={
            "current_password": "WrongP@ssword123!",
            "new_password": "NewSecureP@ss456!",
            "new_password_confirm": "NewSecureP@ss456!",
        },
        headers=headers,
    )
    assert response.status_code == 400


# Test that PATCH /api/settings/cloudflare-trust toggles the setting
@pytest.mark.asyncio
async def test_patch_cloudflare_trust(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/settings/cloudflare-trust",
        json={"enabled": True},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["cloudflare_trust_enabled"] is True

    response = await client.patch(
        "/api/settings/cloudflare-trust",
        json={"enabled": False},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["cloudflare_trust_enabled"] is False


# Test that POST /api/account/totp/regenerate returns new QR data
@pytest.mark.asyncio
async def test_totp_regenerate(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    response = await client.post(
        "/api/account/totp/regenerate",
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "totp_secret" in data
    assert "totp_uri" in data
    assert "qr_code_base64" in data
    assert len(data["totp_secret"]) > 0


# Test that POST /api/settings/smtp/test returns a response when SMTP is not configured
@pytest.mark.asyncio
async def test_smtp_test_unconfigured(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.post("/api/settings/smtp/test", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "success" in data
    assert "message" in data
    assert data["success"] is False


# Test that POST /api/account/totp/regenerate returns valid QR data with URI
@pytest.mark.asyncio
async def test_totp_regenerate_contains_uri(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.post(
        "/api/account/totp/regenerate",
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "otpauth://" in data["totp_uri"]
    assert "BibliothecaFabulae" in data["totp_uri"]


# Test that GET /api/storage/warnings returns a list
@pytest.mark.asyncio
async def test_storage_warnings_returns_list(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/storage/warnings", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
