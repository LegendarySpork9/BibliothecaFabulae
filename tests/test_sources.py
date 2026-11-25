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


async def _authenticated_headers(db: AsyncSession) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="sourceuser",
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
async def test_list_supported_sites(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/sources/supported", headers=headers)

    assert resp.status_code == 200
    sites = resp.json()
    assert len(sites) > 0
    site_keys = [s["site_key"] for s in sites]
    assert "ao3" in site_keys


@pytest.mark.asyncio
async def test_create_source_via_api(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.post(
        "/api/sources",
        json={"site_key": "ao3", "auth_type": "credentials", "auth_data": "secret"},
        headers=headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["site_key"] == "ao3"
    assert data["auth_configured"] is True
    assert "auth_data" not in data


@pytest.mark.asyncio
async def test_create_source_bad_site(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.post(
        "/api/sources",
        json={"site_key": "badsite"},
        headers=headers,
    )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_sources(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    await client.post(
        "/api/sources",
        json={"site_key": "ao3", "auth_type": "credentials"},
        headers=headers,
    )

    resp = await client.get("/api/sources", headers=headers)

    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_source_by_id(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    create_resp = await client.post(
        "/api/sources",
        json={"site_key": "adultfanfiction", "auth_type": "none"},
        headers=headers,
    )
    source_id = create_resp.json()["id"]

    resp = await client.get(f"/api/sources/{source_id}", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["site_key"] == "adultfanfiction"


@pytest.mark.asyncio
async def test_get_source_not_found(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    resp = await client.get("/api/sources/9999", headers=headers)

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_source(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    create_resp = await client.post(
        "/api/sources",
        json={"site_key": "ao3", "auth_type": "credentials"},
        headers=headers,
    )
    source_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/sources/{source_id}",
        json={"is_enabled": False},
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is False


@pytest.mark.asyncio
async def test_patch_source_auth(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    create_resp = await client.post(
        "/api/sources",
        json={"site_key": "ao3", "auth_type": "credentials"},
        headers=headers,
    )
    source_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/sources/{source_id}/auth",
        json={"auth_type": "cookies", "auth_data": "new_cookie"},
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json()["auth_type"] == "cookies"
    assert resp.json()["auth_configured"] is True


@pytest.mark.asyncio
async def test_delete_source_via_api(client: AsyncClient, db_session: AsyncSession):
    headers = await _authenticated_headers(db_session)

    create_resp = await client.post(
        "/api/sources",
        json={"site_key": "ao3", "auth_type": "credentials"},
        headers=headers,
    )
    source_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/sources/{source_id}", headers=headers)

    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_sources_require_auth(client: AsyncClient, db_session: AsyncSession):
    app_settings = SettingsModel(id=1, storage_path="./data", setup_complete=True)
    db_session.add(app_settings)
    await db_session.flush()

    resp = await client.get("/api/sources")

    assert resp.status_code in (401, 403)
