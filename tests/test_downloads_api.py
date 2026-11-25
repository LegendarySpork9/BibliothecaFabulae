# Load libraries
import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.download_job import DownloadJob
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User


# Creates an authenticated user and returns authorization headers
async def _authenticated_headers(db: AsyncSession) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="dluser",
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


@pytest.mark.asyncio
# Lists downloads when no jobs exist
async def test_list_downloads_empty(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/fics/downloads", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
# Lists downloads when jobs exist
async def test_list_downloads_with_jobs(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    db_session.add(DownloadJob(url="https://example.com/1", status="queued", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/2", status="complete", source_site="ffnet"))
    await db_session.flush()

    resp = await client.get("/api/fics/downloads", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
# Filters downloads by status
async def test_list_downloads_filter_by_status(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    db_session.add(DownloadJob(url="https://example.com/1", status="complete", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/2", status="complete", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/3", status="queued", source_site="ao3"))
    await db_session.flush()

    resp = await client.get("/api/fics/downloads?status=complete", headers=headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2

    for item in data["items"]:
        assert item["status"] == "complete"


@pytest.mark.asyncio
# Clears only completed downloads
async def test_clear_completed_downloads(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    db_session.add(DownloadJob(url="https://example.com/1", status="complete", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/2", status="complete", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/3", status="failed", source_site="ao3"))
    await db_session.flush()

    resp = await client.delete("/api/fics/downloads/completed", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["cleared"] == 2

    list_resp = await client.get("/api/fics/downloads", headers=headers)
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["status"] == "failed"


@pytest.mark.asyncio
# Clears all downloads
async def test_clear_all_downloads(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    db_session.add(DownloadJob(url="https://example.com/1", status="complete", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/2", status="failed", source_site="ao3"))
    db_session.add(DownloadJob(url="https://example.com/3", status="queued", source_site="ao3"))
    await db_session.flush()

    resp = await client.delete("/api/fics/downloads", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["cleared"] == 3

    list_resp = await client.get("/api/fics/downloads", headers=headers)
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
# Rejects import of an unsupported URL
async def test_import_fic_bad_url(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.post(
        "/api/fics/import",
        json={"url": "https://example.com/not-a-fic"},
        headers=headers,
    )

    assert resp.status_code == 400
