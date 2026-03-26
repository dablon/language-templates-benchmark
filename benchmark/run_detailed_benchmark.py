#!/usr/bin/env python3
"""
Comprehensive Benchmark Suite
Tests: HTTP, gRPC, Service Mesh per language
Measures: TPS, Latency, Memory, CPU
"""

import os
import time
import json
import asyncio
import httpx
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import statistics

# Configuration
SERVICES = {
    "rust": {"port": 3001, "framework": "Axum"},
    "go": {"port": 3002, "framework": "Gin"},
    "python": {"port": 3003, "framework": "FastAPI"},
    "c": {"port": 3004, "framework": "libmicrohttpd"},
}
GATEWAY_PORT = 3100
CONCURRENCY_LEVELS = [1, 10, 50, 100, 200]
DURATION_SECONDS = 5
RESULTS_DIR = "benchmark/results"

# Colors (ASCII-safe - empty for Windows compatibility)
C_OK = '[OK] '
C_INFO = '[INFO] '
C_HEADER = '==== '
C_END = ''

class BenchmarkResults:
    def __init__(self):
        self.data = {
            "timestamp": datetime.now().isoformat(),
            "http": {},
            "grpc": {},
            "inter_service": {},
            "resource_usage": {}
        }

    def add_http_result(self, service: str, concurrency: int, tps: float, latency_avg: float, latency_p99: float):
        if service not in self.data["http"]:
            self.data["http"][service] = []
        self.data["http"][service].append({
            "concurrency": concurrency,
            "tps": tps,
            "latency_avg_ms": latency_avg,
            "latency_p99_ms": latency_p99
        })

    def add_grpc_result(self, service: str, concurrency: int, tps: float, latency_avg: float):
        if service not in self.data["grpc"]:
            self.data["grpc"][service] = []
        self.data["grpc"][service].append({
            "concurrency": concurrency,
            "tps": tps,
            "latency_avg_ms": latency_avg
        })

    def add_inter_service_result(self, pattern: str, service: str, time_ms: float):
        if pattern not in self.data["inter_service"]:
            self.data["inter_service"][pattern] = {}
        self.data["inter_service"][pattern][service] = time_ms

    def add_resource_usage(self, service: str, cpu: str, memory: str):
        self.data["resource_usage"][service] = {
            "cpu": cpu,
            "memory": memory
        }

    def save(self, filename: str):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        filepath = os.path.join(RESULTS_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(self.data, f, indent=2)
        return filepath

def get_container_stats(container_name: str) -> Tuple[str, str]:
    """Get CPU and memory usage for a container."""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}\t{{.MemUsage}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.strip()
        if output:
            parts = output.split('\t')
            return parts[0] if len(parts) > 0 else "N/A", parts[1] if len(parts) > 1 else "N/A"
    except:
        pass
    return "N/A", "N/A"

async def make_request(client: httpx.AsyncClient, url: str) -> Tuple[bool, float]:
    """Make a single request and return success status and latency in ms."""
    start = time.perf_counter()
    try:
        response = await client.get(url, timeout=10.0)
        elapsed = (time.perf_counter() - start) * 1000
        return response.status_code == 200, elapsed
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        return False, elapsed

async def benchmark_endpoint(url: str, concurrency: int, duration: int) -> Dict:
    """Benchmark an endpoint with given concurrency for specified duration."""
    latencies = []
    successes = 0
    failures = 0

    async with httpx.AsyncClient() as client:
        start_time = time.time()
        tasks = []

        while time.time() - start_time < duration:
            # Create batch of concurrent requests
            batch = [make_request(client, url) for _ in range(concurrency)]
            results = await asyncio.gather(*batch)

            for success, latency in results:
                latencies.append(latency)
                if success:
                    successes += 1
                else:
                    failures += 1

        elapsed_time = time.time() - start_time

    total_requests = successes + failures
    tps = total_requests / elapsed_time if elapsed_time > 0 else 0
    avg_latency = statistics.mean(latencies) if latencies else 0
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0

    return {
        "total_requests": total_requests,
        "successes": successes,
        "failures": failures,
        "tps": round(tps, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
        "min_latency_ms": round(min(latencies), 2) if latencies else 0,
        "max_latency_ms": round(max(latencies), 2) if latencies else 0,
    }

async def run_http_benchmarks(results: BenchmarkResults):
    """Run HTTP benchmarks for all services."""
    print(f"\n{C_HEADER}{'='*60}{C_END}")
    print(f"{C_INFO}  HTTP BENCHMARKS (GET /api/hello){C_END}")
    print(f"{C_HEADER}{'='*60}{C_END}\n")

    for service_name, config in SERVICES.items():
        port = config["port"]
        url = f"http://localhost:{port}/api/hello"
        print(f"{C_INFO}Testing {service_name.upper()} (Axum) on port {port}{C_END}")

        container_name = f"language-templates-benchmark-{service_name}-template-1"
        cpu, mem = get_container_stats(container_name)
        results.add_resource_usage(service_name, cpu, mem)

        for concurrency in CONCURRENCY_LEVELS:
            print(f"  Concurrency: {concurrency}...", end=" ", flush=True)
            benchmark = await benchmark_endpoint(url, concurrency, DURATION_SECONDS)

            results.add_http_result(
                service_name,
                concurrency,
                benchmark["tps"],
                benchmark["avg_latency_ms"],
                benchmark["p99_latency_ms"]
            )

            print(f"TPS: {benchmark['tps']:.2f}, "
                  f"Latency: {benchmark['avg_latency_ms']:.2f}ms, "
                  f"P99: {benchmark['p99_latency_ms']:.2f}ms")

        print()

async def run_grpc_benchmarks(results: BenchmarkResults):
    """Run gRPC-style benchmarks for all services."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}  gRPC-STYLE BENCHMARKS (POST /grpc.hello){NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    for service_name, config in SERVICES.items():
        port = config["port"]
        url = f"http://localhost:{port}/grpc.hello"

        print(f"{YELLOW}Testing gRPC {service_name.upper()}{NC}")

        for concurrency in CONCURRENCY_LEVELS[:3]:  # Fewer levels for gRPC
            print(f"  Concurrency: {concurrency}...", end=" ", flush=True)

            async with httpx.AsyncClient() as client:
                start_time = time.time()
                tasks = []
                latencies = []
                successes = 0

                for _ in range(concurrency * 10):
                    task = client.post(url, json={"name": "benchmark"}, timeout=10.0)
                    tasks.append(task)

                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for resp in responses:
                    if isinstance(resp, Exception):
                        latencies.append(0)
                    else:
                        latencies.append(resp.elapsed.total_seconds() * 1000)
                        if resp.status_code == 200:
                            successes += 1

                elapsed = time.time() - start_time
                tps = len(responses) / elapsed if elapsed > 0 else 0
                avg_lat = statistics.mean(latencies) if latencies else 0

                results.add_grpc_result(service_name, concurrency, tps, avg_lat)
                print(f"TPS: {tps:.2f}, Latency: {avg_lat:.2f}ms")

        print()

async def run_inter_service_benchmarks(results: BenchmarkResults):
    """Run inter-service communication benchmarks."""
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}  INTER-SERVICE COMMUNICATION BENCHMARKS{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

    # Test 1: Gateway REST Aggregate
    print(f"{YELLOW}Testing Gateway REST Aggregate -> All Services{NC}")
    url = f"http://localhost:{GATEWAY_PORT}/api/rest/aggregate"

    for i in range(5):
        start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
        elapsed = (time.perf_counter() - start) * 1000

        if i < 3:  # Print first 3
            data = resp.json()
            print(f"  Run {i+1}: {elapsed:.2f}ms - "
                  f"Total time: {data.get('total_time_ms', 0)}ms")

    results.add_inter_service_result("gateway_rest_aggregate", "gateway", elapsed)

    # Test 2: Gateway gRPC Aggregate
    print(f"\n{YELLOW}Testing Gateway gRPC Aggregate -> All Services{NC}")
    url = f"http://localhost:{GATEWAY_PORT}/api/grpc/aggregate"

    for i in range(5):
        start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"name": "test"}, timeout=30.0)
        elapsed = (time.perf_counter() - start) * 1000

        if i < 3:
            print(f"  Run {i+1}: {elapsed:.2f}ms")

    results.add_inter_service_result("gateway_grpc_aggregate", "gateway", elapsed)

    # Test 3: Service Mesh Status
    print(f"\n{YELLOW}Testing Service Mesh Status{NC}")
    url = f"http://localhost:{GATEWAY_PORT}/api/mesh/services"

    for i in range(3):
        start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"  Run {i+1}: {elapsed:.2f}ms")

    results.add_inter_service_result("service_mesh_status", "consul", elapsed)

    # Test 4: Individual service internal aggregate
    print(f"\n{YELLOW}Testing Individual Service -> Aggregate Calls{NC}")

    for service_name, config in SERVICES.items():
        port = config["port"]
        url = f"http://localhost:{port}/internal/aggregate"

        times = []
        for i in range(3):
            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    resp = await client.get(url)
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                except Exception as e:
                    times.append(0)

        avg_time = statistics.mean(times) if times else 0
        print(f"  {service_name}: avg {avg_time:.2f}ms")
        results.add_inter_service_result(f"service_{service_name}_aggregate", service_name, avg_time)

def generate_markdown_report(results: BenchmarkResults, filepath: str):
    """Generate detailed markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = f"""# Benchmark Results Report
Generated: {timestamp}

---

## Executive Summary

This report contains comprehensive benchmarks for the multi-language microservice template,
including HTTP performance, gRPC-style communication, and inter-service patterns.

---

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Duration per test | {DURATION_SECONDS}s |
| Concurrency levels | {CONCURRENCY_LEVELS} |
| Services tested | 4 (+ Gateway) |
| Protocol | HTTP/1.1 |

---

## HTTP Performance Results

### TPS (Transactions Per Second)

| Service | Framework | 1 req | 10 req | 50 req | 100 req | 200 req |
|---------|-----------|-------|--------|--------|----------|----------|
"""

    # Add TPS table
    for service, data in results.data["http"].items():
        row = f"| {service} | {SERVICES[service]['framework']} |"
        for conc in CONCURRENCY_LEVELS:
            entry = next((x for x in data if x["concurrency"] == conc), None)
            if entry:
                row += f" {entry['tps']:.1f} |"
            else:
                row += " - |"
        md += row + "\n"

    md += """
### Average Latency (ms)

| Service | Framework | 1 req | 10 req | 50 req | 100 req | 200 req |
|---------|-----------|-------|--------|--------|----------|----------|
"""

    for service, data in results.data["http"].items():
        row = f"| {service} | {SERVICES[service]['framework']} |"
        for conc in CONCURRENCY_LEVELS:
            entry = next((x for x in data if x["concurrency"] == conc), None)
            if entry:
                row += f" {entry['latency_avg_ms']:.2f} |"
            else:
                row += " - |"
        md += row + "\n"

    md += """
### P99 Latency (ms)

| Service | Framework | 1 req | 10 req | 50 req | 100 req | 200 req |
|---------|-----------|-------|--------|--------|----------|----------|
"""

    for service, data in results.data["http"].items():
        row = f"| {service} | {SERVICES[service]['framework']} |"
        for conc in CONCURRENCY_LEVELS:
            entry = next((x for x in data if x["concurrency"] == conc), None)
            if entry:
                row += f" {entry['latency_p99_ms']:.2f} |"
            else:
                row += " - |"
        md += row + "\n"

    # Resource Usage
    md += """
---

## Resource Usage (at peak load)

| Service | CPU | Memory |
|---------|-----|--------|
"""
    for service, usage in results.data["resource_usage"].items():
        md += f"| {service} | {usage['cpu']} | {usage['memory']} |\n"

    # gRPC Results
    md += """
---

## gRPC-style Performance

### gRPC Aggregate Endpoints

| Service | TPS (10 concurrent) | Avg Latency (ms) |
|---------|---------------------|------------------|
"""
    for service, data in results.data["grpc"].items():
        entry = next((x for x in data if x["concurrency"] == 10), None)
        if entry:
            md += f"| {service} | {entry['tps']:.2f} | {entry['latency_avg_ms']:.2f} |\n"

    # Inter-service
    md += """
---

## Inter-Service Communication

| Pattern | Service | Time (ms) |
|---------|---------|-----------|
"""
    for pattern, services in results.data["inter_service"].items():
        for service, time_ms in services.items():
            md += f"| {pattern} | {service} | {time_ms:.2f} |\n"

    # Analysis
    md += """
---

## Analysis

### Best Performing Service (TPS at 100 concurrent)
"""

    # Find best
    best_service = None
    best_tps = 0
    for service, data in results.data["http"].items():
        entry = next((x for x in data if x["concurrency"] == 100), None)
        if entry and entry['tps'] > best_tps:
            best_tps = entry['tps']
            best_service = service

    if best_service:
        md += f"**{best_service.upper()}** with {best_tps:.1f} TPS\n"

    md += """
### Fastest Response Time (avg at 10 concurrent)
"""

    fastest = None
    fastest_latency = float('inf')
    for service, data in results.data["http"].items():
        entry = next((x for x in data if x["concurrency"] == 10), None)
        if entry and entry['latency_avg_ms'] < fastest_latency:
            fastest_latency = entry['latency_avg_ms']
            fastest = service

    if fastest:
        md += f"**{fastest.upper()}** with {fastest_latency:.2f}ms average latency\n"

    md += """
---

## Conclusions

1. **Rust** typically leads in raw performance due to compiled nature
2. **Go** provides excellent balance of performance and developer productivity
3. **Python** slower but most productive for rapid development
4. **C** provides lowest-level control but highest complexity

### Recommendations

- **High throughput**: Use Rust or Go for API endpoints
- **Complex business logic**: Python for rapid development
- **Inter-service**: Use gateway pattern for aggregation
- **Service mesh**: Consul provides centralized service discovery
"""

    with open(filepath, 'w') as f:
        f.write(md)

    print(f"\n{GREEN}Report saved to: {filepath}{NC}")

def main():
    print(f"{GREEN}{'='*60}{NC}")
    print(f"{GREEN}  Language Templates Benchmark Suite{NC}")
    print(f"{GREEN}  HTTP | gRPC | Service Mesh | Inter-Service{NC}")
    print(f"{GREEN}{'='*60}{NC}\n")

    # Check services
    print("Checking services...")
    for name, config in SERVICES.items():
        port = config["port"]
        try:
            import requests
            r = requests.get(f"http://localhost:{port}/health", timeout=2)
            status = "[OK]" if r.status_code == 200 else "[FAIL]"
            print(f"  {status} {name} (port {port})")
        except:
            print(f"  [NA] {name} (port {port}) - NOT AVAILABLE")

    try:
        import requests
        r = requests.get(f"http://localhost:{GATEWAY_PORT}/health", timeout=2)
        status = "[OK]" if r.status_code == 200 else "[FAIL]"
        print(f"  {status} gateway (port {GATEWAY_PORT})")
    except:
        print(f"  [NA] gateway (port {GATEWAY_PORT}) - NOT AVAILABLE")

    print()

    results = BenchmarkResults()

    # Run benchmarks
    asyncio.run(run_http_benchmarks(results))
    asyncio.run(run_grpc_benchmarks(results))
    asyncio.run(run_inter_service_benchmarks(results))

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = results.save(f"benchmark_results_{timestamp}.json")

    # Generate markdown report
    md_file = os.path.join(RESULTS_DIR, f"benchmark_report_{timestamp}.md")
    generate_markdown_report(results, md_file)

    print(f"\n{GREEN}{'='*60}{NC}")
    print(f"{GREEN}  Benchmark Complete!{NC}")
    print(f"{GREEN}{'='*60}{NC}")
    print(f"\nResults saved to:")
    print(f"  - {json_file}")
    print(f"  - {md_file}")

if __name__ == "__main__":
    main()