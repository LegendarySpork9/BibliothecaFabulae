# Load libraries
import smtplib
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.settings import Settings as SettingsModel
from backend.services.email_service import (
    send_email,
    test_smtp_connection as smtp_connection_test,
    test_smtp_with_values as smtp_values_test,
)


# Test that test_smtp_with_values returns success when SMTP connects
def test_smtp_with_values_success():
    mock_server = MagicMock()

    with patch("backend.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = smtp_values_test(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            use_tls=True,
        )

    assert result["success"] is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "pass")
    mock_server.quit.assert_called_once()


# Test that test_smtp_with_values returns auth failure on SMTPAuthenticationError
def test_smtp_with_values_auth_failure():
    mock_server = MagicMock()
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad credentials")

    with patch("backend.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = smtp_values_test(
            host="smtp.example.com",
            port=587,
            username="user",
            password="wrongpass",
            use_tls=False,
        )

    assert result["success"] is False
    assert result["message"] == "Authentication failed"


# Test that test_smtp_with_values returns timeout on TimeoutError
def test_smtp_with_values_timeout():
    with patch(
        "backend.services.email_service.smtplib.SMTP",
        side_effect=TimeoutError("timed out"),
    ):
        result = smtp_values_test(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            use_tls=True,
        )

    assert result["success"] is False
    assert result["message"] == "Connection timed out"


# Test that send_email returns False when SMTP is not configured
@pytest.mark.asyncio
async def test_send_email_no_smtp_configured(db_session: AsyncSession):
    settings_row = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db_session.add(settings_row)
    await db_session.flush()

    result = await send_email(db_session, "Subject", "Body")
    assert result is False


# Test that test_smtp_connection returns failure when SMTP is not configured
@pytest.mark.asyncio
async def test_smtp_connection_no_smtp_configured(db_session: AsyncSession):
    settings_row = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db_session.add(settings_row)
    await db_session.flush()

    result = await smtp_connection_test(db_session)
    assert result["success"] is False
    assert result["message"] == "SMTP not configured"


# Test that send_email with mocked SMTP succeeds and returns True
@pytest.mark.asyncio
async def test_send_email_success_with_mock(db_session: AsyncSession):
    from backend.core.config import settings
    from backend.core.encryption import encrypt

    encrypted_password = encrypt("smtp_pass", settings.ENCRYPTION_KEY)
    settings_row = SettingsModel(
        id=1,
        storage_path="/tmp/test",
        setup_complete=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password_encrypted=encrypted_password,
        smtp_use_tls=True,
        smtp_from_address="from@example.com",
        smtp_to_address="to@example.com",
    )
    db_session.add(settings_row)
    await db_session.flush()

    mock_server = MagicMock()

    with patch("backend.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = await send_email(db_session, "Test Subject", "Test Body")

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "smtp_pass")
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


# Test that send_email sends HTML body when provided
@pytest.mark.asyncio
async def test_send_email_with_html_body(db_session: AsyncSession):
    from backend.core.config import settings
    from backend.core.encryption import encrypt

    encrypted_password = encrypt("smtp_pass", settings.ENCRYPTION_KEY)
    settings_row = SettingsModel(
        id=1,
        storage_path="/tmp/test",
        setup_complete=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password_encrypted=encrypted_password,
        smtp_use_tls=False,
        smtp_from_address="from@example.com",
        smtp_to_address="to@example.com",
    )
    db_session.add(settings_row)
    await db_session.flush()

    mock_server = MagicMock()

    with patch("backend.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = await send_email(
            db_session, "Test Subject", "Plain body", html_body="<p>HTML body</p>"
        )

    assert result is True
    mock_server.starttls.assert_not_called()
    mock_server.sendmail.assert_called_once()


# Test that test_smtp_connection succeeds with mocked SMTP and saved config
@pytest.mark.asyncio
async def test_smtp_connection_success_with_mock(db_session: AsyncSession):
    from backend.core.config import settings
    from backend.core.encryption import encrypt

    encrypted_password = encrypt("smtp_pass", settings.ENCRYPTION_KEY)
    settings_row = SettingsModel(
        id=1,
        storage_path="/tmp/test",
        setup_complete=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password_encrypted=encrypted_password,
        smtp_use_tls=True,
        smtp_from_address="from@example.com",
        smtp_to_address="to@example.com",
    )
    db_session.add(settings_row)
    await db_session.flush()

    mock_server = MagicMock()

    with patch("backend.services.email_service.smtplib.SMTP", return_value=mock_server):
        result = await smtp_connection_test(db_session)

    assert result["success"] is True
    assert result["message"] == "Connection successful"
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "smtp_pass")
    mock_server.quit.assert_called_once()


# Test that send_email returns False when SMTP raises an exception
@pytest.mark.asyncio
async def test_send_email_smtp_exception(db_session: AsyncSession):
    from backend.core.config import settings
    from backend.core.encryption import encrypt

    encrypted_password = encrypt("smtp_pass", settings.ENCRYPTION_KEY)
    settings_row = SettingsModel(
        id=1,
        storage_path="/tmp/test",
        setup_complete=True,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password_encrypted=encrypted_password,
        smtp_use_tls=True,
        smtp_from_address="from@example.com",
        smtp_to_address="to@example.com",
    )
    db_session.add(settings_row)
    await db_session.flush()

    with patch(
        "backend.services.email_service.smtplib.SMTP",
        side_effect=ConnectionRefusedError("Connection refused"),
    ):
        result = await send_email(db_session, "Subject", "Body")

    assert result is False
