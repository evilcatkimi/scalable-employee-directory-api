"""Application configuration for the service."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limit settings per organization (hard-coded defaults)."""

    # You can edit these constants directly if needed.
    requests_per_minute: int = 2
    window_seconds: int = 60


RATE_LIMIT_CONFIG = RateLimitConfig()
