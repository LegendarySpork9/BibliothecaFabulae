# Load libraries
import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.settings import Settings as SettingsModel
from backend.models.source import Source
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


# Verifies that cancelling a sync for an existing source returns 200
@pytest.mark.asyncio
async def test_cancel_sync(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    source = Source(
        site_key="ao3",
        auth_type="none",
        is_enabled=True,
        auth_status="unknown",
    )
    db_session.add(source)
    await db_session.flush()

    resp = await client.post(f"/api/sources/{source.id}/cancel-sync", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "cancelling"


# Verifies that cancelling a sync for a non-existent source returns 404
@pytest.mark.asyncio
async def test_cancel_sync_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.post("/api/sources/999/cancel-sync", headers=headers)

    assert resp.status_code == 404


# Verifies that triggering a sync for an existing source returns 200
@pytest.mark.asyncio
async def test_trigger_sync(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    source = Source(
        site_key="ao3",
        auth_type="none",
        is_enabled=True,
        auth_status="unknown",
    )
    db_session.add(source)
    await db_session.flush()

    resp = await client.post(f"/api/sources/{source.id}/sync", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "syncing"


# Verifies that triggering a sync for a non-existent source returns 404
@pytest.mark.asyncio
async def test_trigger_sync_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.post("/api/sources/999/sync", headers=headers)

    assert resp.status_code == 404


# Verifies that getting sync state for a source returns default values
@pytest.mark.asyncio
async def test_get_sync_state(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    source = Source(
        site_key="ao3",
        auth_type="none",
        is_enabled=True,
        auth_status="unknown",
    )
    db_session.add(source)
    await db_session.flush()

    resp = await client.get(f"/api/sources/{source.id}/sync-state", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["source_site"] == "ao3"
    assert data["last_synced"] is None
    assert data["total_synced"] == 0


# Verifies that listing scheduled jobs returns a list
@pytest.mark.asyncio
async def test_list_scheduled_jobs(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/sources/scheduler/jobs", headers=headers)

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
