"""Unit tests for data isolation between organizations."""
import pytest
from fastapi.testclient import TestClient


def test_org_a_does_not_see_org_b_employees(client: TestClient) -> None:
    """Org A search returns only org_a employees."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_a"})
    assert r.status_code == 200
    data = r.json()
    # org_b has Charlie, Diana, John Smith - none should appear for org_a
    names = [item.get("name", "") for item in data["items"]]
    assert "Charlie Wilson" not in names
    assert "Diana Prince" not in names


def test_org_b_does_not_see_org_a_employees(client: TestClient) -> None:
    """Org B search returns only org_b employees."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_b"})
    assert r.status_code == 200
    data = r.json()
    names = [item.get("name", "") for item in data["items"]]
    assert "John Doe" not in names  # org_a
    assert "Jane Smith" not in names  # org_a
    assert "Alice Brown" not in names  # org_a


def test_no_org_id_leak_in_response(client: TestClient) -> None:
    """Response items never contain org_id."""
    for org in ["org_a", "org_b", "org_default"]:
        r = client.get("/api/v1/employees/search", params={"org_id": org})
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert "org_id" not in item
