"""
API Router - Core benchmark endpoints
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app import __service__, __version__
from services import compute as compute_service
from services import echo as echo_service

router = APIRouter()


class HelloResponse(BaseModel):
    message: str
    service: str
    version: str


@router.get("/hello", response_model=HelloResponse)
async def hello() -> HelloResponse:
    """GET /api/hello - JSON greeting endpoint"""
    return HelloResponse(
        message=f"Hello from {__service__}!",
        service=__service__,
        version=__version__
    )


@router.get("/compute")
async def compute(n: int = 30):
    """
    GET /api/compute - CPU benchmark endpoint
    Performs fibonacci and prime number calculation
    """
    return compute_service.execute(n)


@router.post("/echo")
async def echo(request: Request):
    """
    POST /api/echo - Echo endpoint
    Returns transformed version of request body
    """
    body = await request.body()
    return echo_service.process(body)