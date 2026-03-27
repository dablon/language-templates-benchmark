"""
Web Endpoints

HTML web endpoints that serve static content.
"""

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


def _load_index_html() -> str:
    """Load the index.html file."""
    static_path = Path(__file__).parent.parent.parent / "static" / "index.html"
    if static_path.exists():
        return static_path.read_text()
    # Fallback HTML if file doesn't exist
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Python Web Service</title>
    </head>
    <body>
        <h1>🐍 Python Web Service</h1>
        <p>Static files not found.</p>
    </body>
    </html>
    """


@router.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """
    GET /

    Serves the main HTML page.
    """
    return HTMLResponse(content=_load_index_html())
