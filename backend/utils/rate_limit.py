"""Tiny in-memory sliding-window rate limiter (per process).
In production, put this behind an API gateway or Redis so the limit is shared
across multiple backend instances instead of counted separately on each one."""
import threading
import time
from collections import defaultdict, deque

from backend.utils.errors import TooManyRequests


class RateLimiter:
    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window_seconds:
                q.popleft()
            if len(q) >= limit:
                raise TooManyRequests("Too many attempts. Please wait a minute and try again.")
            q.append(now)


auth_rate_limiter = RateLimiter()
