"""Unit tests for rate limiting."""
import pytest
from fastapi.testclient import TestClient

# Rate limit: 100 req/min per org. We use a fresh limiter per test via import reset.
# For deterministic tests, we need to exhaust the limit.
# Note: TestClient reuses the app; the limiter is a global singleton.
# To test 429 we need to make 101 requests for the same org_id.


def test_rate_limit_returns_429_when_exceeded(client: TestClient) -> None:
    """When limit exceeded, API returns 429."""
    # Reset limiter by reimporting - tricky with singleton.
    # Alternative: use a small limit for testing. We can't easily change the limiter.
    # Better: patch the limiter in test to use max_requests=2.
    from app.middleware import rate_limit as rl_mod

    # Temporarily use a limiter with max_requests=2
    original_limiter = rl_mod._limiter
    rl_mod._limiter = rl_mod.SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

    try:
        # First two requests succeed
        for _ in range(2):
            r = client.get(
                "/api/v1/employees/search",
                params={"org_id": "org_ratelimit_test"},
            )
            assert r.status_code == 200

        # Third request gets 429
        r = client.get(
            "/api/v1/employees/search",
            params={"org_id": "org_ratelimit_test"},
        )
        assert r.status_code == 429
        assert "retry" in r.json().get("detail", "").lower() or "rate" in r.json().get("detail", "").lower()
        assert r.headers.get("Retry-After") == "60"
    finally:
        rl_mod._limiter = original_limiter


def test_rate_limit_per_org_isolation(client: TestClient) -> None:
    """Rate limit is per org - exhausting org_a does not affect org_b."""
    from app.middleware import rate_limit as rl_mod

    original = rl_mod._limiter
    rl_mod._limiter = rl_mod.SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

    try:
        for _ in range(2):
            client.get("/api/v1/employees/search", params={"org_id": "org_limit_a"})
        r_a = client.get("/api/v1/employees/search", params={"org_id": "org_limit_a"})
        assert r_a.status_code == 429

        r_b = client.get("/api/v1/employees/search", params={"org_id": "org_limit_b"})
        assert r_b.status_code == 200  # org_b still has quota
    finally:
        rl_mod._limiter = original


def test_non_search_endpoint_not_rate_limited(client: TestClient) -> None:
    """Other endpoints (e.g. docs) are not rate limited."""
    # /docs might redirect or return 200
    r = client.get("/docs")
    assert r.status_code in (200, 307)
