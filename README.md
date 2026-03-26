# Language Templates Benchmark

Comparative benchmark of web service templates across multiple programming languages.

## Overview

This project provides production-ready web service templates in different programming languages, all implementing the same API surface for fair performance comparison.

## Templates

| Language | Framework | Port | Status |
|----------|-----------|------|--------|
| [Rust/Axum](rust-template/) | Axum | 3001 | ✅ |
| [Go/Gin](go-template/) | Gin | 3002 | ✅ |
| [Python/FastAPI](python-template/) | FastAPI | 3003 | ✅ |
| [C/libmicrohttpd](c-template/) | libmicrohttpd | 3004 | ✅ |

## Project Structure

Each template follows a consistent, production-ready structure:

```
template/
├── src/                      # Source code
│   ├── main.rs               # Entry point
│   ├── lib.rs                # Library exports
│   ├── config.rs             # Configuration
│   ├── constants.rs          # Constants
│   ├── error.rs              # Error handling
│   ├── routes/               # Route handlers
│   │   ├── mod.rs
│   │   ├── api.rs
│   │   ├── health.rs
│   │   └── web.rs
│   └── models/               # Data models
│       ├── mod.rs
│       └── response.rs
├── static/                   # Static files
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── app.js
├── tests/                    # Tests
├── .env.example              # Environment variables
├── Dockerfile                # Multi-stage build
├── docker-compose.yml
├── Cargo.toml / go.mod / etc.
└── README.md
```

## Quick Start

### Build All Services

```bash
# Build and run all services
docker compose up -d

# View logs
docker compose logs -f
```

### Run Benchmarks

```bash
# Start benchmark suite
docker compose -f docker-compose.benchmark.yml up
```

## API Specification

All templates implement the same endpoints:

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/` | HTML homepage | HTML |
| GET | `/health` | Health check | JSON |
| GET | `/api/hello` | JSON greeting | JSON |
| POST | `/api/echo` | Echo body | Raw |

### Example Responses

**GET /health**
```json
{
  "status": "healthy",
  "service": "rust-template",
  "version": "0.1.0"
}
```

**GET /api/hello**
```json
{
  "message": "Hello from Rust!",
  "service": "rust-template",
  "version": "0.1.0"
}
```

## Template Features

Each template includes:

- ✅ Structured project layout (separate routes, models, config)
- ✅ Static file serving (HTML, CSS, JS)
- ✅ Health check endpoint
- ✅ REST API with JSON responses
- ✅ POST endpoint with request body handling
- ✅ Error handling middleware
- ✅ Configuration via environment variables
- ✅ Docker multi-stage build
- ✅ Unit and integration tests
- ✅ Non-root Docker user
- ✅ Health checks

## Benchmark Suite

Located in `benchmark/` - uses [Bombardier](https://github.com/codesenberg/bombardier) for HTTP benchmarking.

### Running Benchmarks

```bash
# Run all benchmarks
cd benchmark
./run.sh

# Or use Makefile
make benchmark
```

## Results

See [BENCHMARK_RESULTS.md](./BENCHMARK_RESULTS.md) for latest benchmark data.

## Adding a New Template

1. Create a new directory for your language (e.g., `java-template/`)
2. Follow the standard project structure
3. Implement all API endpoints
4. Add Dockerfile with multi-stage build
5. Update `docker-compose.yml` with your service
6. Submit a pull request

## Contributing

Contributions welcome! Please ensure:

- Follow the standard project structure
- All endpoints match the API specification
- Include tests
- Update benchmark suite if adding new metrics

## License

MIT
