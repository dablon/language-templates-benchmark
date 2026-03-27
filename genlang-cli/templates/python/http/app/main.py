"""
Main Application Entry Point
FastAPI application with clean architecture structure
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app import __service__, __version__
from app.routers import api, health, web

app = FastAPI(
    title=__service__.replace("-", " ").title(),
    version=__version__,
    description="Benchmark web service"
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(api.router, prefix="/api", tags=["api"])
app.include_router(web.router, tags=["web"])


@app.get("/", response_class=HTMLResponse)
async def index():
    """Root endpoint serving index.html"""
    html_path = static_path / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content=f"<h1>{__service__}</h1><p>Version: {__version__}</p>")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3003"))
    uvicorn.run(app, host="0.0.0.0", port=port)