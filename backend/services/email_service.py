# Load libraries
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.encryption import decrypt
from backend.models.settings import Settings

logger = logging.getLogger(__name__)


# Sends an email using the configured SMTP settings
async def send_email(
    db: AsyncSession,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> bool:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None or not settings_row.smtp_host:
        logger.warning("Cannot send email: SMTP not configured")

        return False

    try:
        smtp_password = None

        if settings_row.smtp_password_encrypted:
            smtp_password = decrypt(
                settings_row.smtp_password_encrypted,
                settings.ENCRYPTION_KEY,
                settings.ENCRYPTION_KEY_PREVIOUS or None,
            )

        from email.utils import formataddr

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = formataddr(("Bibliotheca Fabulae", settings_row.smtp_from_address))
        msg["To"] = settings_row.smtp_to_address

        msg.attach(MIMEText(body, "plain"))

        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        if settings_row.smtp_use_tls:
            server = smtplib.SMTP(settings_row.smtp_host, settings_row.smtp_port, timeout=10)
            server.starttls()

        else:
            server = smtplib.SMTP(settings_row.smtp_host, settings_row.smtp_port, timeout=10)

        if settings_row.smtp_username and smtp_password:
            server.login(settings_row.smtp_username, smtp_password)

        server.sendmail(
            settings_row.smtp_from_address,
            settings_row.smtp_to_address,
            msg.as_string(),
        )
        server.quit()

        logger.info("Email sent: %s", subject)

        return True

    except Exception:
        logger.exception("Failed to send email: %s", subject)

        return False


# Tests an SMTP connection using the provided credentials
def test_smtp_with_values(
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
) -> dict:
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()

        else:
            server = smtplib.SMTP(host, port, timeout=10)

        if username and password:
            server.login(username, password)

        server.quit()

        logger.info("SMTP connection test successful")

        return {"success": True, "message": "Connection successful"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentication failed"}

    except smtplib.SMTPConnectError:
        return {"success": False, "message": "Connection refused"}

    except TimeoutError:
        return {"success": False, "message": "Connection timed out"}

    except Exception as e:
        logger.exception("SMTP connection test failed")

        return {"success": False, "message": str(e)}


# Tests the SMTP connection using the saved database configuration
async def test_smtp_connection(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None or not settings_row.smtp_host:
        return {"success": False, "message": "SMTP not configured"}

    try:
        smtp_password = None

        if settings_row.smtp_password_encrypted:
            smtp_password = decrypt(
                settings_row.smtp_password_encrypted,
                settings.ENCRYPTION_KEY,
                settings.ENCRYPTION_KEY_PREVIOUS or None,
            )

        if settings_row.smtp_use_tls:
            server = smtplib.SMTP(settings_row.smtp_host, settings_row.smtp_port, timeout=10)
            server.starttls()

        else:
            server = smtplib.SMTP(settings_row.smtp_host, settings_row.smtp_port, timeout=10)

        if settings_row.smtp_username and smtp_password:
            server.login(settings_row.smtp_username, smtp_password)

        server.quit()

        logger.info("SMTP connection test successful")

        return {"success": True, "message": "Connection successful"}

    except smtplib.SMTPAuthenticationError:
        logger.warning("SMTP authentication failed")

        return {"success": False, "message": "Authentication failed"}

    except smtplib.SMTPConnectError:
        logger.warning("SMTP connection refused")

        return {"success": False, "message": "Connection refused"}

    except TimeoutError:
        logger.warning("SMTP connection timed out")

        return {"success": False, "message": "Connection timed out"}

    except Exception as e:
        logger.exception("SMTP connection test failed")

        return {"success": False, "message": str(e)}
