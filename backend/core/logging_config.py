# Load libraries
import logging
import os
import re
from logging.handlers import RotatingFileHandler

from backend.core.config import settings

_SENSITIVE_PATTERN = re.compile(
    r'(?i)(password|secret|token|key|authorization|cookie)["\s:=]+\S+',
)


class _RedactingFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE_PATTERN.sub(r"\1=***REDACTED***", record.msg)

        return True


# Sets up rotating file log handler with optional console output
def setup_logging() -> None:
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    redact_filter = _RedactingFilter()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        os.path.join(settings.LOG_DIR, "app.log"),
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redact_filter)
    root_logger.addHandler(file_handler)

    if settings.ENVIRONMENT == "development":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(redact_filter)
        root_logger.addHandler(console_handler)
