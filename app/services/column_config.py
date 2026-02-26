"""
Organization column configuration.
Hardcoded per org - defines which fields are visible and in what order.
"""
from typing import Final

# Allowed column names - whitelist to prevent injection/leak
ALLOWED_COLUMNS: Final[frozenset[str]] = frozenset({
    "id", "name", "email", "department", "location", "position"
})

# org_id -> ordered list of visible columns
# org_id is NEVER exposed in response; used only for lookup
_ORG_COLUMN_CONFIG: dict[str, list[str]] = {
    "org_a": ["name", "email", "department", "location"],
    "org_b": ["name", "department", "position"],
    "org_default": ["id", "name", "email", "department", "location", "position"],
}


def get_org_columns(org_id: str) -> list[str]:
    """
    Get ordered list of visible columns for an organization.
    Returns default config if org not found.
    Only returns columns that exist in ALLOWED_COLUMNS.
    """
    raw = _ORG_COLUMN_CONFIG.get(org_id, _ORG_COLUMN_CONFIG["org_default"])
    return [c for c in raw if c in ALLOWED_COLUMNS]
