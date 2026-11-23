# Load libraries
import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import create_access_token, hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.notification import Notification, NotificationPreference
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User

VALID_PASSWORD = "SecureP@ss123!"

DEFAULT_NOTIFICATION_TYPES = [
    "fic_updated",
    "sync_complete",
    "sync_failed",
    "auth_required",
    "storage_low",
    "fic_unavailable",
    "scanner_new_works",
    "audio_ready",
]


# Create a user with setup complete, seed preferences, and return auth headers
async def _authenticated_headers(db: AsyncSession) -> dict[str, str]:
    totp_secret = pyotp.random_base32()
    user = User(
        username="notifuser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db.add(app_settings)

    for ntype in DEFAULT_NOTIFICATION_TYPES:
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


# Test that GET /api/notifications returns an empty list initially
@pytest.mark.asyncio
async def test_get_notifications_empty(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get("/api/notifications", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["unread_count"] == 0


# Test that GET /api/notifications/unread-count returns zero initially
@pytest.mark.asyncio
async def test_get_unread_count_zero(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get(
        "/api/notifications/unread-count", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 0


# Test that POST /api/notifications/mark-all-read succeeds with no notifications
@pytest.mark.asyncio
async def test_mark_all_read_empty(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.post(
        "/api/notifications/mark-all-read", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


# Test that GET /api/notifications/preferences returns seeded preferences
@pytest.mark.asyncio
async def test_get_preferences_seeded(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get(
        "/api/notifications/preferences", headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(DEFAULT_NOTIFICATION_TYPES)

    types_returned = {p["notification_type"] for p in data}

    for ntype in DEFAULT_NOTIFICATION_TYPES:
        assert ntype in types_returned


# Test that preferences contain expected fields
@pytest.mark.asyncio
async def test_get_preferences_fields(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.get(
        "/api/notifications/preferences", headers=headers
    )
    assert response.status_code == 200

    for pref in response.json():
        assert "id" in pref
        assert "notification_type" in pref
        assert "ui_enabled" in pref
        assert "email_enabled" in pref
        assert pref["ui_enabled"] is True
        assert pref["email_enabled"] is False


# Test that notifications appear after being created directly in the database
@pytest.mark.asyncio
async def test_get_notifications_with_data(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    notification = Notification(
        type="fic_updated",
        title="New chapter available",
        message="Chapter 5 has been published.",
        severity="info",
    )
    db_session.add(notification)
    await db_session.flush()

    response = await client.get("/api/notifications", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["unread_count"] == 1
    assert data["items"][0]["title"] == "New chapter available"
    assert data["items"][0]["is_read"] is False


# Test that unread count reflects the number of unread notifications
@pytest.mark.asyncio
async def test_unread_count_reflects_data(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    for i in range(3):
        db_session.add(
            Notification(
                type="sync_complete",
                title=f"Sync {i}",
                message=f"Sync {i} completed.",
                severity="info",
            )
        )

    await db_session.flush()

    response = await client.get(
        "/api/notifications/unread-count", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 3


# Test that marking all read sets unread count to zero
@pytest.mark.asyncio
async def test_mark_all_read_clears_count(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    for i in range(2):
        db_session.add(
            Notification(
                type="fic_updated",
                title=f"Update {i}",
                message=f"Fic {i} updated.",
                severity="info",
            )
        )

    await db_session.flush()

    await client.post("/api/notifications/mark-all-read", headers=headers)

    response = await client.get(
        "/api/notifications/unread-count", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["unread_count"] == 0


# Test that marking a single notification as read succeeds
@pytest.mark.asyncio
async def test_mark_single_read(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    notification = Notification(
        type="storage_low",
        title="Storage warning",
        message="Disk space is running low.",
        severity="warning",
    )
    db_session.add(notification)
    await db_session.flush()

    response = await client.patch(
        f"/api/notifications/{notification.id}/read", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    count_resp = await client.get(
        "/api/notifications/unread-count", headers=headers
    )
    assert count_resp.json()["unread_count"] == 0


# Test that marking a nonexistent notification returns 404
@pytest.mark.asyncio
async def test_mark_read_nonexistent(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/notifications/99999/read", headers=headers
    )
    assert response.status_code == 404


# Test that deleting a notification returns 204
@pytest.mark.asyncio
async def test_delete_notification(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    notification = Notification(
        type="fic_updated",
        title="Deletable",
        message="This will be deleted.",
        severity="info",
    )
    db_session.add(notification)
    await db_session.flush()

    response = await client.delete(
        f"/api/notifications/{notification.id}", headers=headers
    )
    assert response.status_code == 204

    list_resp = await client.get("/api/notifications", headers=headers)
    assert list_resp.json()["total"] == 0


# Test that deleting a nonexistent notification returns 404
@pytest.mark.asyncio
async def test_delete_nonexistent_notification(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.delete(
        "/api/notifications/99999", headers=headers
    )
    assert response.status_code == 404


# Test that updating a preference toggles the email_enabled flag
@pytest.mark.asyncio
async def test_update_preference(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/notifications/preferences/fic_updated",
        json={"email_enabled": True},
        headers=headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["notification_type"] == "fic_updated"
    assert data["email_enabled"] is True
    assert data["ui_enabled"] is True


# Test that updating a nonexistent preference returns 404
@pytest.mark.asyncio
async def test_update_preference_nonexistent(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    response = await client.patch(
        "/api/notifications/preferences/nonexistent_type",
        json={"ui_enabled": False},
        headers=headers,
    )
    assert response.status_code == 404


# Test that notification endpoints require authentication
@pytest.mark.asyncio
async def test_notifications_require_auth(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/api/notifications")
    assert response.status_code in (401, 403)

    response = await client.get("/api/notifications/unread-count")
    assert response.status_code in (401, 403)

    response = await client.post("/api/notifications/mark-all-read")
    assert response.status_code in (401, 403)

    response = await client.get("/api/notifications/preferences")
    assert response.status_code in (401, 403)


# Test that the unread_only filter returns only unread notifications
@pytest.mark.asyncio
async def test_get_notifications_unread_only(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _authenticated_headers(db_session)

    db_session.add(
        Notification(
            type="fic_updated",
            title="Unread one",
            message="Still unread.",
            severity="info",
            is_read=False,
        )
    )
    db_session.add(
        Notification(
            type="fic_updated",
            title="Read one",
            message="Already read.",
            severity="info",
            is_read=True,
        )
    )
    await db_session.flush()

    response = await client.get(
        "/api/notifications?unread_only=true", headers=headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Unread one"
