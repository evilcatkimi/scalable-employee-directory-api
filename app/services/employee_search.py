"""
Employee search service.
Applies column config and returns only allowed fields in correct order.
Backed by SQLite via the Python standard library (`sqlite3`).
"""
from app.db.sqlite_store import SearchFilters, get_employee_store
from app.models.employee import Employee
from app.schemas.employee import EmployeeSearchRequest, EmployeeSearchResponse
from app.services.column_config import get_org_columns


class EmployeeSearchService:
    """Search employees with org-specific column projection."""

    @staticmethod
    def search(req: EmployeeSearchRequest) -> EmployeeSearchResponse:
        """
        Search employees, filter by org + criteria, paginate,
        and project only org-configured columns.
        """
        store = get_employee_store()
        filters = SearchFilters(
            org_id=req.org_id,
            name=req.name,
            department=req.department,
            location=req.location,
            position=req.position,
            limit=req.limit,
            offset=req.offset,
        )
        employees, total = store.search(filters)
        columns = get_org_columns(req.org_id)
        items = [_project_employee(e, columns) for e in employees]
        return EmployeeSearchResponse(
            items=items,
            total=total,
            limit=req.limit,
            offset=req.offset,
        )


def _project_employee(employee: Employee, columns: list[str]) -> dict:
    """
    Project employee to dict with ONLY specified columns in order.
    NEVER includes org_id or any field not in columns.
    """
    d = employee.to_dict()
    # Build result in config order, only allowed columns
    result: dict = {}
    for col in columns:
        if col in d:
            result[col] = d[col]
    return result
