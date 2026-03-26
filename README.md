# Language Templates Benchmark

Comparative benchmark of web service templates across multiple programming languages.

## Overview

This project provides production-ready web service templates in different programming languages, all implementing the same API surface for fair performance comparison.

## Scaffold CLI

Quickly generate new projects with the **scaffold-cli** tool:

```bash
# Build the CLI
cd scaffold-cli
cargo build --release

# Run with interactive prompts (append .exe on Windows)
./target/release/scaffold-cli

# Or use CLI flags
./target/release/scaffold-cli -n myproject -l go -p grpc -d postgres
```

Every push to `master` now triggers the `Build and release scaffold-cli` workflow, which validates the CLI, builds release archives for Linux, macOS (Intel and Apple Silicon), and Windows, and publishes a GitHub release tagged as `v0.0.<UTC timestamp>`.

### CLI Options

| Flag | Short | Description | Values |
|------|-------|-------------|--------|
| `--name` | `-n` | Project name | string (required) |
| `--language` | `-l` | Programming language | `go`, `python`, `rust`, `c` |
| `--protocol` | `-p` | Protocol type | `http`, `grpc`, `service-mesh` |
| `--database` | `-d` | Database options | `none`, `postgres`, `postgres-redis` |
| `--output` | `-o` | Output directory | path |

### Examples

```bash
# HTTP only, no database (fastest startup)
./scaffold-cli -n my-api -l go -p http -d none

# gRPC with PostgreSQL
./scaffold-cli -n my-service -l rust -p grpc -d postgres

# Full service mesh with PostgreSQL + Redis
./scaffold-cli -n my-mesh -l python -p service-mesh -d postgres-redis
```

### Generated Project Features

The CLI generates projects with runtime feature flags:

- `ENABLE_GRPC=true/false` - enables gRPC endpoints
- `ENABLE_DATABASE=true/false` - enables PostgreSQL connection and CRUD routes
- `ENABLE_CONSUL=true/false` - enables Consul service mesh registration

The generated `docker-compose.yml` automatically configures the appropriate services (PostgreSQL, Redis, Consul) based on your selection.

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

Option 1: Use the **scaffold-cli** to generate a base project, then customize:

```bash
# Generate a base template
./scaffold-cli/target/release/scaffold-cli -n my-template -l <language> -p http -d none

# Then add your custom code and features
```

Option 2: Create manually:

1. Create a new directory for your language (e.g., `java-template/`)
2. Follow the standard project structure
3. Implement all API endpoints
4. Add Dockerfile with multi-stage build
5. Update `docker-compose.yml` with your service
6. Add template to `scaffold-cli/templates/` for CLI support
7. Submit a pull request

## Contributing

Contributions welcome! Please ensure:

- Follow the standard project structure
- All endpoints match the API specification
- Include tests
- Update benchmark suite if adding new metrics

## License

MIT
