import grpc
from concurrent import futures
import time
import os

# Import generated protobuf modules
import benchmark_pb2
import benchmark_pb2_grpc

class BenchmarkServicer(benchmark_pb2_grpc.BenchmarkServicer):
    def Health(self, request, context):
        return benchmark_pb2.HealthResponse(
            service="{{PROJECT_NAME}}",
            status="healthy",
            version="0.1.0",
            uptime_ns=int(time.time() * 1e9),
            timestamp=int(time.time())
        )

    def Hello(self, request, context):
        return benchmark_pb2.HelloResponse(
            service="{{PROJECT_NAME}}",
            message="Hello from {{PROJECT_NAME}} (gRPC)!",
            version="0.1.0",
            timestamp=int(time.time())
        )

    def Compute(self, request, context):
        n = min(max(request.n, 1), 35)

        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)

        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n**0.5) + 1):
                if n % i == 0:
                    return False
            return True

        start = time.time()
        fib = fibonacci(n)
        primes = [i for i in range(2, n*10) if is_prime(i)][:100]
        elapsed = time.time() - start

        return benchmark_pb2.ComputeResponse(
            operation="compute",
            fibonacci_input=n,
            fibonacci_value=fib,
            primes_count=len(primes),
            execution_time_ns=int(elapsed * 1e9),
            service="{{PROJECT_NAME}}"
        )

    def Echo(self, request, context):
        body = request.body
        return benchmark_pb2.EchoResponse(
            original_length=len(body),
            uppercase=body.upper(),
            lowercase=body.lower(),
            service="{{PROJECT_NAME}}"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    benchmark_pb2_grpc.add_BenchmarkServicer_to_server(BenchmarkServicer(), server)

    port = os.getenv("PORT", "3003")
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Starting {{PROJECT_NAME}} (gRPC) on port {port}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
