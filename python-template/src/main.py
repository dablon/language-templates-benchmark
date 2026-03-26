"""
Python Web Service Template
FastAPI with 3 benchmark endpoints + PostgreSQL CRUD
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import time
import os
import asyncpg

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: initialize database
    await init_db()
    yield
    # Shutdown: close database connections
    if db_pool:
        await db_pool.close()

app = FastAPI(title="Python Template", version="0.1.0", lifespan=lifespan)

# Database connection pool
db_pool = None


async def init_db():
    """Initialize database connection pool."""
    global db_pool
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:
            db_pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            print("PostgreSQL connected successfully")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            db_pool = None
    else:
        print("DATABASE_URL not set, skipping database connection")

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


# Run with: uvicorn src.main:app --host 0.0.0.0 --port 3003
