"""
Search Employee API.
"""
from fastapi import APIRouter, Depends, Query, Request

from app.middleware.rate_limit import check_rate_limit
from app.schemas.employee import EmployeeSearchRequest, EmployeeSearchResponse
from app.services.employee_search import EmployeeSearchService

router = APIRouter(prefix="/employees", tags=["employees"])


async def verify_rate_limit(request: Request, org_id: str = Query(...)) -> str:
    """Dependency: check rate limit by org_id, return org_id for route."""
    check_rate_limit(request, org_id)
    return org_id


@router.get(
    "/search",
    response_model=EmployeeSearchResponse,
    summary="Search employees",
    description="Search employees with filters. Returns only columns configured for the organization.",
    responses={
        200: {"description": "Success"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def search_employees(
    request: Request,
    org_id: str = Depends(verify_rate_limit),
    name: str | None = Query(None, description="Partial match on name"),
    department: str | None = Query(None, description="Exact match on department"),
    location: str | None = Query(None, description="Exact match on location"),
    position: str | None = Query(None, description="Exact match on position"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> EmployeeSearchResponse:
    """
    Search employees within an organization.

    - **org_id**: Required. Filters by organization.
    - **name**: Optional partial match (case-insensitive).
    - **department**, **location**, **position**: Optional exact match.
    - **limit**, **offset**: Pagination.

    Response fields depend on organization column config.
    """
    req = EmployeeSearchRequest(
        org_id=org_id,
        name=name,
        department=department,
        location=location,
        position=position,
        limit=limit,
        offset=offset,
    )
    return EmployeeSearchService.search(req)
