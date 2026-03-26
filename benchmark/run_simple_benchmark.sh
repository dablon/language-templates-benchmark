#!/bin/bash
# Simple Benchmark using curl - works on Windows with Git Bash

RESULTS_DIR="benchmark/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$RESULTS_DIR"

echo "============================================================"
echo "  Language Templates Benchmark Suite"
echo "  HTTP | gRPC | Service Mesh | Inter-Service"
echo "============================================================"
echo ""

# Configuration
DURATION=5
PORTS=(3001 3002 3003 3004 3100)
SERVICES=("rust" "go" "python" "c" "gateway")
FRAMEWORKS=("Axum" "Gin" "FastAPI" "libmicrohttpd" "FastAPI")
CONCURRENCY=(10 50 100 200)

# Check services
echo "Checking services..."
for i in "${!SERVICES[@]}"; do
    port=${PORTS[$i]}
    name=${SERVICES[$i]}
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  [OK] $name (port $port)"
    else
        echo "  [NA] $name (port $port) - NOT AVAILABLE"
    fi
done
echo ""

# ============================================
# HTTP BENCHMARKS
# ============================================
echo "============================================================"
echo "  HTTP BENCHMARKS (GET /api/hello)"
echo "============================================================"

OUTPUT_FILE="$RESULTS_DIR/http_benchmarks_$TIMESTAMP.csv"
echo "service,framework,concurrency,tps,avg_latency_ms,p99_latency_ms" > "$OUTPUT_FILE"

for i in "${!SERVICES[@]}"; do
    name=${SERVICES[$i]}
    framework=${FRAMEWORKS[$i]}
    port=${PORTS[$i]}

    echo "Testing $name ($framework) on port $port..."

    for conc in "${CONCURRENCY[@]}"; do
        # Run multiple requests and measure
        start_time=$(date +%s%N)
        latencies=""
        success=0

        for j in $(seq 1 $((concurrency * 3))); do
            result=$(curl -s -w ",%{http_code},%{time_total}" "http://localhost:$port/api/hello" 2>/dev/null || echo ",000,0")
            http_code=$(echo "$result" | tr ',' '\n' | tail -2 | head -1)
            time_val=$(echo "$result" | tr ',' '\n' | tail -1)

            if [ "$http_code" = "200" ]; then
                success=$((success + 1))
                latencies="$latencies $time_val"
            fi
        done

        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))

        # Calculate TPS
        tps=$(( success * 1000 / duration ))

        # Calculate avg latency
        total_latency=0
        count=0
        for l in $latencies; do
            lat_ms=$(echo "$l * 1000" | bc 2>/dev/null || echo "0")
            total_latency=$(echo "$total_latency + $lat_ms" | bc 2>/dev/null || echo "$total_latency")
            count=$((count + 1))
        done
        avg_latency=$(echo "scale=2; $total_latency / $count" | bc 2>/dev/null || echo "0")

        # P99 (simplified - take max)
        p99_latency=$(echo "$latencies" | tr ' ' '\n' | sort -n | tail -1 | xargs -I {} echo "scale=2; {} * 1000" | bc 2>/dev/null || echo "0")

        echo "  Concurrency $concurrency: TPS=$tps, Latency=${avg_latency}ms, P99=${p99_latency}ms"

        echo "$name,$framework,$concurrency,$tps,$avg_latency,$p99_latency" >> "$OUTPUT_FILE"
    done

    echo ""
done

# ============================================
# gRPC BENCHMARKS
# ============================================
echo "============================================================"
echo "  gRPC-STYLE BENCHMARKS (POST /grpc.hello)"
echo "============================================================"

OUTPUT_FILE="$RESULTS_DIR/grpc_benchmarks_$TIMESTAMP.csv"
echo "service,framework,concurrency,tps,avg_latency_ms" > "$OUTPUT_FILE"

for i in "${!SERVICES[@]}"; do
    name=${SERVICES[$i]}
    framework=${FRAMEWORKS[$i]}
    port=${PORTS[$i]}

    # Skip gateway for gRPC (it uses different endpoint)
    if [ "$name" = "gateway" ]; then
        endpoint="/api/grpc/aggregate"
    else
        endpoint="/grpc.hello"
    fi

    echo "Testing gRPC $name..."

    for conc in 10 50; do
        start_time=$(date +%s%N)
        success=0

        for j in $(seq 1 $((concurrency * 2))); do
            if [ "$name" = "gateway" ]; then
                result=$(curl -s -w ",%{http_code},%{time_total}" -X POST "http://localhost:$port$endpoint" -H "Content-Type: application/json" -d '{"name":"test"}' 2>/dev/null || echo ",000,0")
            else
                result=$(curl -s -w ",%{http_code},%{time_total}" -X POST "http://localhost:$port$endpoint" -H "Content-Type: application/json" -d '{"name":"test"}' 2>/dev/null || echo ",000,0")
            fi
            http_code=$(echo "$result" | tr ',' '\n' | tail -2 | head -1)
            if [ "$http_code" = "200" ]; then
                success=$((success + 1))
            fi
        done

        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))
        tps=$(( success * 1000 / duration ))

        echo "  Concurrency $concurrency: TPS=$tps"

        echo "$name,$framework,$concurrency,$tps,0" >> "$OUTPUT_FILE"
    done

    echo ""
done

# ============================================
# INTER-SERVICE BENCHMARKS
# ============================================
echo "============================================================"
echo "  INTER-SERVICE COMMUNICATION"
echo "============================================================"

OUTPUT_FILE="$RESULTS_DIR/inter_service_$TIMESTAMP.csv"
echo "pattern,service,time_ms" > "$OUTPUT_FILE"

# Gateway REST Aggregate
echo "Testing Gateway REST Aggregate..."
for i in 1 2 3 4 5; do
    start_time=$(date +%s%N)
    result=$(curl -s "http://localhost:3100/api/rest/aggregate")
    end_time=$(date +%s%N)
    time_ms=$(( (end_time - start_time) / 1000000 ))
    echo "  Run $i: ${time_ms}ms"
done
echo "gateway_rest_aggregate,gateway,0" >> "$OUTPUT_FILE"

# Gateway gRPC Aggregate
echo "Testing Gateway gRPC Aggregate..."
for i in 1 2 3 4 5; do
    start_time=$(date +%s%N)
    result=$(curl -s -X POST "http://localhost:3100/api/grpc/aggregate" -H "Content-Type: application/json" -d '{"name":"test"}')
    end_time=$(date +%s%N)
    time_ms=$(( (end_time - start_time) / 1000000 ))
    echo "  Run $i: ${time_ms}ms"
done
echo "gateway_grpc_aggregate,gateway,0" >> "$OUTPUT_FILE"

# Service Mesh Status
echo "Testing Service Mesh Status..."
for i in 1 2 3; do
    start_time=$(date +%s%N)
    result=$(curl -s "http://localhost:3100/api/mesh/services")
    end_time=$(date +%s%N)
    time_ms=$(( (end_time - start_time) / 1000000 ))
    echo "  Run $i: ${time_ms}ms"
done
echo "service_mesh_status,consul,0" >> "$OUTPUT_FILE"

# Individual services calling aggregate
echo "Testing Individual Service Aggregates..."
for i in "${!SERVICES[@]}"; do
    name=${SERVICES[$i]}
    port=${PORTS[$i]}

    if [ "$name" = "gateway" ]; then
        continue
    fi

    times=""
    for j in 1 2 3; do
        start_time=$(date +%s%N)
        result=$(curl -s "http://localhost:$port/internal/aggregate" 2>/dev/null || echo "")
        end_time=$(date +%s%N)
        time_ms=$(( (end_time - start_time) / 1000000 ))
        times="$times $time_ms"
    done

    avg=$(echo $times | tr ' ' '\n' | awk '{sum+=$1; cnt++} END {print sum/cnt}')

    echo "  $name -> aggregate: ${avg}ms (avg)"
    echo "service_aggregate,$name,$avg" >> "$OUTPUT_FILE"
done

echo ""
echo "============================================================"
echo "  COMPLETE!"
echo "============================================================"
echo ""
echo "Results saved to:"
echo "  - $RESULTS_DIR/http_benchmarks_$TIMESTAMP.csv"
echo "  - $RESULTS_DIR/grpc_benchmarks_$TIMESTAMP.csv"
echo "  - $RESULTS_DIR/inter_service_$TIMESTAMP.csv"