import os
import time
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx

# Consul imports
try:
    import consul
    CONSUL_AVAILABLE = True
except ImportError:
    CONSUL_AVAILABLE = False

app = FastAPI()

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

SERVICE_NAME = "{{PROJECT_NAME}}"
VERSION = "0.1.0"
START_TIME = time.time()

# Service mesh configuration
ENABLE_CONSUL = os.getenv("ENABLE_CONSUL", "false").lower() == "true"
CONSUL_ADDR = os.getenv("CONSUL_ADDR", "localhost:8500")
SERVICE_ID = os.getenv("SERVICE_NAME", SERVICE_NAME)

consul_client = None

if ENABLE_CONSUL and CONSUL_AVAILABLE:
    try:
        consul_client = consul.Consul(host=CONSUL_ADDR.split(":")[0], port=int(CONSUL_ADDR.split(":")[1]))
        # Register service
        port = os.getenv("PORT", "3003")
        consul_client.agent.service.register(
            SERVICE_ID,
            service_id=f"{SERVICE_ID}-{port}",
            port=int(port),
            check=consul.Check.http(f"http://localhost:{port}/health", interval="10s")
        )
        print(f"Service mesh enabled - Consul: {CONSUL_ADDR}")
    except Exception as e:
        print(f"Failed to connect to Consul: {e}")
        consul_client = None

def get_service_endpoint(service_key: str) -> str:
    """Get service endpoint from Consul or use fallback."""
    if consul_client:
        try:
            _, services = consul_client.health.service(service_key)
            if services:
                return f"localhost:{services[0]['ServicePort']}"
        except Exception:
            pass

    # Fallback endpoints
    defaults = {
        "rust": "localhost:3001",
        "go": "localhost:3002",
        "c": "localhost:3004"
    }
    return defaults.get(service_key, f"localhost:3001")

@app.get("/health")
async def health():
    mesh_info = {"enabled": False}
    if consul_client:
        mesh_info = {"enabled": True, "consul_addr": CONSUL_ADDR}

    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "uptime_seconds": time.time() - START_TIME,
        "protocol": "service-mesh",
        "mesh_status": mesh_info
    }

@app.get("/")
async def index():
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(str(static_path))

    mesh_info = "disabled" if not consul_client else f"Consul @ {CONSUL_ADDR}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{SERVICE_NAME}</title>
        <style>
            body {{ font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }}
            h1 {{ color: #4caf50; }}
            .card {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }}
            .mesh {{ color: #ff9800; }}
        </style>
    </head>
    <body>
        <h1>{SERVICE_NAME}</h1>
        <div class="card">
            <p>Version: {VERSION}</p>
            <p>Protocol: <span class="mesh">Service Mesh (HTTP + Consul)</span></p>
            <p>Mesh: {mesh_info}</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/api/hello")
async def hello():
    return {
        "message": f"Hello from {SERVICE_NAME} (Service Mesh)!",
        "service": SERVICE_NAME,
        "version": VERSION,
        "protocol": "service-mesh",
        "mesh": consul_client is not None,
        "timestamp": int(time.time())
    }

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

@app.get("/api/compute")
async def compute(n: int = 30):
    n = min(max(n, 1), 35)

    start = time.time()
    fib = fibonacci(n)
    primes = [i for i in range(2, n*10) if is_prime(i)][:100]
    elapsed = time.time() - start

    return {
        "operation": "compute",
        "fibonacci_input": n,
        "fibonacci_value": fib,
        "primes_count": len(primes),
        "execution_time_ns": int(elapsed * 1e9),
        "service": SERVICE_NAME,
        "protocol": "service-mesh"
    }

@app.post("/api/echo")
async def echo(request: Request):
    body = await request.body()
    text = body.decode("utf-8")

    return {
        "original_length": len(text),
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "service": SERVICE_NAME,
        "protocol": "service-mesh"
    }

if __name__ == "__main__":
    port = os.getenv("PORT", "3003")
    print(f"Starting {SERVICE_NAME} (Service Mesh) on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=int(port))
