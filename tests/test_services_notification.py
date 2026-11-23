# Load libraries
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification, NotificationPreference
from backend.models.settings import Settings as SettingsModel
from backend.services.notification_service import (
    create_notification,
    delete_notification,
    get_notifications,
    get_preferences,
    get_unread_count,
    mark_all_read,
    mark_read,
    update_preference,
)

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


# Seed settings and notification preferences for tests
async def _seed_settings_and_prefs(db: AsyncSession) -> None:
    db.add(SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True))

    for ntype in DEFAULT_NOTIFICATION_TYPES:
        db.add(
            NotificationPreference(
                notification_type=ntype,
                ui_enabled=True,
                email_enabled=False,
            )
        )

    await db.flush()


# Test that create_notification with ui_enabled preference creates a row
@pytest.mark.asyncio
async def test_create_notification_ui_enabled(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    notification = await create_notification(
        db_session,
        type="fic_updated",
        title="New chapter",
        message="Chapter 5 is available.",
    )

    assert notification is not None
    assert notification.type == "fic_updated"
    assert notification.title == "New chapter"
    assert notification.message == "Chapter 5 is available."
    assert notification.severity == "info"
    assert notification.is_read is False


# Test that create_notification with ui_disabled preference does not create a row
@pytest.mark.asyncio
async def test_create_notification_ui_disabled(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True))
    db_session.add(
        NotificationPreference(
            notification_type="fic_updated",
            ui_enabled=False,
            email_enabled=False,
        )
    )
    await db_session.flush()

    notification = await create_notification(
        db_session,
        type="fic_updated",
        title="New chapter",
        message="Chapter 5 is available.",
    )

    assert notification is None


# Test that create_notification with no matching preference still creates a row
@pytest.mark.asyncio
async def test_create_notification_no_preference(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True))
    await db_session.flush()

    notification = await create_notification(
        db_session,
        type="unknown_type",
        title="Unknown event",
        message="Something happened.",
    )

    assert notification is not None
    assert notification.type == "unknown_type"


# Test that get_notifications returns items sorted by created_at desc
@pytest.mark.asyncio
async def test_get_notifications_sorted(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    db_session.add(
        Notification(type="fic_updated", title="First", message="First.", severity="info")
    )
    await db_session.flush()

    db_session.add(
        Notification(type="fic_updated", title="Second", message="Second.", severity="info")
    )
    await db_session.flush()

    result = await get_notifications(db_session)

    assert len(result["items"]) == 2
    assert result["total"] == 2
    assert result["unread_count"] == 2


# Test that get_notifications with unread_only filter works
@pytest.mark.asyncio
async def test_get_notifications_unread_only(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    db_session.add(
        Notification(
            type="fic_updated",
            title="Unread",
            message="Still unread.",
            severity="info",
            is_read=False,
        )
    )
    db_session.add(
        Notification(
            type="fic_updated",
            title="Read",
            message="Already read.",
            severity="info",
            is_read=True,
        )
    )
    await db_session.flush()

    result = await get_notifications(db_session, unread_only=True)

    assert result["total"] == 1
    assert result["items"][0]["title"] == "Unread"


# Test that get_notifications with type filter works
@pytest.mark.asyncio
async def test_get_notifications_type_filter(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    db_session.add(
        Notification(type="fic_updated", title="Fic", message="Fic.", severity="info")
    )
    db_session.add(
        Notification(type="sync_complete", title="Sync", message="Sync.", severity="info")
    )
    await db_session.flush()

    result = await get_notifications(db_session, type_filter="fic_updated")

    assert result["total"] == 1
    assert result["items"][0]["type"] == "fic_updated"


# Test that get_notifications pagination works
@pytest.mark.asyncio
async def test_get_notifications_pagination(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    for i in range(15):
        db_session.add(
            Notification(
                type="fic_updated",
                title=f"Notification {i}",
                message=f"Message {i}.",
                severity="info",
            )
        )
    await db_session.flush()

    # First page
    result = await get_notifications(db_session, limit=10, offset=0)
    assert len(result["items"]) == 10
    assert result["total"] == 15

    # Second page
    result2 = await get_notifications(db_session, limit=10, offset=10)
    assert len(result2["items"]) == 5
    assert result2["total"] == 15


# Test that get_unread_count returns correct count
@pytest.mark.asyncio
async def test_get_unread_count(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    db_session.add(
        Notification(type="fic_updated", title="A", message="A.", severity="info", is_read=False)
    )
    db_session.add(
        Notification(type="fic_updated", title="B", message="B.", severity="info", is_read=False)
    )
    db_session.add(
        Notification(type="fic_updated", title="C", message="C.", severity="info", is_read=True)
    )
    await db_session.flush()

    count = await get_unread_count(db_session)
    assert count == 2


# Test that mark_read marks a notification as read
@pytest.mark.asyncio
async def test_mark_read(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    notification = Notification(
        type="fic_updated", title="Test", message="Test.", severity="info"
    )
    db_session.add(notification)
    await db_session.flush()

    result = await mark_read(db_session, notification.id)
    assert result["success"] is True

    count = await get_unread_count(db_session)
    assert count == 0


# Test that mark_read raises ValueError for nonexistent notification
@pytest.mark.asyncio
async def test_mark_read_nonexistent_raises(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Notification not found"):
        await mark_read(db_session, 99999)


# Test that mark_all_read marks all notifications as read
@pytest.mark.asyncio
async def test_mark_all_read(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    for i in range(3):
        db_session.add(
            Notification(
                type="fic_updated",
                title=f"N{i}",
                message=f"M{i}.",
                severity="info",
            )
        )
    await db_session.flush()

    result = await mark_all_read(db_session)
    assert result["success"] is True

    count = await get_unread_count(db_session)
    assert count == 0


# Test that delete_notification removes the row
@pytest.mark.asyncio
async def test_delete_notification(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    notification = Notification(
        type="fic_updated", title="Deletable", message="Delete me.", severity="info"
    )
    db_session.add(notification)
    await db_session.flush()

    result = await delete_notification(db_session, notification.id)
    assert result["success"] is True

    all_notifs = await get_notifications(db_session)
    assert all_notifs["total"] == 0


# Test that delete_notification raises ValueError for nonexistent notification
@pytest.mark.asyncio
async def test_delete_notification_nonexistent_raises(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Notification not found"):
        await delete_notification(db_session, 99999)


# Test that get_preferences returns all seeded preferences
@pytest.mark.asyncio
async def test_get_preferences_returns_all(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    prefs = await get_preferences(db_session)

    assert len(prefs) == len(DEFAULT_NOTIFICATION_TYPES)

    types_returned = {p["notification_type"] for p in prefs}

    for ntype in DEFAULT_NOTIFICATION_TYPES:
        assert ntype in types_returned

    for pref in prefs:
        assert "id" in pref
        assert "notification_type" in pref
        assert "ui_enabled" in pref
        assert "email_enabled" in pref
        assert pref["ui_enabled"] is True
        assert pref["email_enabled"] is False


# Test that update_preference toggles email_enabled
@pytest.mark.asyncio
async def test_update_preference_toggles_email(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    result = await update_preference(
        db_session, "fic_updated", email_enabled=True
    )

    assert result["notification_type"] == "fic_updated"
    assert result["email_enabled"] is True
    assert result["ui_enabled"] is True


# Test that update_preference toggles ui_enabled
@pytest.mark.asyncio
async def test_update_preference_toggles_ui(db_session: AsyncSession):
    await _seed_settings_and_prefs(db_session)

    result = await update_preference(
        db_session, "fic_updated", ui_enabled=False
    )

    assert result["notification_type"] == "fic_updated"
    assert result["ui_enabled"] is False
    assert result["email_enabled"] is False


# Test that update_preference raises ValueError for nonexistent type
@pytest.mark.asyncio
async def test_update_preference_nonexistent_raises(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Notification preference not found"):
        await update_preference(db_session, "nonexistent_type", ui_enabled=False)
