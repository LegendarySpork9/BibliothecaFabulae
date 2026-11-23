# Load libraries
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification, NotificationPreference
from backend.models.session import RefreshToken
from backend.models.settings import Settings
from backend.models.user import User


# Test that a user can be created and defaults are applied
@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    user = User(
        username="testuser",
        password_hash="$2b$12$" + "a" * 53,
        totp_secret_encrypted="encrypted_secret",
    )
    db_session.add(user)
    await db_session.flush()

    result = await db_session.execute(select(User).where(User.username == "testuser"))
    fetched = result.scalar_one()
    assert fetched.username == "testuser"
    assert fetched.totp_verified is False


# Test that settings can be created with correct defaults
@pytest.mark.asyncio
async def test_create_settings(db_session: AsyncSession):
    settings = Settings(id=1, storage_path="/tmp/fics")
    db_session.add(settings)
    await db_session.flush()

    result = await db_session.execute(select(Settings).where(Settings.id == 1))
    fetched = result.scalar_one()
    assert fetched.storage_path == "/tmp/fics"
    assert fetched.theme == "dark"
    assert fetched.setup_complete is False
    assert fetched.remember_device_days == 30
    assert fetched.smtp_use_tls is True


# Test that a notification can be created with correct defaults
@pytest.mark.asyncio
async def test_create_notification(db_session: AsyncSession):
    notification = Notification(
        type="fic_updated",
        title="New chapter",
        message="A fic has been updated with a new chapter.",
        severity="info",
    )
    db_session.add(notification)
    await db_session.flush()

    result = await db_session.execute(
        select(Notification).where(Notification.type == "fic_updated")
    )
    fetched = result.scalar_one()
    assert fetched.title == "New chapter"
    assert fetched.is_read is False
    assert fetched.email_sent is False
    assert fetched.related_fic_id is None


# Test that a notification preference can be created
@pytest.mark.asyncio
async def test_create_notification_preference(db_session: AsyncSession):
    pref = NotificationPreference(
        notification_type="fic_updated",
        ui_enabled=True,
        email_enabled=False,
    )
    db_session.add(pref)
    await db_session.flush()

    result = await db_session.execute(
        select(NotificationPreference).where(
            NotificationPreference.notification_type == "fic_updated"
        )
    )
    fetched = result.scalar_one()
    assert fetched.ui_enabled is True
    assert fetched.email_enabled is False


# Test that a refresh token can be created for a user
@pytest.mark.asyncio
async def test_create_refresh_token(db_session: AsyncSession):
    user = User(
        username="tokenuser",
        password_hash="$2b$12$" + "b" * 53,
        totp_secret_encrypted="encrypted_secret",
    )
    db_session.add(user)
    await db_session.flush()

    token = RefreshToken(
        user_id=user.id,
        token_hash="a" * 64,
        device_name="Chrome on Windows",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db_session.add(token)
    await db_session.flush()

    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    fetched = result.scalar_one()
    assert fetched.device_name == "Chrome on Windows"
    assert fetched.remember_device is False
