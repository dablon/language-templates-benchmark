"""
Python Web Service Template

A high-performance web service template using FastAPI.
Part of the Language Templates Benchmark project.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from . import __version__
from .config import settings
from .routes import api, web, health

# Create FastAPI application
app = FastAPI(
    title="Python Web Service Template",
    description="High-performance web service template for benchmarking",
    version=__version__,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(api.router, prefix="/api", tags=["API"])
app.include_router(web.router, tags=["Web"])


def create_app() -> FastAPI:
    """Factory function to create the application."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development",
    )
