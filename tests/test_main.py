# Load libraries
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.settings import Settings as SettingsModel


# Test that security headers are present on responses
@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Permissions-Policy" in response.headers


# Test that security headers are present on POST responses too
@pytest.mark.asyncio
async def test_security_headers_on_post(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/auth/login",
        json={"username": "nobody", "password": "password"},
    )

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


# Test that CSRF check blocks POST requests with a wrong Origin header
@pytest.mark.asyncio
async def test_csrf_blocks_wrong_origin(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/auth/login",
        json={"username": "test", "password": "test"},
        headers={"Origin": "http://evil.example.com"},
    )
    assert response.status_code == 403

    data = response.json()
    assert "Cross-origin" in data["detail"]


# Test that CSRF check allows requests with the correct Origin
@pytest.mark.asyncio
async def test_csrf_allows_correct_origin(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/auth/login",
        json={"username": "test", "password": "test"},
        headers={"Origin": "http://localhost:5173"},
    )

    # Should not be blocked by CSRF; will reach the login handler
    assert response.status_code != 403 or "Cross-origin" not in response.json().get(
        "detail", ""
    )


# Test that CSRF check allows GET requests regardless of Origin
@pytest.mark.asyncio
async def test_csrf_allows_get_with_bad_origin(client: AsyncClient):
    response = await client.get(
        "/api/health",
        headers={"Origin": "http://evil.example.com"},
    )
    assert response.status_code == 200


# Test that CSRF check blocks requests with a wrong Referer header
@pytest.mark.asyncio
async def test_csrf_blocks_wrong_referer(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/auth/login",
        json={"username": "test", "password": "test"},
        headers={"Referer": "http://evil.example.com/page"},
    )
    assert response.status_code == 403

    data = response.json()
    assert "Cross-origin" in data["detail"]


# Test that requests without Origin or Referer are not blocked by CSRF
@pytest.mark.asyncio
async def test_csrf_allows_no_origin_header(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/auth/login",
        json={"username": "test", "password": "test"},
    )

    # Should not be 403 with Cross-origin detail
    if response.status_code == 403:
        assert "Cross-origin" not in response.json().get("detail", "")
