"""Rate limiting using only Python standard library.

Sliding window per (org_id or IP).
Configuration is centralized in `app.config.RATE_LIMIT_CONFIG`.
"""
import threading
import time
from collections import deque

from fastapi import Request

from app.config import RATE_LIMIT_CONFIG


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter.
    Uses deque of timestamps - no external deps.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._cache: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _clean_old(self, key: str, now: float) -> None:
        """Remove timestamps outside the window."""
        q = self._cache[key]
        cutoff = now - self.window_seconds
        while q and q[0] < cutoff:
            q.popleft()

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed. If yes, records the request."""
        now = time.monotonic()
        with self._lock:
            if key not in self._cache:
                self._cache[key] = deque()
            self._clean_old(key, now)
            q = self._cache[key]
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            return True

# Global limiter configured via RATE_LIMIT_CONFIG
_limiter = SlidingWindowRateLimiter(
    max_requests=RATE_LIMIT_CONFIG.requests_per_minute,
    window_seconds=RATE_LIMIT_CONFIG.window_seconds,
)


def get_client_key(request: Request, org_id: str | None = None) -> str:
    """
    Rate limit key: prefer org_id, fallback to IP.
    """
    if org_id:
        return f"org:{org_id}"
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return f"ip:{ip}"


def check_rate_limit(request: Request, org_id: str) -> None:
    """
    Dependency: raises 429 if rate limit exceeded.
    Call with org_id from the route (we have it as query param).
    """
    key = get_client_key(request, org_id)
    if not _limiter.is_allowed(key):
        raise RateLimitExceeded()


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    pass
