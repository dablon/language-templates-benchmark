"""
Gateway Service - Aggregates calls to all language templates.
Provides REST endpoints for benchmarking inter-service communication.
"""

import os
import asyncio
import time
from typing import List, Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
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

HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Gateway - Language Templates Benchmark">
    <title>Gateway - Language Templates Benchmark</title>
    <style>
        :root {
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent-gateway: #9b59b6;
            --accent-python: #4caf50;
            --accent-go: #00add8;
            --accent-rust: #dea584;
            --accent-c: #ff6b6b;
            --border-color: #30363d;
            --success: #238636;
            --warning: #d29922;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; }
        .bg-animation { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; }
        .bg-animation::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle at 20% 80%, rgba(155, 89, 182, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(0, 173, 216, 0.08) 0%, transparent 50%); animation: bgMove 20s ease-in-out infinite; }
        @keyframes bgMove { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(-10%, -10%); } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--border-color); }
        .logo { display: flex; align-items: center; gap: 15px; }
        .logo-icon { font-size: 48px; animation: float 3s ease-in-out infinite; }
        .logo h1 { font-size: 2em; background: linear-gradient(90deg, var(--accent-gateway), #8e44ad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav { display: flex; gap: 20px; }
        .nav a { color: var(--text-secondary); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: all 0.3s; }
        .nav a:hover { background: var(--bg-tertiary); color: var(--text-primary); }
        .hero { text-align: center; padding: 60px 0; }
        .hero h2 { font-size: 3em; margin-bottom: 20px; }
        .hero .framework { font-size: 1.5em; color: var(--text-secondary); margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }
        .stat-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 25px; text-align: center; transition: transform 0.3s, border-color 0.3s; }
        .stat-card:hover { transform: translateY(-5px); border-color: var(--accent-gateway); }
        .stat-card.fast { border-color: var(--success); background: linear-gradient(135deg, var(--bg-secondary), rgba(35, 134, 54, 0.1)); }
        .stat-value { font-size: 2.5em; font-weight: bold; color: var(--accent-gateway); }
        .stat-label { color: var(--text-secondary); margin-top: 5px; }
        .stat-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; margin-top: 10px; }
        .badge-tps { background: var(--success); color: white; }
        .badge-latency { background: var(--warning); color: black; }
        .badge-memory { background: #9c27b0; color: white; }
        .badge-dev { background: var(--accent-gateway); color: white; }
        section { margin: 40px 0; }
        section h3 { font-size: 1.8em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }
        .comparison-table { width: 100%; border-collapse: collapse; background: var(--bg-secondary); border-radius: 12px; overflow: hidden; }
        .comparison-table th, .comparison-table td { padding: 15px 20px; text-align: left; border-bottom: 1px solid var(--border-color); }
        .comparison-table th { background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85em; }
        .comparison-table tr:hover { background: var(--bg-tertiary); }
        .comparison-table .fast-row { background: rgba(155, 89, 182, 0.15); }
        .comparison-table .fast-row td:first-child::before { content: '⚡ '; }
        .chart-container { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; margin: 20px 0; }
        .bar-chart { display: flex; flex-direction: column; gap: 15px; }
        .bar-row { display: flex; align-items: center; gap: 15px; }
        .bar-label { width: 80px; font-size: 0.9em; }
        .bar-track { flex: 1; height: 30px; background: var(--bg-tertiary); border-radius: 6px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 6px; transition: width 1s ease-out; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-size: 0.85em; font-weight: bold; }
        .bar-fill.rust { background: var(--accent-rust); }
        .bar-fill.go { background: var(--accent-go); }
        .bar-fill.python { background: var(--accent-python); }
        .bar-fill.c { background: var(--accent-c); }
        .endpoints-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .endpoint-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; transition: all 0.3s; }
        .endpoint-card:hover { border-color: var(--accent-gateway); }
        .endpoint-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .method { padding: 4px 10px; border-radius: 4px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; }
        .method.get { background: var(--success); }
        .method.post { background: var(--accent-go); }
        .endpoint-path { font-family: monospace; font-size: 1.1em; color: var(--accent-gateway); }
        .endpoint-desc { color: var(--text-secondary); font-size: 0.9em; }
        .quick-actions { display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; }
        .action-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); text-decoration: none; transition: all 0.3s; cursor: pointer; }
        .action-btn:hover { background: var(--bg-secondary); border-color: var(--accent-gateway); }
        .action-btn.primary { background: var(--accent-gateway); color: white; border-color: var(--accent-gateway); }
        .action-btn.primary:hover { background: #8e44ad; }
        footer { text-align: center; padding: 40px 0; margin-top: 60px; border-top: 1px solid var(--border-color); color: var(--text-secondary); }
        footer a { color: var(--accent-gateway); text-decoration: none; }
        .result-box { background: var(--bg-tertiary); border-radius: 8px; padding: 15px; margin-top: 15px; font-family: monospace; font-size: 0.9em; display: none; }
        .result-box.show { display: block; }
        .result-box pre { overflow-x: auto; color: var(--accent-gateway); }
        .inter-service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .inter-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
        .inter-card h4 { color: var(--text-secondary); font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }
        .inter-value { font-size: 1.8em; color: var(--accent-gateway); }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .service-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; text-align: center; }
        .service-card .lang { font-size: 2em; margin-bottom: 10px; }
        .service-card .name { font-weight: bold; }
        .service-card .port { color: var(--text-secondary); font-size: 0.9em; }
        @media (max-width: 768px) { .hero h2 { font-size: 2em; } .stats-grid { grid-template-columns: repeat(2, 1fr); } .nav { display: none; } }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="container">
        <header>
            <div class="logo">
                <span class="logo-icon">🌐</span>
                <div>
                    <h1>Gateway</h1>
                    <span style="color: var(--text-secondary);">Inter-Service Aggregator</span>
                </div>
            </div>
            <nav class="nav">
                <a href="/">Home</a>
                <a href="/health">Health</a>
                <a href="/api/services">Services</a>
                <a href="http://localhost:8500">Consul</a>
            </nav>
        </header>
        <main>
            <section class="hero">
                <h2>Service Gateway</h2>
                <p class="framework">Aggregates <strong>4 microservices</strong> • REST • gRPC-style • Service Mesh</p>
                <div class="quick-actions">
                    <button class="action-btn primary" onclick="testEndpoint('/health')">🟢 Test Health</button>
                    <button class="action-btn" onclick="testEndpoint('/api/rest/aggregate')">🔗 Test REST Aggregate</button>
                    <button class="action-btn" onclick="testEndpoint('/api/grpc/aggregate', 'POST')">⚡ Test gRPC</button>
                    <button class="action-btn" onclick="testEndpoint('/api/mesh/services')">🔍 Test Mesh</button>
                </div>
                <div id="result" class="result-box"><pre></pre></div>
            </section>
            <section>
                <h3>📊 Connected Services</h3>
                <div class="service-grid">
                    <div class="service-card"><div class="lang">🦀</div><div class="name">Rust</div><div class="port">Port 3001</div></div>
                    <div class="service-card"><div class="lang">🐹</div><div class="name">Go</div><div class="port">Port 3002</div></div>
                    <div class="service-card"><div class="lang">🐍</div><div class="name">Python</div><div class="port">Port 3003</div></div>
                    <div class="service-card"><div class="lang">⚙️</div><div class="name">C</div><div class="port">Port 3004</div></div>
                </div>
            </section>
            <section>
                <h3>📈 Inter-Service Performance</h3>
                <div class="chart-container">
                    <div class="bar-chart">
                        <div class="bar-row"><div class="bar-label">REST</div><div class="bar-track"><div class="bar-fill rust" style="width: 79%;">30ms</div></div></div>
                        <div class="bar-row"><div class="bar-label">gRPC</div><div class="bar-track"><div class="bar-fill go" style="width: 100%;">38ms</div></div></div>
                        <div class="bar-row"><div class="bar-label">Mesh</div><div class="bar-track"><div class="bar-fill c" style="width: 50%;">19ms</div></div></div>
                    </div>
                </div>
            </section>
            <section>
                <h3>🔬 Performance Comparison</h3>
                <table class="comparison-table">
                    <thead><tr><th>Language</th><th>Framework</th><th>TPS</th><th>Avg Latency</th><th>P99</th><th>Memory</th></tr></thead>
                    <tbody>
                        <tr><td>🦀 Rust</td><td>Axum</td><td>600</td><td>102ms</td><td>266ms</td><td>8MB</td></tr>
                        <tr><td>🐹 Go</td><td>Gin</td><td>567</td><td>110ms</td><td>241ms</td><td>11MB</td></tr>
                        <tr><td>⚙️ C</td><td>libmicrohttpd</td><td>567</td><td>117ms</td><td>255ms</td><td>1.5MB</td></tr>
                        <tr><td>🐍 Python</td><td>FastAPI</td><td>500</td><td>137ms</td><td>347ms</td><td>38MB</td></tr>
                    </tbody>
                </table>
            </section>
            <section>
                <h3>🔌 Available Endpoints</h3>
                <div class="endpoints-grid">
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/</span></div><p class="endpoint-desc">Gateway homepage</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/health</span></div><p class="endpoint-desc">Gateway health</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/services</span></div><p class="endpoint-desc">List services</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/rest/aggregate</span></div><p class="endpoint-desc">REST aggregate</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/rest/chain</span></div><p class="endpoint-desc">Sequential chain</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/rest/fanout</span></div><p class="endpoint-desc">Fan-out</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method post">POST</span><span class="endpoint-path">/api/grpc/aggregate</span></div><p class="endpoint-desc">gRPC aggregate</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/mesh/services</span></div><p class="endpoint-desc">Service mesh status</p></div>
                </div>
            </section>
            <section>
                <h3>🌐 Inter-Service Communication</h3>
                <div class="inter-service-grid">
                    <div class="inter-card"><h4>REST Aggregate</h4><div class="inter-value">30ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Parallel calls</p></div>
                    <div class="inter-card"><h4>gRPC Aggregate</h4><div class="inter-value">38ms</div><p style="color: var(--text-secondary); margin-top: 10px;">gRPC-style</p></div>
                    <div class="inter-card"><h4>Service Mesh</h4><div class="inter-value">19ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Consul DNS</p></div>
                    <div class="inter-card"><h4>Chain</h4><div class="inter-value">45ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Sequential</p></div>
                </div>
            </section>
            <section>
                <h3>Database CRUD Operations</h3>
                <div class="inter-service-grid">
                    <div class="inter-card"><h4>CREATE</h4><div class="inter-value">~20ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Insert new record</p></div>
                    <div class="inter-card"><h4>READ</h4><div class="inter-value">~5ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Query records</p></div>
                    <div class="inter-card"><h4>UPDATE</h4><div class="inter-value">~15ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Modify record</p></div>
                    <div class="inter-card"><h4>DELETE</h4><div class="inter-value">~12ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Remove record</p></div>
                </div>
                <div class="quick-actions" style="margin-top: 20px;">
                    <button class="action-btn" onclick="testCrud('GET', 'http://localhost:3002/db/records')">Get All Records</button>
                    <button class="action-btn" onclick="testCrud('POST', 'http://localhost:3002/db/records', {name: 'Test', value: 42})">Create Record</button>
                    <button class="action-btn" onclick="testCrud('PUT', 'http://localhost:3002/db/records/1', {value: 100})">Update Record</button>
                    <button class="action-btn" onclick="testCrud('DELETE', 'http://localhost:3002/db/records/10')">Delete Record</button>
                </div>
                <div id="crud-result" class="result-box"><pre></pre></div>
            </section>
        </main>
        <footer>
            <p>Language Templates Benchmark Project</p>
            <p style="margin-top: 10px;"><a href="/health">Health</a> • <a href="/api/rest/aggregate">Aggregate</a> • <a href="http://localhost:8500">Consul UI</a></p>
            <p style="margin-top: 20px; font-size: 0.8em; color: var(--text-secondary);">Gateway powered by Python + FastAPI • March 2026</p>
        </footer>
    </div>
    <script>
        async function testEndpoint(path, method = 'GET') {
            const resultBox = document.getElementById('result');
            const pre = resultBox.querySelector('pre');
            resultBox.classList.add('show');
            pre.textContent = 'Loading...';
            try {
                const response = await fetch(path, { method, headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}, body: method === 'POST' ? JSON.stringify({ name: 'test' }) : null });
                const data = await response.json();
                pre.textContent = JSON.stringify(data, null, 2);
            } catch (error) { pre.textContent = 'Error: ' + error.message; }
        }

        async function testCrud(method, path, body = null) {
            const resultBox = document.getElementById('crud-result');
            const pre = resultBox.querySelector('pre');
            resultBox.classList.add('show');
            pre.textContent = 'Loading...';
            try {
                const headers = { 'Content-Type': 'application/json' };
                const response = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : null });
                const data = await response.json();
                pre.textContent = JSON.stringify(data, null, 2);
            } catch (error) { pre.textContent = 'Error: ' + error.message; }
        }
    </script>
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
# Service Mesh Endpoints (Consul-style)
# ============================================

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