# Load libraries
import sys

from pydantic_settings import BaseSettings

_INSECURE_DEFAULT = "change-me-in-production"


# Defines application settings with environment variable overrides
class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bibliothecafabulae.db"
    SECRET_KEY: str = _INSECURE_DEFAULT
    ENCRYPTION_KEY: str = _INSECURE_DEFAULT
    ENCRYPTION_KEY_PREVIOUS: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    LOG_DIR: str = "./logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def validate_secrets() -> None:
    if settings.ENVIRONMENT == "development":
        return

    if settings.SECRET_KEY == _INSECURE_DEFAULT:
        print("FATAL: SECRET_KEY must be set in production — see .env.example", file=sys.stderr)
        sys.exit(1)

    if settings.ENCRYPTION_KEY == _INSECURE_DEFAULT:
        print("FATAL: ENCRYPTION_KEY must be set in production — see .env.example", file=sys.stderr)
        sys.exit(1)
