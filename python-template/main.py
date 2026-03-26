import os
import asyncio
import time
from typing import Dict, List, Any
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import httpx

app = FastAPI()

SERVICE_NAME = "python-template"
VERSION = "0.1.0"

# Service endpoints configuration
SERVICE_ENDPOINTS = {
    "rust": os.getenv("RUST_SERVICE_URL", "http://localhost:3001"),
    "go": os.getenv("GO_SERVICE_URL", "http://localhost:3002"),
    "c": os.getenv("C_SERVICE_URL", "http://localhost:3004"),
}


async def call_service(service_key: str, path: str) -> Dict[str, Any]:
    """Make an async HTTP call to a service."""
    url = SERVICE_ENDPOINTS.get(service_key)
    if not url:
        return {"service": service_key, "error": "service not found", "success": False}

    full_url = f"{url}{path}"
    start_time = time.time()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(full_url)
            elapsed_ms = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                data = response.json()
                data["success"] = True
                data["elapsed_ms"] = elapsed_ms
                return data
            else:
                return {
                    "service": service_key,
                    "error": response.text,
                    "status": response.status_code,
                    "success": False,
                    "elapsed_ms": elapsed_ms,
                }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "service": service_key,
            "error": str(e),
            "success": False,
            "elapsed_ms": elapsed_ms,
        }


async def call_all_services(path: str) -> List[Dict[str, Any]]:
    """Call all services in parallel."""
    tasks = [call_service(key, path) for key in SERVICE_ENDPOINTS]
    return await asyncio.gather(*tasks)

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Template - Web Service</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #4caf50; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }
        code { background: #0f3460; padding: 2px 6px; border-radius: 4px; }
        a { color: #4caf50; }
    </style>
</head>
<body>
    <h1>🐍 Python Web Service Template</h1>
    <div class="card">
        <h2>Language: Python</h2>
        <p>Framework: <code>FastAPI</code></p>
        <p>Port: <code>3003</code></p>
    </div>
    <div class="card">
        <h2>Endpoints</h2>
        <ul>
            <li><a href="/health">GET /health</a> - Health check</li>
            <li><a href="/api/hello">GET /api/hello</a> - JSON response</li>
            <li>POST /api/echo - Echo body</li>
        </ul>
    </div>
</body>
</html>
"""

@app.get("/")
async def index():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": SERVICE_NAME
    }

@app.get("/api/hello")
async def hello():
    return {
        "message": "Hello from Python!",
        "service": SERVICE_NAME,
        "version": VERSION
    }

@app.post("/api/echo")
async def echo(request: Request):
    body = await request.body()
    return Response(content=body, media_type="text/plain")


# ============================================
# Inter-service Communication Endpoints
# ============================================

@app.get("/internal/aggregate")
async def aggregate():
    """Call all services and aggregate responses."""
    start_time = time.time()
    results = await call_all_services("/api/hello")
    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "caller": SERVICE_NAME,
        "results": results,
        "total_time_ms": total_time_ms,
    }


@app.post("/internal/chain")
async def chain(request: Request):
    """Chain service calls sequentially."""
    start_time = time.time()

    try:
        body = await request.json()
        payload = body.get("payload", "")
    except:
        payload = ""

    # Python -> Rust -> Go -> C
    rust_result = await call_service("rust", "/api/hello")
    go_result = await call_service("go", "/api/hello")

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "service": SERVICE_NAME,
        "chain": [rust_result, go_result],
        "total_time_ms": total_time_ms,
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3003"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
