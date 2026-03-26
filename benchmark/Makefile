# Benchmark targets
.PHONY: benchmark benchmark-rust benchmark-go benchmark-python benchmark-c clean

# Default target
benchmark: benchmark-rust benchmark-go benchmark-python benchmark-c
	@echo "=== All benchmarks complete ==="

# Individual language benchmarks
benchmark-rust:
	@echo "=== Benchmarking Rust (Axum) ==="
	bombardier -c 100 -d 30s -p results-rust.json http://localhost:3001/api/hello

benchmark-go:
	@echo "=== Benchmarking Go (Gin) ==="
	bombardier -c 100 -d 30s -p results-go.json http://localhost:3002/api/hello

benchmark-python:
	@echo "=== Benchmarking Python (FastAPI) ==="
	bombardier -c 100 -d 30s -p results-python.json http://localhost:3003/api/hello

benchmark-c:
	@echo "=== Benchmarking C (libmicrohttpd) ==="
	bombardier -c 100 -d 30s -p results-c.json http://localhost:3004/api/hello

# Run with different concurrency levels
benchmark-concurrency:
	@for c in 10 50 100 200 500; do \
		echo "=== Concurrency $$c ==="; \
		bombardier -c $$c -d 20s http://localhost:3001/api/hello 2>/dev/null | grep "Requests/sec"; \
		bombardier -c $$c -d 20s http://localhost:3002/api/hello 2>/dev/null | grep "Requests/sec"; \
		bombardier -c $$c -d 20s http://localhost:3003/api/hello 2>/dev/null | grep "Requests/sec"; \
		bombardier -c $$c -d 20s http://localhost:3004/api/hello 2>/dev/null | grep "Requests/sec"; \
	done

clean:
	rm -f results-*.json
