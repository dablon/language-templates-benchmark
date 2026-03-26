import os
import asyncio
import time
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import httpx

app = FastAPI()

SERVICE_NAME = "python-template"
VERSION = "0.1.0"

# Database connection
db_pool = None

async def init_db():
    """Initialize database connection pool based on ENABLE_DATABASE flag."""
    global db_pool
    enable_db = os.getenv("ENABLE_DATABASE", "false").lower() == "true"
    if not enable_db:
        print("ENABLE_DATABASE=false, skipping database connection")
        return

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            from asyncpg import create_pool
            db_pool = await create_pool(database_url, min_size=2, max_size=10)
            print("PostgreSQL connected successfully")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            db_pool = None
    else:
        print("DATABASE_URL not set, skipping database connection")

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


# ============================================
# gRPC-style Endpoints (JSON over HTTP)
# ============================================

@app.post("/grpc/hello")
async def grpc_hello(request: Request):
    """gRPC-style Hello endpoint."""
    try:
        body = await request.json()
        name = body.get("name", "world")
    except:
        name = "world"

    start_time = time.time()
    results = []

    for service_key, url in SERVICE_ENDPOINTS.items():
        svc_start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/api/hello")
                elapsed = int((time.time() - svc_start) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", "")
                    results.append(f"{service_key}: {msg} ({elapsed}ms)")
        except Exception as e:
            results.append(f"{service_key}: error - {e}")

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "service_name": SERVICE_NAME,
        "message": f"Hello from Python! Greeted: {name}",
        "version": VERSION,
        "timestamp": int(time.time()),
        "results": results,
    }


@app.get("/grpc/health")
async def grpc_health():
    """gRPC-style Health endpoint."""
    start_time = time.time()
    services = {"python": True}

    for service_key, url in SERVICE_ENDPOINTS.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/health")
                services[service_key] = resp.status_code == 200
        except:
            services[service_key] = False

    return {
        "services": services,
        "timestamp": int(time.time()),
    }


@app.post("/grpc/aggregate")
async def grpc_aggregate(request: Request):
    """gRPC-style Aggregate endpoint."""
    start_time = time.time()
    results = []

    for service_key, url in SERVICE_ENDPOINTS.items():
        svc_start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{url}/api/hello")
                elapsed = int((time.time() - svc_start) * 1000)
                if resp.status_code == 200:
                    data = resp.json()
                    results.append({
                        "service": service_key,
                        "message": data.get("message", ""),
                        "elapsed_ms": elapsed,
                        "success": True,
                    })
                else:
                    results.append({
                        "service": service_key,
                        "message": f"HTTP {resp.status_code}",
                        "elapsed_ms": elapsed,
                        "success": False,
                    })
        except Exception as e:
            results.append({
                "service": service_key,
                "message": str(e),
                "elapsed_ms": 0,
                "success": False,
            })

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "caller": SERVICE_NAME,
        "results": results,
        "total_time_ms": total_time_ms,
    }


# ============================================
# Database CRUD Endpoints
# ============================================

@app.get("/db/records")
async def get_records():
    """Get all benchmark records."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, value, created_at, updated_at FROM benchmark_records ORDER BY id")
        return [{"id": r["id"], "name": r["name"], "description": r["description"], "value": r["value"],
                 "created_at": r["created_at"].isoformat(), "updated_at": r["updated_at"].isoformat()} for r in rows]


@app.get("/db/records/{record_id}")
async def get_record(record_id: int):
    """Get a single benchmark record by ID."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, description, value, created_at, updated_at FROM benchmark_records WHERE id = $1", record_id)
        if not row:
            raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
        return {"id": row["id"], "name": row["name"], "description": row["description"], "value": row["value"],
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}


@app.post("/db/records")
async def create_record(request: Request):
    """Create a new benchmark record."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        body = await request.json()
    except:
        body = {}

    name = body.get("name", "New Record")
    description = body.get("description")
    value = body.get("value", 0)

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO benchmark_records (name, description, value) VALUES ($1, $2, $3) RETURNING id, name, description, value, created_at, updated_at",
            name, description, value
        )
        return {"id": row["id"], "name": row["name"], "description": row["description"], "value": row["value"],
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}


@app.put("/db/records/{record_id}")
async def update_record(record_id: int, request: Request):
    """Update an existing benchmark record."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        body = await request.json()
    except:
        body = {}

    name = body.get("name")
    description = body.get("description")
    value = body.get("value")

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE benchmark_records SET name = COALESCE($1, name), description = COALESCE($2, description), value = COALESCE($3, value), updated_at = CURRENT_TIMESTAMP WHERE id = $4 RETURNING id, name, description, value, created_at, updated_at",
            name, description, value, record_id
        )
        if not row:
            raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
        return {"id": row["id"], "name": row["name"], "description": row["description"], "value": row["value"],
                "created_at": row["created_at"].isoformat(), "updated_at": row["updated_at"].isoformat()}


@app.delete("/db/records/{record_id}")
async def delete_record(record_id: int):
    """Delete a benchmark record."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM benchmark_records WHERE id = $1", record_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
        return {"success": True, "deleted": record_id}


if __name__ == "__main__":
    # Initialize database on startup
    import asyncio
    asyncio.run(init_db())

    port = int(os.getenv("PORT", "3003"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
