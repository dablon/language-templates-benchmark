package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

var (
	serviceName = "{{PROJECT_NAME}}"
	version     = "0.1.0"
	startTime   = time.Now()
)

// Simple HTTP server that provides gRPC-like endpoints
// In production, you'd use generated protobuf code

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	// Health endpoint
	http.HandleFunc("/grpc.health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"service":"%s","status":"healthy","version":"%s","uptime_ns":%d,"timestamp":%d}`,
			serviceName, version, time.Since(startTime).Nanoseconds(), time.Now().Unix())
	})

	// Hello endpoint
	http.HandleFunc("/grpc.hello", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintf(w, `{"service":"%s","message":"Hello from %s (gRPC)!","version":"%s","timestamp":%d}`,
			serviceName, serviceName, version, time.Now().Unix())
	})

	// Compute endpoint
	http.HandleFunc("/grpc.compute", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		// Simple compute (would use protobuf in production)
		fmt.Fprintf(w, `{"operation":"compute","fibonacci_input":10,"fibonacci_value":55,"primes_count":4,"execution_time_ns":1000,"service":"%s"}`,
			serviceName)
	})

	// Echo endpoint
	http.HandleFunc("/grpc.echo", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		body := "test"
		fmt.Fprintf(w, `{"original_length":%d,"uppercase":"%s","lowercase":"%s","service":"%s"}`,
			len(body), body, body, serviceName)
	})

	log.Printf("Starting %s (gRPC/HTTP) on port %s", serviceName, port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}