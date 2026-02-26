"""Unit tests for Search API."""
import pytest
from fastapi.testclient import TestClient


def test_search_returns_200(client: TestClient) -> None:
    """Search API returns 200 with valid params."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_a"})
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)


def test_search_with_filters(client: TestClient) -> None:
    """Search with name filter returns matching employees."""
    r = client.get(
        "/api/v1/employees/search",
        params={"org_id": "org_a", "name": "john"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any("john" in str(item.get("name", "")).lower() for item in data["items"])


def test_search_pagination(client: TestClient) -> None:
    """Pagination limit and offset work correctly."""
    r = client.get(
        "/api/v1/employees/search",
        params={"org_id": "org_a", "limit": 2, "offset": 0},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) <= 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    r2 = client.get(
        "/api/v1/employees/search",
        params={"org_id": "org_a", "limit": 2, "offset": 2},
    )
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["offset"] == 2


def test_search_requires_org_id(client: TestClient) -> None:
    """Search fails without org_id."""
    r = client.get("/api/v1/employees/search")
    assert r.status_code == 422  # validation error


def test_search_department_filter(client: TestClient) -> None:
    """Department exact match filter works."""
    r = client.get(
        "/api/v1/employees/search",
        params={"org_id": "org_a", "department": "Engineering"},
    )
    assert r.status_code == 200
    data = r.json()
    for item in data["items"]:
        assert item.get("department") == "Engineering"
