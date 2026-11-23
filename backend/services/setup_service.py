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
    verify_totp,
)
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.notification import NotificationPreference
from backend.models.settings import Settings
from backend.models.user import User

logger = logging.getLogger(__name__)

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
PASSWORD_MIN_LENGTH = 12

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


# Returns the current setup progress and active step
async def get_setup_status(db: AsyncSession) -> dict:
    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    base = {
        "storage_path": settings_row.storage_path if settings_row else "",
        "smtp_configured": bool(settings_row and settings_row.smtp_host),
    }

    if settings_row and settings_row.setup_complete:
        return {**base, "setup_complete": True, "current_step": 0}

    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if user is None:
        return {**base, "setup_complete": False, "current_step": 1}

    if not user.totp_verified:
        return {**base, "setup_complete": False, "current_step": 2}

    if settings_row is None or not settings_row.storage_path:
        return {**base, "setup_complete": False, "current_step": 3}

    if settings_row.smtp_host is None:
        return {**base, "setup_complete": False, "current_step": 4}

    return {**base, "setup_complete": False, "current_step": 5}


# Creates or resets the admin account and generates TOTP enrolment data
async def create_account(db: AsyncSession, username: str, password: str) -> dict:
    if not USERNAME_PATTERN.match(username):
        raise ValueError(
            "Username must be 3-50 characters and contain only "
            "letters, numbers, and underscores"
        )

    _validate_password(password)

    password_hash = hash_password(password)
    totp_secret = generate_totp_secret()
    totp_secret_encrypted = encrypt(totp_secret, settings.ENCRYPTION_KEY)

    existing_result = await db.execute(select(User).limit(1))
    existing_user = existing_result.scalar_one_or_none()

    if existing_user is not None:
        existing_user.username = username
        existing_user.password_hash = password_hash
        existing_user.totp_secret_encrypted = totp_secret_encrypted
        existing_user.totp_verified = False
        await db.flush()
        user = existing_user
        logger.info("Account reset for interrupted setup: %s", username)

    else:
        user = User(
            username=username,
            password_hash=password_hash,
            totp_secret_encrypted=totp_secret_encrypted,
            totp_verified=False,
        )
        db.add(user)
        await db.flush()
        logger.info("Account created for user: %s", username)

    totp_uri = generate_totp_uri(totp_secret, username)
    qr_code_base64 = generate_qr_base64(totp_uri)

    return {
        "totp_secret": totp_secret,
        "totp_uri": totp_uri,
        "qr_code_base64": qr_code_base64,
    }


# Confirms the TOTP code during setup and marks the user as verified
async def verify_setup_totp(db: AsyncSession, totp_code: str) -> dict:
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if user is None:
        raise ValueError("No user account found. Complete account setup first.")

    from backend.core.encryption import decrypt

    totp_secret = decrypt(
        user.totp_secret_encrypted,
        settings.ENCRYPTION_KEY,
        settings.ENCRYPTION_KEY_PREVIOUS or None,
    )

    if not verify_totp(totp_secret, totp_code):
        raise ValueError("Invalid TOTP code")

    user.totp_verified = True
    await db.flush()

    logger.info("TOTP verified for user: %s", user.username)

    return {"verified": True}


# Validates and saves the storage directory path
async def configure_storage(db: AsyncSession, storage_path: str) -> dict:
    resolved_path = _validate_storage_path(storage_path)

    test_file = os.path.join(resolved_path, ".bf_write_test")

    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)

    except OSError as e:
        raise ValueError(f"Directory is not writable: {e}")

    disk_usage = shutil.disk_usage(resolved_path)

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        settings_row = Settings(id=1, storage_path=resolved_path)
        db.add(settings_row)

    else:
        settings_row.storage_path = resolved_path

    await db.flush()

    logger.info("Storage configured: %s", resolved_path)

    return {
        "valid": True,
        "total_bytes": disk_usage.total,
        "free_bytes": disk_usage.free,
    }


# Saves SMTP email server configuration
async def configure_smtp(
    db: AsyncSession,
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
    from_address: str,
    to_address: str,
) -> dict:
    encrypted_password = encrypt(password, settings.ENCRYPTION_KEY) if password else None

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None:
        settings_row = Settings(id=1)
        db.add(settings_row)

    settings_row.smtp_host = host
    settings_row.smtp_port = port
    settings_row.smtp_username = username
    settings_row.smtp_password_encrypted = encrypted_password
    settings_row.smtp_use_tls = use_tls
    settings_row.smtp_from_address = from_address
    settings_row.smtp_to_address = to_address

    await db.flush()

    logger.info("SMTP configured: %s:%d", host, port)

    return {"configured": True}


# Marks the setup wizard as complete and seeds default notification preferences
async def complete_setup(db: AsyncSession) -> dict:
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if user is None or not user.totp_verified:
        raise ValueError("Account setup and TOTP verification must be completed first")

    result = await db.execute(select(Settings).where(Settings.id == 1))
    settings_row = result.scalar_one_or_none()

    if settings_row is None or not settings_row.storage_path:
        raise ValueError("Storage must be configured first")

    settings_row.setup_complete = True
    await db.flush()

    existing_prefs = await db.execute(select(NotificationPreference))
    existing_types = {p.notification_type for p in existing_prefs.scalars().all()}

    for notification_type in DEFAULT_NOTIFICATION_TYPES:
        if notification_type not in existing_types:
            pref = NotificationPreference(
                notification_type=notification_type,
                ui_enabled=True,
                email_enabled=False,
            )
            db.add(pref)

    await db.flush()

    logger.info("Setup completed successfully")

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
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")

    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")

    if not re.search(r"[^a-zA-Z0-9]", password):
        raise ValueError("Password must contain at least one special character")
