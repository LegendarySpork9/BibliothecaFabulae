# Load libraries
import pytest
from httpx import AsyncClient


# Test that the health endpoint returns 200 with expected fields
@pytest.mark.asyncio
async def test_health_endpoint_returns_200(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["setup_complete"] is False
