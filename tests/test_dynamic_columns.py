"""Unit tests for dynamic columns per organization."""
import pytest
from fastapi.testclient import TestClient


def test_org_a_columns(client: TestClient) -> None:
    """Org A returns only name, email, department, location."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_a"})
    assert r.status_code == 200
    data = r.json()
    for item in data["items"]:
        keys = set(item.keys())
        expected = {"name", "email", "department", "location"}
        assert keys == expected, f"Expected {expected}, got {keys}"
        assert "org_id" not in item
        assert "id" not in item
        assert "position" not in item


def test_org_b_columns(client: TestClient) -> None:
    """Org B returns only name, department, position."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_b"})
    assert r.status_code == 200
    data = r.json()
    for item in data["items"]:
        keys = set(item.keys())
        expected = {"name", "department", "position"}
        assert keys == expected, f"Expected {expected}, got {keys}"
        assert "email" not in item
        assert "location" not in item
        assert "org_id" not in item


def test_org_default_columns(client: TestClient) -> None:
    """Unknown org uses default: id, name, email, department, location, position."""
    r = client.get("/api/v1/employees/search", params={"org_id": "unknown_org"})
    assert r.status_code == 200
    data = r.json()
    if data["items"]:
        item = data["items"][0]
        expected = {"id", "name", "email", "department", "location", "position"}
        assert set(item.keys()) == expected


def test_column_order_follows_config(client: TestClient) -> None:
    """Column order in response follows org config."""
    r = client.get("/api/v1/employees/search", params={"org_id": "org_a"})
    assert r.status_code == 200
    data = r.json()
    expected_order = ["name", "email", "department", "location"]
    for item in data["items"]:
        assert list(item.keys()) == expected_order
