# Load libraries
import pyotp
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User
from backend.services.settings_service import (
    _validate_password,
    _validate_storage_path,
    change_password,
    confirm_new_totp,
    get_account,
    get_settings,
    regenerate_totp,
    update_backup,
    update_remember_device,
    update_smtp,
    update_storage_path,
    update_theme,
)

VALID_PASSWORD = "SecureP@ss123!"


# Create a user and settings row for tests that need them
async def _seed_user_and_settings(db: AsyncSession) -> User:
    totp_secret = pyotp.random_base32()
    user = User(
        username="testuser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db.add(user)

    app_settings = SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True)
    db.add(app_settings)
    await db.flush()

    return user


# Test that get_settings returns all expected fields
@pytest.mark.asyncio
async def test_get_settings_returns_all_fields(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test", setup_complete=True))
    await db_session.flush()

    result = await get_settings(db_session)

    assert result["storage_path"] == "/tmp/test"
    assert result["theme"] == "dark"
    assert result["smtp_host"] is None
    assert result["smtp_port"] is None
    assert result["smtp_username"] is None
    assert result["smtp_password_configured"] is False
    assert result["smtp_use_tls"] is True
    assert result["smtp_from_address"] is None
    assert result["smtp_to_address"] is None
    assert result["backup_location"] is None
    assert result["backup_schedule"] is None
    assert result["cloudflare_trust_enabled"] is False
    assert result["remember_device_days"] == 30
    assert result["setup_complete"] is True


# Test that get_settings returns empty dict when no settings exist
@pytest.mark.asyncio
async def test_get_settings_returns_empty_when_no_settings(db_session: AsyncSession):
    result = await get_settings(db_session)
    assert result == {}


# Test that update_storage_path succeeds with a valid temporary directory
@pytest.mark.asyncio
async def test_update_storage_path_valid(db_session: AsyncSession, tmp_path):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/old", setup_complete=True))
    await db_session.flush()

    result = await update_storage_path(db_session, str(tmp_path))

    assert result["storage_path"] == str(tmp_path.resolve())
    assert result["total_bytes"] > 0
    assert result["free_bytes"] > 0


# Test that update_storage_path raises ValueError for nonexistent path
@pytest.mark.asyncio
async def test_update_storage_path_nonexistent_raises(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/old", setup_complete=True))
    await db_session.flush()

    with pytest.raises(ValueError, match="does not exist"):
        await update_storage_path(db_session, "/nonexistent/path/xyz123")


# Test that update_theme with "dark" succeeds
@pytest.mark.asyncio
async def test_update_theme_dark(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test", theme="light"))
    await db_session.flush()

    result = await update_theme(db_session, "dark")
    assert result["theme"] == "dark"


# Test that update_theme with "light" succeeds
@pytest.mark.asyncio
async def test_update_theme_light(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test", theme="dark"))
    await db_session.flush()

    result = await update_theme(db_session, "light")
    assert result["theme"] == "light"


# Test that update_theme with an invalid value raises ValueError
@pytest.mark.asyncio
async def test_update_theme_invalid_raises(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    with pytest.raises(ValueError, match="must be 'dark' or 'light'"):
        await update_theme(db_session, "blue")


# Test that update_smtp saves all fields and encrypts password
@pytest.mark.asyncio
async def test_update_smtp_saves_all_fields(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    result = await update_smtp(
        db_session,
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="secret123",
        use_tls=True,
        from_address="from@example.com",
        to_address="to@example.com",
    )

    assert result["configured"] is True

    # Verify the row was actually updated
    from sqlalchemy import select

    row_result = await db_session.execute(select(SettingsModel).where(SettingsModel.id == 1))
    row = row_result.scalar_one()

    assert row.smtp_host == "smtp.example.com"
    assert row.smtp_port == 587
    assert row.smtp_username == "user@example.com"
    assert row.smtp_use_tls is True
    assert row.smtp_from_address == "from@example.com"
    assert row.smtp_to_address == "to@example.com"
    assert row.smtp_password_encrypted is not None

    # Verify the password can be decrypted
    from backend.core.encryption import decrypt

    decrypted = decrypt(row.smtp_password_encrypted, settings.ENCRYPTION_KEY)
    assert decrypted == "secret123"


# Test that update_backup saves location and schedule
@pytest.mark.asyncio
async def test_update_backup_saves_values(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    result = await update_backup(db_session, "/tmp/backups", "daily")

    assert result["backup_location"] == "/tmp/backups"
    assert result["backup_schedule"] == "daily"


# Test that update_remember_device with valid days succeeds
@pytest.mark.asyncio
async def test_update_remember_device_valid(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    result = await update_remember_device(db_session, 14)
    assert result["remember_device_days"] == 14


# Test that update_remember_device with 0 raises ValueError
@pytest.mark.asyncio
async def test_update_remember_device_zero_raises(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    with pytest.raises(ValueError, match="between 1 and 365"):
        await update_remember_device(db_session, 0)


# Test that update_remember_device with 400 raises ValueError
@pytest.mark.asyncio
async def test_update_remember_device_too_high_raises(db_session: AsyncSession):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/test"))
    await db_session.flush()

    with pytest.raises(ValueError, match="between 1 and 365"):
        await update_remember_device(db_session, 400)


# Test that get_account returns username and totp_enabled
@pytest.mark.asyncio
async def test_get_account_returns_user_info(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    result = await get_account(db_session, user.id)

    assert result["username"] == "testuser"
    assert result["totp_enabled"] is True
    assert "created_at" in result


# Test that change_password succeeds with correct current password
@pytest.mark.asyncio
async def test_change_password_success(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    result = await change_password(
        db_session, user.id, VALID_PASSWORD, "NewSecureP@ss456!"
    )
    assert result["success"] is True


# Test that change_password with wrong current password raises ValueError
@pytest.mark.asyncio
async def test_change_password_wrong_current_raises(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    with pytest.raises(ValueError, match="Current password is incorrect"):
        await change_password(
            db_session, user.id, "WrongP@ssword123!", "NewSecureP@ss456!"
        )


# Test that regenerate_totp returns secret, uri, and qr_code_base64
@pytest.mark.asyncio
async def test_regenerate_totp_returns_data(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    result = await regenerate_totp(db_session, user.id)

    assert "totp_secret" in result
    assert "totp_uri" in result
    assert "qr_code_base64" in result
    assert len(result["totp_secret"]) > 0
    assert "BibliothecaFabulae" in result["totp_uri"]
    assert len(result["qr_code_base64"]) > 0


# Test that confirm_new_totp with valid code replaces the secret
@pytest.mark.asyncio
async def test_confirm_new_totp_valid_code(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    new_secret = pyotp.random_base32()
    totp = pyotp.TOTP(new_secret)
    code = totp.now()

    result = await confirm_new_totp(db_session, user.id, code, new_secret)
    assert result["success"] is True

    # Verify the secret was replaced in the database
    from backend.core.encryption import decrypt

    decrypted = decrypt(user.totp_secret_encrypted, settings.ENCRYPTION_KEY)
    assert decrypted == new_secret


# Test that confirm_new_totp with invalid code raises ValueError
@pytest.mark.asyncio
async def test_confirm_new_totp_invalid_code_raises(db_session: AsyncSession):
    user = await _seed_user_and_settings(db_session)

    new_secret = pyotp.random_base32()

    with pytest.raises(ValueError, match="Invalid TOTP code"):
        await confirm_new_totp(db_session, user.id, "000000", new_secret)


# Test that _validate_password rejects short passwords
def test_validate_password_too_short():
    with pytest.raises(ValueError, match="at least 12 characters"):
        _validate_password("Short1!")


# Test that _validate_password rejects passwords without uppercase
def test_validate_password_no_uppercase():
    with pytest.raises(ValueError, match="uppercase"):
        _validate_password("nouppercase123!")


# Test that _validate_password rejects passwords without lowercase
def test_validate_password_no_lowercase():
    with pytest.raises(ValueError, match="lowercase"):
        _validate_password("NOLOWERCASE123!")


# Test that _validate_password rejects passwords without a digit
def test_validate_password_no_digit():
    with pytest.raises(ValueError, match="digit"):
        _validate_password("NoDigitHere!!!")


# Test that _validate_password rejects passwords without a special character
def test_validate_password_no_special_char():
    with pytest.raises(ValueError, match="special character"):
        _validate_password("NoSpecialChar123")


# Test that _validate_storage_path rejects nonexistent directories
def test_validate_storage_path_nonexistent():
    with pytest.raises(ValueError, match="does not exist"):
        _validate_storage_path("/nonexistent/path/xyz123")


# Test that _validate_storage_path accepts a valid tmp_path directory
def test_validate_storage_path_valid(tmp_path):
    result = _validate_storage_path(str(tmp_path))
    assert result == str(tmp_path.resolve())
