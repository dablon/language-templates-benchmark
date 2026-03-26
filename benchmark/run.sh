#!/bin/bash
# Benchmark runner script

set -e

RESULTS_DIR="results"
mkdir -p $RESULTS_DIR

echo "========================================"
echo "Language Templates Benchmark Suite"
echo "========================================"
echo ""

LANGUAGES=(
    "rust:Rust (Axum):3001"
    "go:Go (Gin):3002"
    "python:Python (FastAPI):3003"
    "c:C (libmicrohttpd):3004"
)

for lang in "${LANGUAGES[@]}"; do
    IFS=':' read -r id name port <<< "$lang"
    echo ""
    echo "========================================"
    echo "Benchmarking: $name"
    echo "========================================"

    if curl -sf "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "Service is UP on port $port"

        # Run bombardier benchmark
        bombardier -c 100 -d 30s -f $RESULTS_DIR/results-$id.json http://localhost:$port/api/hello 2>&1 | tee $RESULTS_DIR/output-$id.txt

        # Latency test with different concurrency
        echo ""
        echo "Latency test (p50, p95, p99) at concurrency 10:"
        bombardier -c 10 -d 15s http://localhost:$port/api/hello 2>&1 | grep -E "Latency|Percentiles"

        echo ""
        echo "Latency test (p50, p95, p99) at concurrency 100:"
        bombardier -c 100 -d 15s http://localhost:$port/api/hello 2>&1 | grep -E "Latency|Percentiles"
    else
        echo "Service is DOWN on port $port - SKIPPING"
    fi
done

echo ""
echo "========================================"
echo "Benchmark Complete!"
echo "Results saved in $RESULTS_DIR/"
echo "========================================"
