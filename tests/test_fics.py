# Load libraries
import os
import tempfile

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.downloader.fanficfare_wrapper import DownloadResult
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User
from backend.services.fic_service import store_downloaded_fic


async def _authenticated_headers(db: AsyncSession, storage_path: str) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="ficuser",
        password_hash=hash_password("TestPass123!"),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path=storage_path, setup_complete=True)
    db.add(app_settings)
    await db.flush()

    access_token = create_access_token(user.id)

    return {"Authorization": f"Bearer {access_token}"}


async def _store_test_fic(db: AsyncSession, storage_path: str, source_id: str = "12345") -> int:
    epub_path = os.path.join(storage_path, "test.epub")

    with open(epub_path, "w") as f:
        f.write("fake")

    result = DownloadResult(
        epub_path=epub_path,
        metadata={"title": "Test Story", "creators": ["Author"], "subjects": ["Tag1"]},
        chapters=[
            {"chapter_number": 1, "title": "Ch1", "html_content": "<p>Content</p>", "word_count": 1},
        ],
    )
    fic = await store_downloaded_fic(
        db, result, "ao3", source_id,
        f"https://archiveofourown.org/works/{source_id}", "manual_url",
    )

    return fic.id


@pytest.mark.asyncio
async def test_list_fics_empty(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        headers = await _authenticated_headers(db_session, tmpdir)
        resp = await client.get("/api/fics", headers=headers)

        assert resp.status_code == 200
        assert resp.json()["total"] == 0
        assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_list_fics_with_data(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        headers = await _authenticated_headers(db_session, storage_dir)
        await _store_test_fic(db_session, storage_dir)

        resp = await client.get("/api/fics", headers=headers)

        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["title"] == "Test Story"


@pytest.mark.asyncio
async def test_get_fic_detail(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        headers = await _authenticated_headers(db_session, storage_dir)
        fic_id = await _store_test_fic(db_session, storage_dir)

        resp = await client.get(f"/api/fics/{fic_id}", headers=headers)

        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Story"
        assert len(resp.json()["chapters"]) == 1


@pytest.mark.asyncio
async def test_get_fic_not_found(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        headers = await _authenticated_headers(db_session, tmpdir)
        resp = await client.get("/api/fics/9999", headers=headers)

        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_chapters(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        headers = await _authenticated_headers(db_session, storage_dir)
        fic_id = await _store_test_fic(db_session, storage_dir)

        resp = await client.get(f"/api/fics/{fic_id}/chapters", headers=headers)

        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Ch1"


@pytest.mark.asyncio
async def test_delete_fic(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = os.path.join(tmpdir, "storage")
        os.makedirs(storage_dir)
        headers = await _authenticated_headers(db_session, storage_dir)
        fic_id = await _store_test_fic(db_session, storage_dir)

        resp = await client.delete(f"/api/fics/{fic_id}", headers=headers)

        assert resp.status_code == 204


@pytest.mark.asyncio
async def test_import_bad_url(client: AsyncClient, db_session: AsyncSession):
    with tempfile.TemporaryDirectory() as tmpdir:
        headers = await _authenticated_headers(db_session, tmpdir)
        resp = await client.post(
            "/api/fics/import",
            json={"url": "https://example.com/not-a-fic"},
            headers=headers,
        )

        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_fics_require_auth(client: AsyncClient, db_session: AsyncSession):
    app_settings = SettingsModel(id=1, storage_path="./data", setup_complete=True)
    db_session.add(app_settings)
    await db_session.flush()

    resp = await client.get("/api/fics")

    assert resp.status_code in (401, 403)
