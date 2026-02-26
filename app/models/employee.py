"""
Employee data model.
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class Employee:
    """Employee entity - internal representation."""

    id: str
    org_id: str
    name: str
    email: str
    department: str
    location: str
    position: str

    def to_dict(self) -> dict[str, Any]:
        """Return all fields as dict for filtering and projection."""
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "email": self.email,
            "department": self.department,
            "location": self.location,
            "position": self.position,
        }
