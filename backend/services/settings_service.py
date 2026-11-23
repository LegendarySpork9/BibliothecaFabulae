# Load libraries
import logging
import os
import re
import shutil

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import (
    generate_qr_base64,
    generate_totp_secret,
    generate_totp_uri,
    hash_password,
    verify_password,
    verify_totp,
)
from backend.core.config import settings
from backend.core.encryption import decrypt, encrypt
from backend.models.settings import Settings
from backend.models.user import User

logger = logging.getLogger(__name__)


# Retrieves the current application settings
async def get_settings(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        return {}

    return {
        "storage_path": settings_row.storage_path,
        "theme": settings_row.theme,
        "smtp_host": settings_row.smtp_host,
        "smtp_port": settings_row.smtp_port,
        "smtp_username": settings_row.smtp_username,
        "smtp_password_configured": settings_row.smtp_password_encrypted is not None,
        "smtp_use_tls": settings_row.smtp_use_tls,
        "smtp_from_address": settings_row.smtp_from_address,
        "smtp_to_address": settings_row.smtp_to_address,
        "backup_location": settings_row.backup_location,
        "backup_schedule": settings_row.backup_schedule,
        "cloudflare_trust_enabled": settings_row.cloudflare_trust_enabled,
        "remember_device_days": settings_row.remember_device_days,
        "setup_complete": settings_row.setup_complete,
    }


# Validates and updates the storage directory path
async def update_storage_path(db: AsyncSession, path: str) -> dict:
    resolved_path = _validate_storage_path(path)

    test_file = os.path.join(resolved_path, ".bf_write_test")

    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)

    except OSError as e:
        raise ValueError(f"Directory is not writable: {e}")

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        raise ValueError("Settings not initialised")

    settings_row.storage_path = resolved_path
    await db.flush()

    disk_usage = shutil.disk_usage(resolved_path)

    logger.info("Storage path updated: %s", resolved_path)

    return {
        "storage_path": resolved_path,
        "total_bytes": disk_usage.total,
        "free_bytes": disk_usage.free,
    }


# Updates the UI theme preference
async def update_theme(db: AsyncSession, theme: str) -> dict:
    if theme not in ("dark", "light"):
        raise ValueError("Theme must be 'dark' or 'light'")

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        raise ValueError("Settings not initialised")

    settings_row.theme = theme
    await db.flush()

    logger.info("Theme updated: %s", theme)

    return {"theme": theme}


# Updates SMTP email server configuration
async def update_smtp(
    db: AsyncSession,
    host: str,
    port: int,
    username: str,
    password: str | None,
    use_tls: bool,
    from_address: str,
    to_address: str,
) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        raise ValueError("Settings not initialised")

    settings_row.smtp_host = host
    settings_row.smtp_port = port
    settings_row.smtp_username = username
    settings_row.smtp_use_tls = use_tls
    settings_row.smtp_from_address = from_address
    settings_row.smtp_to_address = to_address

    if password is not None:
        settings_row.smtp_password_encrypted = encrypt(password, settings.ENCRYPTION_KEY)

    await db.flush()

    logger.info("SMTP settings updated: %s:%d", host, port)

    return {"configured": True}


# Updates backup location and schedule settings
async def update_backup(db: AsyncSession, location: str, schedule: str) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        raise ValueError("Settings not initialised")

    settings_row.backup_location = location
    settings_row.backup_schedule = schedule
    await db.flush()

    logger.info("Backup settings updated: %s / %s", location, schedule)

    return {"backup_location": location, "backup_schedule": schedule}


# Updates the number of days a device is remembered
async def update_remember_device(db: AsyncSession, days: int) -> dict:
    if days < 1 or days > 365:
        raise ValueError("Remember device days must be between 1 and 365")

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        raise ValueError("Settings not initialised")

    settings_row.remember_device_days = days
    await db.flush()

    logger.info("Remember device days updated: %d", days)

    return {"remember_device_days": days}


# Retrieves account details for a user
async def get_account(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    return {
        "username": user.username,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "totp_enabled": user.totp_verified,
    }


# Changes a user's password after verifying the current one
async def change_password(
    db: AsyncSession,
    user_id: int,
    current_password: str,
    new_password: str,
) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    if not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect")

    _validate_password(new_password)

    user.password_hash = hash_password(new_password)
    await db.flush()

    logger.info("Password changed for user: %s", user.username)

    return {"success": True}


# Generates a new TOTP secret and QR code for re-enrolment
async def regenerate_totp(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    totp_secret = generate_totp_secret()
    totp_uri = generate_totp_uri(totp_secret, user.username)
    qr_code_base64 = generate_qr_base64(totp_uri)

    logger.info("TOTP regeneration initiated for user: %s", user.username)

    return {
        "totp_secret": totp_secret,
        "totp_uri": totp_uri,
        "qr_code_base64": qr_code_base64,
    }


# Confirms a new TOTP secret by validating the provided code
async def confirm_new_totp(
    db: AsyncSession,
    user_id: int,
    totp_code: str,
    pending_secret: str,
) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("User not found")

    if not verify_totp(pending_secret, totp_code):
        raise ValueError("Invalid TOTP code for the new secret")

    user.totp_secret_encrypted = encrypt(pending_secret, settings.ENCRYPTION_KEY)
    user.totp_verified = True
    await db.flush()

    logger.info("TOTP confirmed and replaced for user: %s", user.username)

    return {"success": True}


_BLOCKED_PATHS_UNIX = ("/", "/bin", "/sbin", "/usr", "/etc", "/boot", "/dev", "/proc", "/sys", "/root", "/home")
_BLOCKED_PATHS_WIN = ("C:\\", "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)")


# Rejects symlinks and system-critical directories
def _validate_storage_path(raw_path: str) -> str:
    resolved = os.path.realpath(raw_path)

    if os.path.islink(raw_path):
        raise ValueError("Symbolic links are not permitted as storage paths")

    if not os.path.isdir(resolved):
        raise ValueError(f"Directory does not exist: {resolved}")

    normalised = resolved.replace("\\", "/").rstrip("/")

    for blocked in _BLOCKED_PATHS_UNIX:
        if normalised == blocked:
            raise ValueError(f"Cannot use system directory as storage: {resolved}")

    for blocked in _BLOCKED_PATHS_WIN:
        if normalised.lower() == blocked.replace("\\", "/").lower():
            raise ValueError(f"Cannot use system directory as storage: {resolved}")

    return resolved


# Validates that a password meets complexity requirements
def _validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[^a-zA-Z0-9]", password):
        raise ValueError("Password must contain at least one special character")
