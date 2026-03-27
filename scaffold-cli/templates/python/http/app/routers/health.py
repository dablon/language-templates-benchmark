"""
Health Check Router
"""

from fastapi import APIRouter

from app import __service__, __version__

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": __service__,
        "version": __version__
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check - can the service handle requests?"""
    return {
        "status": "ready",
        "service": __service__
    }