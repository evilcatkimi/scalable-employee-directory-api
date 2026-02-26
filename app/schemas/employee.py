"""
Pydantic schemas for Search API.
"""
from typing import Any

from pydantic import BaseModel, Field


class EmployeeSearchRequest(BaseModel):
    """Search request with filters and pagination."""

    org_id: str = Field(..., description="Organization ID", examples=["org_a"])
    name: str | None = Field(None, description="Partial match on name")
    department: str | None = Field(None, description="Exact match on department")
    location: str | None = Field(None, description="Exact match on location")
    position: str | None = Field(None, description="Exact match on position")
    limit: int = Field(20, ge=1, le=100, description="Page size")
    offset: int = Field(0, ge=0, description="Offset for pagination")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"org_id": "org_a", "name": "John", "limit": 10, "offset": 0},
                {"org_id": "org_b", "department": "Engineering", "limit": 20},
            ]
        }
    }


# EmployeeItem: each item is a dict with only org-configured fields.
# Type alias for clarity; actual response uses list[dict[str, Any]]
EmployeeItem = dict[str, Any]


class EmployeeSearchResponse(BaseModel):
    """Search response with pagination metadata."""

    items: list[dict[str, Any]] = Field(
        ...,
        description="List of employees - fields per org config (name, email, etc.)",
    )
    total: int = Field(..., description="Total matching count")
    limit: int = Field(..., description="Page size used")
    offset: int = Field(..., description="Offset used")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {"name": "John Doe", "email": "john@example.com", "department": "Engineering", "location": "HN"}
                    ],
                    "total": 1,
                    "limit": 10,
                    "offset": 0,
                }
            ]
        }
    }
