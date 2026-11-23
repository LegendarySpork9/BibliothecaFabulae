# Load libraries
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.settings import Settings as SettingsModel


# Test that the health endpoint returns 200 with expected fields
@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["setup_complete"] is False


# Test that health returns setup_complete True when a Settings row has it set
@pytest.mark.asyncio
async def test_health_setup_complete_true(
    client: AsyncClient, db_session: AsyncSession
):
    settings_row = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db_session.add(settings_row)
    await db_session.flush()

    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is True


# Test that health returns a version field
@pytest.mark.asyncio
async def test_health_returns_version(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


# Test that health response body includes setup_complete True when set
@pytest.mark.asyncio
async def test_health_body_has_setup_complete_true(
    client: AsyncClient, db_session: AsyncSession
):
    settings_row = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db_session.add(settings_row)
    await db_session.flush()

    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["setup_complete"] is True
    assert data["version"] == "1.0.0"
