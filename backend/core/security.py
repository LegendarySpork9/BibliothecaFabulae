# Load libraries
import time
import threading

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 900


class LoginAttemptTracker:

    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def record_failure(self, key: str) -> None:
        now = time.monotonic()

        with self._lock:
            entries = self._attempts.setdefault(key, [])
            entries.append(now)
            self._attempts[key] = [
                t for t in entries if now - t < _LOCKOUT_SECONDS
            ]

    def is_locked_out(self, key: str) -> bool:
        now = time.monotonic()

        with self._lock:
            entries = self._attempts.get(key, [])
            entries = [t for t in entries if now - t < _LOCKOUT_SECONDS]
            self._attempts[key] = entries

            return len(entries) >= _MAX_ATTEMPTS

    def clear(self, key: str) -> None:
        with self._lock:
            self._attempts.pop(key, None)

    def reset(self) -> None:
        with self._lock:
            self._attempts.clear()


login_attempts = LoginAttemptTracker()
