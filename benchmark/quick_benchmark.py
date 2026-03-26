#!/usr/bin/env python3
"""
Quick Benchmark - Simple and reliable
Tests each service with concurrent requests
"""

import time
import json
import subprocess
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

RESULTS_DIR = "benchmark/results"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

SERVICES = [
    ("rust", 3001, "Axum"),
    ("go", 3002, "Gin"),
    ("python", 3003, "FastAPI"),
    ("c", 3004, "libmicrohttpd"),
]

CONCURRENCY = [10, 50, 100]

def make_request(url):
    """Make a single request and return (success, latency_ms)"""
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            _ = response.read()
            elapsed = (time.perf_counter() - start) * 1000
            return (True, elapsed)
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return (False, elapsed)

def benchmark(url, concurrency, duration_seconds=3):
    """Run benchmark with given concurrency"""
    latencies = []
    successes = 0
    failures = 0

    end_time = time.time() + duration_seconds

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []

        while time.time() < end_time:
            # Submit batch of requests
            for _ in range(concurrency):
                futures.append(executor.submit(make_request, url))

            # Collect results
            for future in as_completed(futures):
                success, latency = future.result()
                latencies.append(latency)
                if success:
                    successes += 1
                else:
                    failures += 1
            futures.clear()

    total = successes + failures
    tps = total / duration_seconds if duration_seconds > 0 else 0
    avg_lat = sum(latencies) / len(latencies) if latencies else 0
    latencies_sorted = sorted(latencies)
    p99_idx = int(len(latencies_sorted) * 0.99)
    p99_lat = latencies_sorted[p99_idx] if latencies_sorted else 0

    return {
        "requests": total,
        "successes": successes,
        "failures": failures,
        "tps": round(tps, 2),
        "avg_latency_ms": round(avg_lat, 2),
        "p99_latency_ms": round(p99_lat, 2),
    }

def get_container_stats(container_name):
    """Get container CPU and memory"""
    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}", container_name],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.strip()
        if output:
            parts = output.split('|')
            return parts[0] if len(parts) > 0 else "N/A", parts[1] if len(parts) > 1 else "N/A"
    except:
        pass
    return "N/A", "N/A"

def main():
    print("=" * 60)
    print("  Language Templates Benchmark Suite")
    print("  HTTP | gRPC | Service Mesh | Inter-Service")
    print("=" * 60)
    print()

    # Check services
    print("Checking services...")
    for name, port, framework in SERVICES:
        try:
            req = urllib.request.Request(f"http://localhost:{port}/health")
            with urllib.request.urlopen(req, timeout=2) as resp:
                print(f"  [OK] {name} (port {port})")
        except:
            print(f"  [NA] {port} - NOT AVAILABLE")

    try:
        req = urllib.request.Request("http://localhost:3100/health")
        with urllib.request.urlopen(req, timeout=2) as resp:
            print(f"  [OK] gateway (port 3100)")
    except:
        print(f"  [NA] gateway - NOT AVAILABLE")

    print()

    # HTTP Benchmarks
    print("=" * 60)
    print("  HTTP BENCHMARKS (GET /api/hello)")
    print("=" * 60)

    results = {"http": {}, "grpc": {}, "inter_service": {}, "resources": {}}

    for name, port, framework in SERVICES:
        print(f"\nTesting {name.upper()} ({framework}) on port {port}...")

        # Get container stats
        cpu, mem = get_container_stats(f"language-templates-benchmark-{name}-template-1")
        results["resources"][name] = {"cpu": cpu, "memory": mem}
        print(f"  Resource: CPU={cpu}, Memory={mem}")

        results["http"][name] = {}

        for conc in CONCURRENCY:
            print(f"  Testing concurrency {conc}...", end=" ", flush=True)

            test_url = f"http://localhost:{port}/api/hello"
            result = benchmark(test_url, conc, duration_seconds=3)

            results["http"][name][conc] = result

            print(f"TPS={result['tps']}, Latency={result['avg_latency_ms']}ms, P99={result['p99_latency_ms']}ms")

    # gRPC Benchmarks
    print("\n" + "=" * 60)
    print("  gRPC-STYLE BENCHMARKS")
    print("=" * 60)

    for name, port, framework in SERVICES:
        print(f"\nTesting gRPC {name.upper()}...")

        results["grpc"][name] = {}

        # Test with lower concurrency for gRPC
        for conc in [10, 50]:
            print(f"  Concurrency {conc}...", end=" ", flush=True)

            if name == "gateway":
                url = f"http://localhost:{port}/api/grpc/aggregate"
                data = b'{"name":"test"}'
            else:
                url = f"http://localhost:{port}/grpc.hello"
                data = b'{"name":"test"}'

            def make_post_request(url, data):
                start = time.perf_counter()
                try:
                    req = urllib.request.Request(url, data=data, method='POST')
                    req.add_header('Content-Type', 'application/json')
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        _ = resp.read()
                        elapsed = (time.perf_counter() - start) * 1000
                        return (True, elapsed)
                except Exception as e:
                    elapsed = (time.perf_counter() - start) * 1000
                    return (False, elapsed)

            latencies = []
            successes = 0
            end_time = time.time() + 3

            with ThreadPoolExecutor(max_workers=conc) as executor:
                futures = []
                while time.time() < end_time:
                    for _ in range(conc):
                        futures.append(executor.submit(make_post_request, url, data))

                    for future in as_completed(futures):
                        success, latency = future.result()
                        latencies.append(latency)
                        if success:
                            successes += 1
                    futures.clear()

            total = len(latencies)
            tps = total / 3 if 3 > 0 else 0
            avg_lat = sum(latencies) / len(latencies) if latencies else 0

            results["grpc"][name][conc] = {"tps": round(tps, 2), "avg_latency_ms": round(avg_lat, 2)}

            print(f"TPS={tps:.2f}, Latency={avg_lat:.2f}ms")

    # Inter-Service Benchmarks
    print("\n" + "=" * 60)
    print("  INTER-SERVICE COMMUNICATION")
    print("=" * 60)

    print("\nGateway REST Aggregate...")
    times = []
    for _ in range(5):
        start = time.perf_counter()
        try:
            req = urllib.request.Request("http://localhost:3100/api/rest/aggregate")
            with urllib.request.urlopen(req, timeout=30) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
        except:
            pass
    avg_time = sum(times) / len(times) if times else 0
    results["inter_service"]["gateway_rest_aggregate"] = round(avg_time, 2)
    print(f"  Average time: {avg_time:.2f}ms")

    print("\nGateway gRPC Aggregate...")
    times = []
    for _ in range(5):
        start = time.perf_counter()
        try:
            req = urllib.request.Request("http://localhost:3100/api/grpc/aggregate", data=b'{"name":"test"}')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=30) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
        except:
            pass
    avg_time = sum(times) / len(times) if times else 0
    results["inter_service"]["gateway_grpc_aggregate"] = round(avg_time, 2)
    print(f"  Average time: {avg_time:.2f}ms")

    print("\nService Mesh Status...")
    times = []
    for _ in range(3):
        start = time.perf_counter()
        try:
            req = urllib.request.Request("http://localhost:3100/api/mesh/services")
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
        except:
            pass
    avg_time = sum(times) / len(times) if times else 0
    results["inter_service"]["service_mesh_status"] = round(avg_time, 2)
    print(f"  Average time: {avg_time:.2f}ms")

    # Individual service aggregates
    for name, port, framework in SERVICES:
        if name == "gateway":
            continue
        times = []
        for _ in range(3):
            start = time.perf_counter()
            try:
                req = urllib.request.Request(f"http://localhost:{port}/internal/aggregate")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    _ = resp.read()
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
            except:
                pass
        avg_time = sum(times) / len(times) if times else 0
        results["inter_service"][f"service_{name}_aggregate"] = round(avg_time, 2)
        print(f"  {name} -> aggregate: {avg_time:.2f}ms")

    # ============================================
    # Database CRUD Benchmarks
    # ============================================
    print("\n" + "=" * 60)
    print("  DATABASE CRUD BENCHMARKS")
    print("=" * 60)

    results["database"] = {}

    # Test: Create record
    print("\nTesting CREATE...")
    create_times = []
    for _ in range(5):
        start = time.perf_counter()
        try:
            data = json.dumps({"name": "Benchmark Record", "description": "CRUD test", "value": 100}).encode('utf-8')
            req = urllib.request.Request(f"http://localhost:3002/db/records", data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                create_times.append(elapsed)
        except Exception as e:
            print(f"  CREATE error: {e}")
    avg_create = sum(create_times) / len(create_times) if create_times else 0
    results["database"]["create"] = round(avg_create, 2)
    print(f"  Average: {avg_create:.2f}ms")

    # Test: Read records
    print("\nTesting READ...")
    read_times = []
    for _ in range(10):
        start = time.perf_counter()
        try:
            req = urllib.request.Request(f"http://localhost:3002/db/records")
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                read_times.append(elapsed)
        except Exception as e:
            print(f"  READ error: {e}")
    avg_read = sum(read_times) / len(read_times) if read_times else 0
    results["database"]["read"] = round(avg_read, 2)
    print(f"  Average: {avg_read:.2f}ms")

    # Test: Update record
    print("\nTesting UPDATE...")
    update_times = []
    for _ in range(5):
        start = time.perf_counter()
        try:
            data = json.dumps({"value": 999}).encode('utf-8')
            req = urllib.request.Request(f"http://localhost:3002/db/records/1", data=data, method='PUT')
            req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                update_times.append(elapsed)
        except Exception as e:
            print(f"  UPDATE error: {e}")
    avg_update = sum(update_times) / len(update_times) if update_times else 0
    results["database"]["update"] = round(avg_update, 2)
    print(f"  Average: {avg_update:.2f}ms")

    # Test: Delete record
    print("\nTesting DELETE...")
    delete_times = []
    for _ in range(5):
        start = time.perf_counter()
        try:
            req = urllib.request.Request(f"http://localhost:3002/db/records/5", method='DELETE')
            with urllib.request.urlopen(req, timeout=10) as resp:
                _ = resp.read()
                elapsed = (time.perf_counter() - start) * 1000
                delete_times.append(elapsed)
        except Exception as e:
            print(f"  DELETE error: {e}")
    avg_delete = sum(delete_times) / len(delete_times) if delete_times else 0
    results["database"]["delete"] = round(avg_delete, 2)
    print(f"  Average: {avg_delete:.2f}ms")

    # Save results
    import os
    os.makedirs(RESULTS_DIR, exist_ok=True)

    output_file = f"{RESULTS_DIR}/benchmark_results_{TIMESTAMP}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print("  COMPLETE!")
    print("=" * 60)
    print(f"\nResults saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    print("\nHTTP TPS Comparison (100 concurrent):")
    print("| Service | Framework | TPS | Avg Latency | P99 Latency |")
    print("|---------|-----------|-----|-------------|-------------|")
    for name, port, framework in SERVICES:
        data = results["http"].get(name, {}).get(100, {})
        print(f"| {name:7} | {framework:9} | {data.get('tps', 'N/A'):3} | {data.get('avg_latency_ms', 'N/A'):5} ms | {data.get('p99_latency_ms', 'N/A'):5} ms |")

    print("\nResource Usage:")
    print("| Service | CPU | Memory |")
    print("|---------|-----|--------|")
    for name, port, framework in SERVICES:
        res = results["resources"].get(name, {})
        print(f"| {name:7} | {res.get('cpu', 'N/A'):4} | {res.get('memory', 'N/A'):12} |")

if __name__ == "__main__":
    main()