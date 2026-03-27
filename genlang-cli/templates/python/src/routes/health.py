"""
Health Check Endpoint

Provides a simple health check endpoint for load balancers and monitoring.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from .. import __service__, __version__


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str | None = None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns a JSON response indicating service health.
    """
    return HealthResponse(
        status="healthy",
        service=__service__,
        version=__version__,
    )
