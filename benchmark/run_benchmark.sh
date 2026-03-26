#!/bin/bash
# ============================================
# Comprehensive Benchmark Suite
# Tests: TPS, Latency, Memory, CPU, Inter-service
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DURATION=10
CONCURRENCY_LEVELS=(1 10 50 100 200)
SERVICES=("rust-template:3001" "go-template:3002" "python-template:3003" "c-template:3004")
GATEWAY="localhost:3100"
RESULTS_DIR="benchmark/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Language Templates Benchmark Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if services are running
check_services() {
    echo -e "${YELLOW}Checking services...${NC}"
    for service in "${SERVICES[@]}"; do
        host="${service%%:*}"
        port="${service##*:}"
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓${NC} $host (port $port)"
        else
            echo -e "  ${RED}✗${NC} $host (port $port) - NOT RUNNING"
        fi
    done

    if curl -s "http://$GATEWAY/health" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} gateway (port 3100)"
    else
        echo -e "  ${RED}✗${NC} gateway - NOT RUNNING"
    fi
    echo ""
}

# Get container stats (CPU/Memory)
get_container_stats() {
    local container=$1
    docker stats --no-stream "$container" 2>/dev/null | tail -1 | awk '{print $3, $4}' || echo "N/A"
}

# Benchmark individual service
benchmark_service() {
    local service_name=$1
    local port=$2
    local endpoint=$3
    local output_file=$4

    echo "Testing $service_name at $endpoint..."

    local results=""
    for concurrency in "${CONCURRENCY_LEVELS[@]}"; do
        # Using wrk or ab if available, otherwise curl loop
        if command -v wrk &> /dev/null; then
            result=$(wrk -t4 -d${DURATION}s -c$concurrency "http://localhost:$port$endpoint" 2>/dev/null | grep -E "Requests/sec|Latency" || echo "0 req/s")
        elif command -v ab &> /dev/null; then
            result=$(ab -n 1000 -c $concurrency "http://localhost:$port$endpoint" 2>/dev/null | grep -E "Requests per second|Time per request" || echo "0 req/s")
        else
            # Fallback: simple curl loop
            local start_time=$(date +%s%N)
            local count=0
            for i in $(seq 1 $((concurrency * 10))); do
                curl -s "http://localhost:$port$endpoint" > /dev/null && count=$((count + 1))
            done
            local end_time=$(date +%s%N)
            local duration=$(( (end_time - start_time) / 1000000 ))
            local rps=$(( count * 1000 / duration ))
            result="Requests/sec: $rps"
        fi

        echo "  Concurrency $concurrency: $result"
        echo "$concurrency:$result" >> "$output_file"
    done
}

# Benchmark with detailed metrics
benchmark_detailed() {
    local service=$1
    local name=$2
    local port=$3
    local endpoint=$4

    echo -e "\n${YELLOW}Benchmarking $name (port $port)${NC}"

    local output_file="$RESULTS_DIR/${name}_detailed.txt"
    > "$output_file"

    echo "Duration: ${DURATION}s | Concurrency levels: ${CONCURRENCY_LEVELS[*]}" | tee "$output_file"
    echo "==============================================" | tee -a "$output_file"

    # Test with different concurrency levels
    for concurrency in "${CONCURRENCY_LEVELS[@]}"; do
        echo "" | tee -a "$output_file"
        echo "--- Concurrency: $concurrency ---" | tee -a "$output_file"

        local start_time=$(date +%s%N)
        local success=0
        local fail=0
        local total_time=0

        # Run requests
        for i in $(seq 1 $concurrency); do
            (
                local req_start=$(date +%s%N)
                local response=$(curl -s -w "%{http_code},%{time_total}" "http://localhost:$port$endpoint" 2>/dev/null || echo "000,0")
                local req_end=$(date +%s%N)
                local req_time=$(( (req_end - req_start) / 1000 ))

                local http_code="${response%%,*}"
                if [ "$http_code" = "200" ]; then
                    echo "success:$req_time" >> /tmp/bench_$$.tmp
                else
                    echo "fail:$req_time" >> /tmp/bench_$$.tmp
                fi
            ) &
        done

        wait

        # Calculate metrics
        local total_requests=$(wc -l < /tmp/bench_$$.tmp 2>/dev/null || echo 0)
        local end_time=$(date +%s%N)
        local duration=$(( (end_time - start_time) / 1000000 ))

        # Get average latency
        if [ -f /tmp/bench_$$.tmp ]; then
            local avg_latency=$(awk -F: '{sum+=$2; count++} END {print (count>0 ? sum/count : 0)}' /tmp/bench_$$.tmp 2>/dev/null || echo 0)
            local p99=$(sort -t: -k2 -n /tmp/bench_$$.tmp | tail -n 1 | cut -d: -f2 2>/dev/null || echo 0)
            rm -f /tmp/bench_$$.tmp
        else
            local avg_latency=0
            local p99=0
        fi

        # TPS
        local tps=$(( total_requests * 1000 / duration ))

        echo "  Requests: $total_requests | Duration: ${duration}ms | TPS: $tps" | tee -a "$output_file"
        echo "  Avg Latency: ${avg_latency}ms | P99: ${p99}ms" | tee -a "$output_file"

        # Memory & CPU
        local container_name="language-templates-benchmark-${service}-1"
        if docker ps | grep -q "$container_name"; then
            local stats=$(get_container_stats "$container_name")
            echo "  Container Stats: $stats" | tee -a "$output_file"
        fi
    done
}

# Inter-service communication benchmark
benchmark_inter_service() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Inter-Service Communication Tests${NC}"
    echo -e "${BLUE}========================================${NC}"

    local output_file="$RESULTS_DIR/inter_service.txt"
    > "$output_file"

    # REST Aggregate (Gateway -> All services)
    echo -e "\n${YELLOW}Testing REST Aggregate (Gateway)${NC}" | tee -a "$output_file"
    for i in {1..5}; do
        start_time=$(date +%s%N)
        response=$(curl -s "http://$GATEWAY/api/rest/aggregate")
        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))
        echo "  Run $i: ${duration}ms" | tee -a "$output_file"
    done

    # gRPC-style Aggregate
    echo -e "\n${YELLOW}Testing gRPC-style Aggregate (Gateway)${NC}" | tee -a "$output_file"
    for i in {1..5}; do
        start_time=$(date +%s%N)
        response=$(curl -s -X POST "http://$GATEWAY/api/grpc/aggregate" -H "Content-Type: application/json" -d '{"name":"test"}')
        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))
        echo "  Run $i: ${duration}ms" | tee -a "$output_file"
    done

    # Chain test
    echo -e "\n${YELLOW}Testing Chain Communication${NC}" | tee -a "$output_file"
    for service in "${SERVICES[@]}"; do
        name="${service%%:*}"
        port="${service##*:}"
        start_time=$(date +%s%N)
        response=$(curl -s "http://localhost:$port/internal/aggregate")
        end_time=$(date +%s%N)
        duration=$(( (end_time - start_time) / 1000000 ))
        echo "  $name -> aggregate: ${duration}ms" | tee -a "$output_file"
    done
}

# Generate summary report
generate_report() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  Generating Summary Report${NC}"
    echo -e "${BLUE}========================================${NC}"

    local report_file="$RESULTS_DIR/benchmark_report_$TIMESTAMP.md"

    cat > "$report_file" << 'EOF'
# Benchmark Results Report

## Test Configuration
- Duration per test: DURATION seconds
- Concurrency levels: CONCURRENCY_LEVELS
- Test date: TIMESTAMP

## Services Tested
| Service | Port | Framework |
|---------|------|-----------|
| Rust | 3001 | Axum |
| Go | 3002 | Gin |
| Python | 3003 | FastAPI |
| C | 3004 | libmicrohttpd |
| Gateway | 3100 | FastAPI |

## Individual Service Performance

### REST Endpoints (/api/hello)

### Inter-Service Communication

### Resource Usage

## Methodology
1. Each service tested at multiple concurrency levels (1, 10, 50, 100, 200)
2. Metrics collected: TPS, latency (avg, p99), memory, CPU
3. Inter-service tests measure aggregation and chain patterns
4. All tests run via Docker containers for consistent environment

## Conclusion
EOF

    # Add TPS comparison
    echo "### TPS Comparison (at 100 concurrent requests)" >> "$report_file"
    echo "" >> "$report_file"
    echo "| Service | TPS | Avg Latency |" >> "$report_file"
    echo "|---------|-----|-------------|" >> "$report_file"

    for service in "${SERVICES[@]}"; do
        name="${service%%:*}"
        port="${service##*:}"
        echo "| $name | TODO | TODO |" >> "$report_file"
    done

    echo "" >> "$report_file"
    echo "Report saved to: $report_file"

    # Also generate CSV
    local csv_file="$RESULTS_DIR/benchmark_data_$TIMESTAMP.csv"
    echo "service,endpoint,tps,avg_latency_ms,p99_latency_ms,cpu_percent,memory_mb" > "$csv_file"

    echo -e "\n${GREEN}Report saved to: $report_file${NC}"
    echo -e "${GREEN}CSV data saved to: $csv_file${NC}"
}

# Run benchmarks
echo -e "${GREEN}Starting benchmark suite...${NC}"
check_services
benchmark_inter_service
generate_report

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Benchmark Complete!${NC}"
echo -e "${GREEN}========================================${NC}"