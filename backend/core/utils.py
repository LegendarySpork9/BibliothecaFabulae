# Load libraries
from datetime import UTC, datetime


# Returns the current UTC time without timezone info
def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
