# Load libraries
import pytest

from backend.core.config import Settings, _INSECURE_DEFAULT, validate_secrets


# Test that Settings has correct default values
def test_settings_defaults():
    s = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test-key",
        ENCRYPTION_KEY="test-enc",
    )

    assert s.CORS_ORIGINS == ["http://localhost:5173"]
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert s.ENVIRONMENT == "production"
    assert s.LOG_BACKUP_COUNT == 5
    assert s.LOG_MAX_BYTES == 10 * 1024 * 1024
    assert s.ENCRYPTION_KEY_PREVIOUS == ""


# Test that validate_secrets does not exit in development mode
def test_validate_secrets_development_mode(monkeypatch):
    monkeypatch.setattr(
        "backend.core.config.settings.ENVIRONMENT", "development"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.SECRET_KEY", _INSECURE_DEFAULT
    )
    monkeypatch.setattr(
        "backend.core.config.settings.ENCRYPTION_KEY", _INSECURE_DEFAULT
    )

    # Should not raise or exit
    validate_secrets()


# Test that validate_secrets exits when SECRET_KEY is default in production
def test_validate_secrets_exits_on_default_secret_key(monkeypatch):
    monkeypatch.setattr(
        "backend.core.config.settings.ENVIRONMENT", "production"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.SECRET_KEY", _INSECURE_DEFAULT
    )
    monkeypatch.setattr(
        "backend.core.config.settings.ENCRYPTION_KEY", "real-encryption-key"
    )

    with pytest.raises(SystemExit) as exc_info:
        validate_secrets()

    assert exc_info.value.code == 1


# Test that validate_secrets exits when ENCRYPTION_KEY is default in production
def test_validate_secrets_exits_on_default_encryption_key(monkeypatch):
    monkeypatch.setattr(
        "backend.core.config.settings.ENVIRONMENT", "production"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.SECRET_KEY", "real-secret-key"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.ENCRYPTION_KEY", _INSECURE_DEFAULT
    )

    with pytest.raises(SystemExit) as exc_info:
        validate_secrets()

    assert exc_info.value.code == 1


# Test that validate_secrets passes when both keys are set in production
def test_validate_secrets_passes_with_real_keys(monkeypatch):
    monkeypatch.setattr(
        "backend.core.config.settings.ENVIRONMENT", "production"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.SECRET_KEY", "real-secret-key"
    )
    monkeypatch.setattr(
        "backend.core.config.settings.ENCRYPTION_KEY", "real-encryption-key"
    )

    # Should not raise or exit
    validate_secrets()
