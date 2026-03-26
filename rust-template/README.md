# Rust Web Service Template

High-performance web service template built with **Rust** and **Axum** framework. Part of the [Language Templates Benchmark](https://github.com/dablon/language-templates-benchmark) project.

## Features

- 🚀 **High Performance** - Built on Axum and Tokio for maximum throughput
- 📦 **Structured** - Clean architecture with separated concerns
- 🧪 **Tested** - Unit and integration tests included
- 🐳 **Docker Ready** - Multi-stage build with minimal image size
- 📊 **Benchmark Ready** - Consistent API across all language implementations

## Project Structure

```
rust-template/
├── src/
│   ├── main.rs           # Application entry point
│   ├── lib.rs             # Library exports
│   ├── config.rs          # Configuration management
│   ├── constants.rs       # Application constants
│   ├── error.rs           # Error handling
│   ├── routes/
│   │   ├── mod.rs         # Route module
│   │   ├── api.rs         # REST API endpoints
│   │   ├── health.rs      # Health check endpoint
│   │   └── web.rs         # Web HTML endpoints
│   └── models/
│       ├── mod.rs         # Models module
│       └── response.rs     # Response types
├── static/
│   ├── index.html         # Main HTML page
│   ├── css/
│   │   └── styles.css     # Styles
│   └── js/
│       └── app.js          # Client JavaScript
├── tests/
│   └── integration_test.rs # Integration tests
├── .env.example          # Environment variables
├── Cargo.toml             # Rust dependencies
├── Dockerfile            # Multi-stage Docker build
└── README.md
```

## Quick Start

### Local Development

```bash
# Build and run
cargo run

# Run tests
cargo test

# Build release
cargo build --release
```

### Docker

```bash
# Build image
docker build -t rust-template .

# Run container
docker run -p 3001:3001 rust-template
```

### Docker Compose

```bash
docker compose up -d
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | HTML homepage |
| GET | `/health` | Health check (JSON) |
| GET | `/api/hello` | JSON greeting |
| POST | `/api/echo` | Echo request body |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3001` | Server port |
| `LOG_LEVEL` | `info` | Log level (trace, debug, info, warn, error) |
| `APP_NAME` | `rust-template` | Application name |

## Performance

This template is designed for maximum performance:

- **Axum** - Fast, async web framework
- **Tokio** - Efficient async runtime
- **Tower** - Modular middleware stack
- **Minimal allocations** - Zero-copy where possible

See [Benchmark Results](../BENCHMARK_RESULTS.md) for comparative performance data.

## License

MIT
