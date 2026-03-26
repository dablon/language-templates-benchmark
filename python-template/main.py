import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

SERVICE_NAME = "python-template"
VERSION = "0.1.0"

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", "3003"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
