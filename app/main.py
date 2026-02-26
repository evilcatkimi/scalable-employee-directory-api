"""
HR Employee Search Microservice - FastAPI application.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.employees import router as employees_router
from app.middleware.rate_limit import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    yield


app = FastAPI(
    title="HR Employee Search API",
    description="Search employees within organizations. Dynamic columns per org.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
        headers={"Retry-After": "60"},
    )


app.include_router(employees_router, prefix="/api/v1")
