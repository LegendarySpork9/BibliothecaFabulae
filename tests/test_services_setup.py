# Load libraries
import pyotp
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import hash_password
from backend.core.config import settings
from backend.core.encryption import encrypt
from backend.models.notification import NotificationPreference
from backend.models.settings import Settings as SettingsModel
from backend.models.user import User
from backend.services.setup_service import (
    _validate_password,
    _validate_storage_path,
    complete_setup,
    configure_smtp,
    configure_storage,
    create_account,
    verify_setup_totp,
)

VALID_PASSWORD = "SecureP@ss123!"
VALID_USERNAME = "setupuser"


# Test that create_account with valid data creates user and returns TOTP data
@pytest.mark.asyncio
async def test_create_account_valid(db_session: AsyncSession):
    result = await create_account(db_session, VALID_USERNAME, VALID_PASSWORD)

    assert "totp_secret" in result
    assert "totp_uri" in result
    assert "qr_code_base64" in result
    assert len(result["totp_secret"]) > 0
    assert "BibliothecaFabulae" in result["totp_uri"]
    assert len(result["qr_code_base64"]) > 0

    # Verify the user was actually created in the database
    from sqlalchemy import select

    user_result = await db_session.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    assert user is not None
    assert user.username == VALID_USERNAME
    assert user.totp_verified is False


# Test that create_account with invalid username raises ValueError
@pytest.mark.asyncio
async def test_create_account_invalid_username(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Username"):
        await create_account(db_session, "ab", VALID_PASSWORD)


# Test that create_account with username containing special chars raises ValueError
@pytest.mark.asyncio
async def test_create_account_username_special_chars(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Username"):
        await create_account(db_session, "user@name", VALID_PASSWORD)


# Test that create_account resets existing user on second call
@pytest.mark.asyncio
async def test_create_account_resets_existing(db_session: AsyncSession):
    first_result = await create_account(db_session, "firstuser", VALID_PASSWORD)
    assert "totp_secret" in first_result

    second_result = await create_account(db_session, "seconduser", VALID_PASSWORD)
    assert "totp_secret" in second_result

    # Verify there is still only one user
    from sqlalchemy import select, func

    count_result = await db_session.execute(select(func.count(User.id)))
    count = count_result.scalar()
    assert count == 1

    # Verify the username was updated
    user_result = await db_session.execute(select(User).limit(1))
    user = user_result.scalar_one()
    assert user.username == "seconduser"
    assert user.totp_verified is False


# Test that verify_setup_totp with valid code sets totp_verified to True
@pytest.mark.asyncio
async def test_verify_setup_totp_valid(db_session: AsyncSession):
    result = await create_account(db_session, VALID_USERNAME, VALID_PASSWORD)
    totp_secret = result["totp_secret"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    verify_result = await verify_setup_totp(db_session, code)
    assert verify_result["verified"] is True

    # Verify the user was marked as verified
    from sqlalchemy import select

    user_result = await db_session.execute(select(User).limit(1))
    user = user_result.scalar_one()
    assert user.totp_verified is True


# Test that verify_setup_totp with invalid code raises ValueError
@pytest.mark.asyncio
async def test_verify_setup_totp_invalid_code(db_session: AsyncSession):
    await create_account(db_session, VALID_USERNAME, VALID_PASSWORD)

    with pytest.raises(ValueError, match="Invalid TOTP code"):
        await verify_setup_totp(db_session, "000000")


# Test that verify_setup_totp with no user raises ValueError
@pytest.mark.asyncio
async def test_verify_setup_totp_no_user(db_session: AsyncSession):
    with pytest.raises(ValueError, match="No user account found"):
        await verify_setup_totp(db_session, "123456")


# Test that configure_storage with valid tmp_path creates settings
@pytest.mark.asyncio
async def test_configure_storage_valid(db_session: AsyncSession, tmp_path):
    result = await configure_storage(db_session, str(tmp_path))

    assert result["valid"] is True
    assert result["total_bytes"] > 0
    assert result["free_bytes"] > 0

    # Verify the settings were created
    from sqlalchemy import select

    settings_result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = settings_result.scalar_one()
    assert settings_row.storage_path == str(tmp_path.resolve())


# Test that configure_storage updates existing settings row
@pytest.mark.asyncio
async def test_configure_storage_updates_existing(db_session: AsyncSession, tmp_path):
    db_session.add(SettingsModel(id=1, storage_path="/tmp/old"))
    await db_session.flush()

    result = await configure_storage(db_session, str(tmp_path))
    assert result["valid"] is True

    # Verify the settings were updated
    from sqlalchemy import select

    settings_result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = settings_result.scalar_one()
    assert settings_row.storage_path == str(tmp_path.resolve())


# Test that configure_storage with nonexistent path raises ValueError
@pytest.mark.asyncio
async def test_configure_storage_nonexistent_path(db_session: AsyncSession):
    with pytest.raises(ValueError, match="does not exist"):
        await configure_storage(db_session, "/nonexistent/path/xyz123")


# Test that configure_smtp saves encrypted password
@pytest.mark.asyncio
async def test_configure_smtp_saves_encrypted(db_session: AsyncSession):
    result = await configure_smtp(
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

    # Verify the settings were created with encrypted password
    from sqlalchemy import select

    settings_result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = settings_result.scalar_one()

    assert settings_row.smtp_host == "smtp.example.com"
    assert settings_row.smtp_port == 587
    assert settings_row.smtp_password_encrypted is not None

    # Verify the password can be decrypted
    from backend.core.encryption import decrypt

    decrypted = decrypt(settings_row.smtp_password_encrypted, settings.ENCRYPTION_KEY)
    assert decrypted == "secret123"


# Test that configure_smtp with empty password stores None
@pytest.mark.asyncio
async def test_configure_smtp_empty_password(db_session: AsyncSession):
    result = await configure_smtp(
        db_session,
        host="smtp.example.com",
        port=25,
        username="",
        password="",
        use_tls=False,
        from_address="from@example.com",
        to_address="to@example.com",
    )

    assert result["configured"] is True

    from sqlalchemy import select

    settings_result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = settings_result.scalar_one()
    assert settings_row.smtp_password_encrypted is None


# Test that complete_setup sets setup_complete and seeds preferences
@pytest.mark.asyncio
async def test_complete_setup_success(db_session: AsyncSession, tmp_path):
    # Create a verified user
    totp_secret = pyotp.random_base32()
    user = User(
        username=VALID_USERNAME,
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db_session.add(user)

    # Create settings with storage path
    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path)))
    await db_session.flush()

    result = await complete_setup(db_session)
    assert result["success"] is True

    # Verify setup_complete was set
    from sqlalchemy import select

    settings_result = await db_session.execute(
        select(SettingsModel).where(SettingsModel.id == 1)
    )
    settings_row = settings_result.scalar_one()
    assert settings_row.setup_complete is True

    # Verify notification preferences were seeded
    pref_result = await db_session.execute(select(NotificationPreference))
    prefs = pref_result.scalars().all()
    assert len(prefs) == 8

    pref_types = {p.notification_type for p in prefs}

    for expected_type in [
        "fic_updated",
        "sync_complete",
        "sync_failed",
        "auth_required",
        "storage_low",
        "fic_unavailable",
        "scanner_new_works",
        "audio_ready",
    ]:
        assert expected_type in pref_types


# Test that complete_setup with no user raises ValueError
@pytest.mark.asyncio
async def test_complete_setup_no_user(db_session: AsyncSession, tmp_path):
    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path)))
    await db_session.flush()

    with pytest.raises(ValueError, match="Account setup and TOTP verification"):
        await complete_setup(db_session)


# Test that complete_setup with unverified TOTP raises ValueError
@pytest.mark.asyncio
async def test_complete_setup_unverified_totp(db_session: AsyncSession, tmp_path):
    totp_secret = pyotp.random_base32()
    user = User(
        username=VALID_USERNAME,
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=False,
    )
    db_session.add(user)
    db_session.add(SettingsModel(id=1, storage_path=str(tmp_path)))
    await db_session.flush()

    with pytest.raises(ValueError, match="Account setup and TOTP verification"):
        await complete_setup(db_session)


# Test that complete_setup with no storage raises ValueError
@pytest.mark.asyncio
async def test_complete_setup_no_storage(db_session: AsyncSession):
    totp_secret = pyotp.random_base32()
    user = User(
        username=VALID_USERNAME,
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(ValueError, match="Storage must be configured"):
        await complete_setup(db_session)


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


# Test that _validate_password accepts a valid password
def test_validate_password_valid():
    # Should not raise
    _validate_password("ValidP@ssw0rd!")


# Test that _validate_storage_path rejects nonexistent directories
def test_validate_storage_path_nonexistent():
    with pytest.raises(ValueError, match="does not exist"):
        _validate_storage_path("/nonexistent/path/xyz123")


# Test that _validate_storage_path accepts a valid directory
def test_validate_storage_path_valid(tmp_path):
    result = _validate_storage_path(str(tmp_path))
    assert result == str(tmp_path.resolve())
