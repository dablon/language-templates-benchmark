"""
API Endpoints

REST API endpoints that return JSON responses.
"""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from .. import __service__, __version__


router = APIRouter()


class HelloResponse(BaseModel):
    """Hello API response model."""
    message: str
    service: str
    version: str


@router.get("/hello", response_model=HelloResponse)
async def hello() -> HelloResponse:
    """
    GET /api/hello

    Returns a JSON greeting message.
    """
    return HelloResponse(
        message="Hello from Python!",
        service=__service__,
        version=__version__,
    )


@router.post("/echo")
async def echo(request: Request) -> Response:
    """
    POST /api/echo

    Echoes back the request body.
    """
    body = await request.body()
    return Response(
        content=body,
        media_type="text/plain",
    )
