# Load libraries
import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User


# Creates an authenticated user and returns JWT headers
async def _authenticated_headers(db: AsyncSession) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="testuser",
        password_hash=hash_password("TestPass123!"),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path="./data", setup_complete=True)
    db.add(app_settings)
    await db.flush()

    access_token = create_access_token(user.id)

    return {"Authorization": f"Bearer {access_token}"}


# Verifies that the update status endpoint returns bulk_running and checking_fic_ids
@pytest.mark.asyncio
async def test_get_update_status(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/fics/update-status", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "bulk_running" in data
    assert "checking_fic_ids" in data
    assert data["bulk_running"] is False
    assert isinstance(data["checking_fic_ids"], list)


# Verifies that the sites endpoint returns a list
@pytest.mark.asyncio
async def test_list_supported_sites(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/fics/sites", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
