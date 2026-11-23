# Load libraries
import tempfile

import pyotp
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

VALID_PASSWORD = "SecureP@ss123!"
VALID_USERNAME = "setupuser"


# Run the full setup wizard through to completion and return the TOTP secret
async def _run_full_setup(
    client: AsyncClient,
    db: AsyncSession,
    username: str = VALID_USERNAME,
    password: str = VALID_PASSWORD,
) -> str:
    account_resp = await client.post(
        "/api/setup/account",
        json={
            "username": username,
            "password": password,
            "password_confirm": password,
        },
    )
    assert account_resp.status_code == 200
    totp_secret = account_resp.json()["totp_secret"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    verify_resp = await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": code},
    )
    assert verify_resp.status_code == 200

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_resp = await client.post(
            "/api/setup/storage",
            json={"storage_path": tmp_dir},
        )
        assert storage_resp.status_code == 200

    return totp_secret


# Test that creating an account returns TOTP provisioning data
@pytest.mark.asyncio
async def test_create_account_returns_totp_data(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    assert response.status_code == 200

    data = response.json()
    assert "totp_secret" in data
    assert "totp_uri" in data
    assert "qr_code_base64" in data
    assert len(data["totp_secret"]) > 0
    assert "BibliothecaFabulae" in data["totp_uri"]


# Test that mismatched passwords return 400
@pytest.mark.asyncio
async def test_create_account_mismatched_passwords(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": "DifferentP@ss123!",
        },
    )
    assert response.status_code == 400
    assert "do not match" in response.json()["detail"]


# Test that a short password returns 400
@pytest.mark.asyncio
async def test_create_account_short_password(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": "Short1!",
            "password_confirm": "Short1!",
        },
    )
    assert response.status_code == 400
    assert "12 characters" in response.json()["detail"]


# Test that a password missing uppercase returns 400
@pytest.mark.asyncio
async def test_create_account_password_no_uppercase(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": "nouppercase123!",
            "password_confirm": "nouppercase123!",
        },
    )
    assert response.status_code == 400
    assert "uppercase" in response.json()["detail"]


# Test that an invalid username returns 400
@pytest.mark.asyncio
async def test_create_account_invalid_username(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/account",
        json={
            "username": "ab",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    assert response.status_code == 400
    assert "Username" in response.json()["detail"]


# Test that verifying TOTP with a valid code succeeds
@pytest.mark.asyncio
async def test_verify_totp_valid_code(
    client: AsyncClient, db_session: AsyncSession
):
    account_resp = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    totp_secret = account_resp.json()["totp_secret"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    response = await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": code},
    )
    assert response.status_code == 200
    assert response.json()["verified"] is True


# Test that verifying TOTP with an invalid code returns 400
@pytest.mark.asyncio
async def test_verify_totp_invalid_code(
    client: AsyncClient, db_session: AsyncSession
):
    await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )

    response = await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": "000000"},
    )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


# Test that verifying TOTP without a user returns 400
@pytest.mark.asyncio
async def test_verify_totp_no_user(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": "123456"},
    )
    assert response.status_code == 400


# Test that configuring storage with a valid path succeeds
@pytest.mark.asyncio
async def test_configure_storage_valid_path(
    client: AsyncClient, db_session: AsyncSession
):
    await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        response = await client.post(
            "/api/setup/storage",
            json={"storage_path": tmp_dir},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is True
        assert data["total_bytes"] > 0
        assert data["free_bytes"] > 0


# Test that configuring storage with a nonexistent path returns 400
@pytest.mark.asyncio
async def test_configure_storage_invalid_path(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/setup/storage",
        json={"storage_path": "/nonexistent/path/that/does/not/exist"},
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


# Test that completing setup succeeds when all steps are done
@pytest.mark.asyncio
async def test_complete_setup_all_steps_done(
    client: AsyncClient, db_session: AsyncSession
):
    await _run_full_setup(client, db_session)

    response = await client.post("/api/setup/complete")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "access_token" in data
    assert len(data["access_token"]) > 0


# Test that completing setup fails when steps are incomplete
@pytest.mark.asyncio
async def test_complete_setup_incomplete_steps(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.post("/api/setup/complete")
    assert response.status_code == 400


# Test that completing setup fails when only account is created
@pytest.mark.asyncio
async def test_complete_setup_missing_storage(
    client: AsyncClient, db_session: AsyncSession
):
    account_resp = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    totp_secret = account_resp.json()["totp_secret"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": code},
    )

    response = await client.post("/api/setup/complete")
    assert response.status_code == 400
    assert "Storage" in response.json()["detail"]


# Test that the setup status endpoint returns the current step
@pytest.mark.asyncio
async def test_setup_status_initial(
    client: AsyncClient, db_session: AsyncSession
):
    response = await client.get("/api/setup/status")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is False
    assert data["current_step"] == 1


# Test that the setup status advances after creating an account
@pytest.mark.asyncio
async def test_setup_status_after_account(
    client: AsyncClient, db_session: AsyncSession
):
    await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )

    response = await client.get("/api/setup/status")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is False
    assert data["current_step"] == 2


# Test that the setup status reaches step 3 after TOTP verification
@pytest.mark.asyncio
async def test_setup_status_after_totp(
    client: AsyncClient, db_session: AsyncSession
):
    account_resp = await client.post(
        "/api/setup/account",
        json={
            "username": VALID_USERNAME,
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    totp_secret = account_resp.json()["totp_secret"]

    totp = pyotp.TOTP(totp_secret)
    code = totp.now()

    await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": code},
    )

    response = await client.get("/api/setup/status")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is False
    assert data["current_step"] == 3


# Test that setup endpoints return 403 after setup is complete
@pytest.mark.asyncio
async def test_setup_endpoints_blocked_after_complete(
    client: AsyncClient, db_session: AsyncSession
):
    await _run_full_setup(client, db_session)
    await client.post("/api/setup/complete")

    account_resp = await client.post(
        "/api/setup/account",
        json={
            "username": "anotheruser",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    assert account_resp.status_code == 403
    assert "already complete" in account_resp.json()["detail"]

    verify_resp = await client.post(
        "/api/setup/verify-totp",
        json={"totp_code": "123456"},
    )
    assert verify_resp.status_code == 403

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_resp = await client.post(
            "/api/setup/storage",
            json={"storage_path": tmp_dir},
        )
        assert storage_resp.status_code == 403

    complete_resp = await client.post("/api/setup/complete")
    assert complete_resp.status_code == 403


# Test that re-creating an account resets the existing user
@pytest.mark.asyncio
async def test_create_account_resets_existing_user(
    client: AsyncClient, db_session: AsyncSession
):
    first_resp = await client.post(
        "/api/setup/account",
        json={
            "username": "firstuser",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    assert first_resp.status_code == 200

    second_resp = await client.post(
        "/api/setup/account",
        json={
            "username": "seconduser",
            "password": VALID_PASSWORD,
            "password_confirm": VALID_PASSWORD,
        },
    )
    assert second_resp.status_code == 200

    second_data = second_resp.json()
    assert "totp_secret" in second_data


# Test that setup status returns step 4 after SMTP-pending state
@pytest.mark.asyncio
async def test_setup_status_step_4_after_storage(
    client: AsyncClient, db_session: AsyncSession
):
    await _run_full_setup(client, db_session)

    response = await client.get("/api/setup/status")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is False
    assert data["current_step"] == 4


# Test that setup endpoints return 403 when setup_complete is True via DB
@pytest.mark.asyncio
async def test_setup_endpoints_403_when_complete_via_db(
    client: AsyncClient, db_session: AsyncSession
):
    from backend.models.settings import Settings as SettingsModel
    from backend.models.user import User as UserModel
    from backend.core.auth import hash_password
    from backend.core.config import settings
    from backend.core.encryption import encrypt

    totp_secret = pyotp.random_base32()
    user = UserModel(
        username="guarduser",
        password_hash=hash_password(VALID_PASSWORD),
        totp_secret_encrypted=encrypt(totp_secret, settings.ENCRYPTION_KEY),
        totp_verified=True,
    )
    db_session.add(user)

    app_settings = SettingsModel(
        id=1,
        storage_path="/tmp/test",
        smtp_host="smtp.example.com",
        setup_complete=True,
    )
    db_session.add(app_settings)
    await db_session.flush()

    status_resp = await client.get("/api/setup/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["setup_complete"] is True

    smtp_resp = await client.post(
        "/api/setup/smtp",
        json={
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_username": "user",
            "smtp_password": "pass",
            "smtp_use_tls": True,
            "smtp_from_address": "from@test.com",
            "smtp_to_address": "to@test.com",
        },
    )
    assert smtp_resp.status_code == 403

    complete_resp = await client.post("/api/setup/complete")
    assert complete_resp.status_code == 403


# Test that POST /api/setup/smtp saves SMTP config after steps 1-3
@pytest.mark.asyncio
async def test_setup_smtp_saves_config(
    client: AsyncClient, db_session: AsyncSession
):
    await _run_full_setup(client, db_session)

    response = await client.post(
        "/api/setup/smtp",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_password": "smtppass",
            "smtp_use_tls": True,
            "smtp_from_address": "from@example.com",
            "smtp_to_address": "to@example.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["configured"] is True


# Test that GET /api/setup/status returns step 5 after all steps complete but not finalised
@pytest.mark.asyncio
async def test_setup_status_step_5_after_smtp(
    client: AsyncClient, db_session: AsyncSession
):
    await _run_full_setup(client, db_session)

    await client.post(
        "/api/setup/smtp",
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user@example.com",
            "smtp_password": "smtppass",
            "smtp_use_tls": True,
            "smtp_from_address": "from@example.com",
            "smtp_to_address": "to@example.com",
        },
    )

    response = await client.get("/api/setup/status")
    assert response.status_code == 200

    data = response.json()
    assert data["setup_complete"] is False
    assert data["current_step"] == 5
