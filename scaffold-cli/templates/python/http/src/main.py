"""
Python Web Service Template
FastAPI with 3 benchmark endpoints
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import hashlib
import time

app = FastAPI(title="Python Template", version="0.1.0")

# ============================================
# 1. JSON API - Simple greeting
# ============================================
@app.get("/api/hello")
async def hello():
    return {
        "message": "Hello from Python!",
        "service": "python-template",
        "version": "0.1.0"
    }

# ============================================
# 2. CPU Computation - Fibonacci + Primes
# ============================================
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

@app.get("/api/compute")
async def compute(n: int = 30):
    start = time.time()
    n_capped = min(n, 35)
    fib_result = fibonacci(n_capped)
    primes = [i for i in range(2, min(n * 10, 500)) if is_prime(i)]
    elapsed = (time.time() - start) * 1000
    return {
        "operation": "compute",
        "fibonacci_35": fib_result,
        "primes_found": len(primes),
        "execution_time_ms": round(elapsed, 2),
        "service": "python-template"
    }

# ============================================
# 3. Data Processing - Echo + Transform
# ============================================
@app.post("/api/echo")
async def echo(request: Request):
    body = await request.body()
    text = body.decode("utf-8")
    words = text.split()
    sha = hashlib.sha256(text.encode()).hexdigest()[:16]
    return {
        "original_length": len(text),
        "word_count": len(words),
        "char_count": len(text.replace(" ", "")),
        "uppercase": text.upper(),
        "lowercase": text.lower(),
        "sha256_prefix": sha,
    }

# ============================================
# Health Check
# ============================================
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "python-template", "version": "0.1.0"}

# ============================================
# Static Files
# ============================================
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)))

@app.get("/")
async def index():
    html_path = static_path / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return {"message": "Python Template"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)
