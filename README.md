# Language Templates Benchmark

Comparative benchmark of web service templates across multiple programming languages.

## Templates

| Language | Framework | Port | Dockerfile |
|----------|-----------|------|------------|
| Rust | Axum | 3001 | ✅ |
| Go | Gin | 3002 | ✅ |
| Python | FastAPI | 3003 | ✅ |
| C | libmicrohttpd | 3004 | ✅ |

## Benchmark Suite

Located in `benchmark/` - uses [ Bombardier ](https://github.com/codesenberg/bombardier) for HTTP benchmarking.

## Quick Start

```bash
# Build and run all services
docker compose up -d

# Run benchmarks
docker compose -f docker-compose.benchmark.yml up
```

## Services

Each template implements:

- `GET /` - HTML homepage
- `GET /health` - Health check (JSON)
- `GET /api/hello` - JSON response
- `POST /api/echo` - Echo back request body

## Results

See [BENCHMARK_RESULTS.md](./BENCHMARK_RESULTS.md) for latest benchmark data.
