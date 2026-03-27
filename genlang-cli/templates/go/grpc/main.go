package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

// Proto message types (manually defined instead of generated)
type HealthRequest struct{}
type HealthResponse struct {
	Service   string `json:"service"`
	Status    string `json:"status"`
	Version   string `json:"version"`
	UptimeNs  int64  `json:"uptime_ns"`
	Timestamp int64  `json:"timestamp"`
}

type HelloRequest struct{}
type HelloResponse struct {
	Service   string `json:"service"`
	Message   string `json:"message"`
	Version   string `json:"version"`
	Timestamp int64  `json:"timestamp"`
}

type ComputeRequest struct{ N int64 }
type ComputeResponse struct {
	Operation       string `json:"operation"`
	FibonacciInput  int64  `json:"fibonacci_input"`
	FibonacciValue  int64  `json:"fibonacci_value"`
	PrimesCount     int64  `json:"primes_count"`
	ExecutionTimeNs int64  `json:"execution_time_ns"`
	Service         string `json:"service"`
}

type EchoRequest struct{ Body string }
type EchoResponse struct {
	OriginalLength int64  `json:"original_length"`
	Uppercase      string `json:"uppercase"`
	Lowercase      string `json:"lowercase"`
	Service        string `json:"service"`
}

// Server interface (simplified - not using generated protobuf)
type BenchmarkServer interface {
	Health(context.Context, *HealthRequest) (*HealthResponse, error)
	Hello(context.Context, *HelloRequest) (*HelloResponse, error)
	Compute(context.Context, *ComputeRequest) (*ComputeResponse, error)
	Echo(context.Context, *EchoRequest) (*EchoResponse, error)
}

var (
	serviceName = "{{PROJECT_NAME}}"
	version     = "0.1.0"
	startTime   = time.Now()
)

// ============================================
// gRPC Service Definition
// ============================================

type BenchmarkService struct {
	pb.UnimplementedBenchmarkServer
}

func (s *BenchmarkService) Health(ctx context.Context, req *pb.HealthRequest) (*pb.HealthResponse, error) {
	return &pb.HealthResponse{
		Service:    serviceName,
		Status:     "healthy",
		Version:     version,
		UptimeNs:   time.Since(startTime).Nanoseconds(),
		Timestamp:  time.Now().Unix(),
	}, nil
}

func (s *BenchmarkService) Hello(ctx context.Context, req *pb.HelloRequest) (*pb.HelloResponse, error) {
	return &pb.HelloResponse{
		Service:  serviceName,
		Message:  fmt.Sprintf("Hello from %s (gRPC)!", serviceName),
		Version:  version,
		Timestamp: time.Now().Unix(),
	}, nil
}

func (s *BenchmarkService) Compute(ctx context.Context, req *pb.ComputeRequest) (*pb.ComputeResponse, error) {
	n := int(req.N)
	if n > 35 {
		n = 35
	}
	if n < 1 {
		n = 1
	}

	start := time.Now()
	fib := fibonacci(n)
	var primes []int64
	for i := int64(2); int64(i) < int64(n)*10; i++ {
		if isPrime(int(i)) {
			primes = append(primes, i)
			if len(primes) >= 100 {
				break
			}
		}
	}
	elapsed := time.Since(start)

	return &pb.ComputeResponse{
		Operation:      "compute",
		FibonacciInput: int64(n),
		FibonacciValue: int64(fib),
		PrimesCount:    int64(len(primes)),
		ExecutionTimeNs: elapsed.Nanoseconds(),
		Service:        serviceName,
	}, nil
}

func (s *BenchmarkService) Echo(ctx context.Context, req *pb.EchoRequest) (*pb.EchoResponse, error) {
	body := req.Body
	return &pb.EchoResponse{
		OriginalLength: int64(len(body)),
		Uppercase:      string([]byte(body)),
		Lowercase:      string([]byte(body)),
		Service:        serviceName,
	}, nil
}

func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2)
}

func isPrime(n int) bool {
	if n < 2 {
		return false
	}
	for i := 2; i*i <= n; i++ {
		if n%i == 0 {
			return false
		}
	}
	return true
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	lis, err := net.Listen("tcp", ":"+port)
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer()
	RegisterBenchmarkServer(grpcServer, &BenchmarkService{})
	reflection.Register(grpcServer)

	log.Printf("Starting %s (gRPC) on port %s", serviceName, port)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
