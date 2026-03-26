"""
Gateway Service - Aggregates calls to all language templates.
Provides REST endpoints for benchmarking inter-service communication.
"""

import os
import asyncio
import time
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI(title="Gateway - Inter-Service Aggregator")

# Service endpoints configuration
SERVICES = {
    "rust": {
        "name": "rust-template",
        "rest_url": os.getenv("RUST_URL", "http://rust-template:3001"),
        "health_endpoint": "/health",
        "api_endpoint": "/api/hello",
    },
    "go": {
        "name": "go-template",
        "rest_url": os.getenv("GO_URL", "http://go-template:3002"),
        "health_endpoint": "/health",
        "api_endpoint": "/api/hello",
    },
    "python": {
        "name": "python-template",
        "rest_url": os.getenv("PYTHON_URL", "http://python-template:3003"),
        "health_endpoint": "/health",
        "api_endpoint": "/api/hello",
    },
    "c": {
        "name": "c-template",
        "rest_url": os.getenv("C_URL", "http://c-template:3004"),
        "health_endpoint": "/health",
        "api_endpoint": "/api/hello",
    },
}

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gateway - Inter-Service Aggregator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #ff6b6b; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }
        code { background: #0f3460; padding: 2px 6px; border-radius: 4px; }
        a { color: #ff6b6b; }
        .endpoint { margin: 10px 0; padding: 10px; background: #0f3460; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>Gateway - Inter-Service Aggregator</h1>
    <div class="card">
        <h2>Available Endpoints</h2>
        <div class="endpoint">
            <code>GET /</code> - This page
        </div>
        <div class="endpoint">
            <code>GET /health</code> - Gateway health check
        </div>
        <div class="endpoint">
            <code>GET /api/services</code> - List all registered services
        </div>
        <div class="endpoint">
            <code>GET /api/rest/aggregate</code> - Call all services via REST (parallel)
        </div>
        <div class="endpoint">
            <code>GET /api/rest/chain</code> - Call services sequentially
        </div>
        <div class="endpoint">
            <code>GET /api/rest/fanout</code> - Fan-out to all services
        </div>
    </div>
    <div class="card">
        <h2>Services</h2>
        <ul>
            <li>Rust (Axum) - Port 3001</li>
            <li>Go (Gin) - Port 3002</li>
            <li>Python (FastAPI) - Port 3003</li>
            <li>C (libmicrohttpd) - Port 3004</li>
        </ul>
    </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the gateway homepage."""
    return HTMLContent


@app.get("/health")
async def health():
    """Gateway health check."""
    return {"status": "healthy", "service": "gateway", "version": "1.0.0"}


@app.get("/api/services")
async def list_services():
    """List all registered services."""
    return {"services": list(SERVICES.keys())}


async def call_service(client: httpx.AsyncClient, service_key: str, endpoint: str) -> Dict[str, Any]:
    """Make an HTTP call to a service and return result with timing."""
    service = SERVICES[service_key]
    url = service["rest_url"] + endpoint
    start_time = time.time()

    try:
        response = await client.get(url, timeout=5.0)
        elapsed_ms = int((time.time() - start_time) * 1000)

        return {
            "service": service["name"],
            "status_code": response.status_code,
            "data": response.json() if response.status_code == 200 else None,
            "elapsed_ms": elapsed_ms,
            "success": response.status_code == 200,
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {
            "service": service["name"],
            "status_code": 0,
            "error": str(e),
            "elapsed_ms": elapsed_ms,
            "success": False,
        }


@app.get("/api/rest/aggregate")
async def aggregate_rest():
    """Call all services in parallel via REST and aggregate responses."""
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        tasks = [call_service(client, key, SERVICES[key]["api_endpoint"]) for key in SERVICES]
        results = await asyncio.gather(*tasks)

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "method": "aggregate",
        "protocol": "rest",
        "results": results,
        "total_time_ms": total_time_ms,
    }


@app.get("/api/rest/chain")
async def chain_rest():
    """Call services sequentially (chain pattern)."""
    start_time = time.time()
    results = []

    async with httpx.AsyncClient() as client:
        for key in SERVICES:
            result = await call_service(client, key, SERVICES[key]["api_endpoint"])
            results.append(result)
            # Chain: pass result from previous service to next
            # (simulated by just collecting results)

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "method": "chain",
        "protocol": "rest",
        "results": results,
        "total_time_ms": total_time_ms,
    }


@app.get("/api/rest/fanout")
async def fanout_rest():
    """Fan-out: broadcast to all services simultaneously."""
    return await aggregate_rest()  # Same as aggregate in HTTP


@app.get("/api/health/all")
async def health_all():
    """Check health of all services."""
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        tasks = [call_service(client, key, SERVICES[key]["health_endpoint"]) for key in SERVICES]
        results = await asyncio.gather(*tasks)

    total_time_ms = int((time.time() - start_time) * 1000)

    health_status = {}
    for result in results:
        health_status[result["service"]] = result.get("data", {}).get("status", "unknown")

    return {
        "services": health_status,
        "total_time_ms": total_time_ms,
    }


# ============================================
# gRPC-style Endpoints (JSON over HTTP)
# ============================================

@app.post("/api/grpc/hello")
async def grpc_hello(request: Request):
    """gRPC-style Hello - calls all services."""
    try:
        body = await request.json()
        name = body.get("name", "world")
    except:
        name = "world"

    start_time = time.time()
    results = []

    async with httpx.AsyncClient() as client:
        for key in SERVICES:
            svc_start = time.time()
            service = SERVICES[key]
            url = service["rest_url"] + "/grpc/hello"

            try:
                response = await client.post(url, json={"name": name}, timeout=5.0)
                elapsed_ms = int((time.time() - svc_start) * 1000)
                if response.status_code == 200:
                    data = response.json()
                    msg = data.get("message", "")
                    results.append(f"{key}: {msg} ({elapsed_ms}ms)")
            except Exception as e:
                results.append(f"{key}: error - {e}")

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "method": "grpc/hello",
        "protocol": "grpc",
        "name": name,
        "results": results,
        "total_time_ms": total_time_ms,
    }


@app.get("/api/grpc/health")
async def grpc_health():
    """gRPC-style Health - checks all services."""
    start_time = time.time()

    async with httpx.AsyncClient() as client:
        tasks = []
        for key in SERVICES:
            service = SERVICES[key]
            url = service["rest_url"] + "/grpc/health"
            tasks.append(client.get(url, timeout=5.0))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

    services = {"gateway": True}
    for i, key in enumerate(SERVICES):
        if isinstance(responses[i], Exception):
            services[key] = False
        elif responses[i].status_code == 200:
            data = responses[i].json()
            services[key] = data.get("services", {}).get(key, False)
        else:
            services[key] = False

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "method": "grpc/health",
        "protocol": "grpc",
        "services": services,
        "total_time_ms": total_time_ms,
    }


@app.post("/api/grpc/aggregate")
async def grpc_aggregate(request: Request):
    """gRPC-style Aggregate - calls all services in parallel."""
    try:
        body = await request.json()
        name = body.get("name", "world")
    except:
        name = "world"

    start_time = time.time()
    results = []

    async with httpx.AsyncClient() as client:
        for key in SERVICES:
            svc_start = time.time()
            service = SERVICES[key]
            url = service["rest_url"] + "/grpc/aggregate"

            try:
                response = await client.post(url, json={"name": name}, timeout=5.0)
                elapsed_ms = int((time.time() - svc_start) * 1000)
                if response.status_code == 200:
                    data = response.json()
                    for r in data.get("results", []):
                        results.append({
                            "service": r.get("service", key),
                            "message": r.get("message", ""),
                            "elapsed_ms": r.get("elapsed_ms", elapsed_ms),
                            "success": r.get("success", False),
                        })
            except Exception as e:
                results.append({
                    "service": key,
                    "message": str(e),
                    "elapsed_ms": 0,
                    "success": False,
                })

    total_time_ms = int((time.time() - start_time) * 1000)

    return {
        "method": "grpc/aggregate",
        "protocol": "grpc",
        "caller": "gateway",
        "results": results,
        "total_time_ms": total_time_ms,
    }


# ============================================
// Service Mesh Endpoints (Consul-style)
// ============================================

@app.get("/api/mesh/services")
async def mesh_services():
    """List all services in the mesh (simulated)."""
    return {
        "services": [
            {"name": "gateway", "port": 3100, "status": "healthy"},
            {"name": "rust-template", "port": 3001, "status": "healthy"},
            {"name": "go-template", "port": 3002, "status": "healthy"},
            {"name": "python-template", "port": 3003, "status": "healthy"},
            {"name": "c-template", "port": 3004, "status": "healthy"},
        ],
        "consul": {"address": "consul:8500", "datacenter": "dc1"},
    }


@app.get("/api/mesh/health")
async def mesh_health():
    """Health check from service mesh perspective."""
    return {
        "checks": [
            {"service": "gateway", "status": "passing"},
            {"service": "rust-template", "status": "passing"},
            {"service": "go-template", "status": "passing"},
            {"service": "python-template", "status": "passing"},
            {"service": "c-template", "status": "passing"},
        ],
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "3100"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")