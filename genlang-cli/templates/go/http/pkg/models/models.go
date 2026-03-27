// Package models - Data models
package models

// Response structures
type (
	// HelloResponse for /api/hello endpoint
	HelloResponse struct {
		Message string `json:"message"`
		Service string `json:"service"`
		Version string `json:"version"`
	}

	// ComputeResponse for /api/compute endpoint
	ComputeResponse struct {
		Operation       string `json:"operation"`
		FibonacciInput  int    `json:"fibonacci_input"`
		FibonacciValue  int    `json:"fibonacci_value"`
		PrimesFound     int    `json:"primes_found"`
		ExecutionTimeMs int64  `json:"execution_time_ms"`
		Service         string `json:"service"`
	}

	// EchoResponse for /api/echo endpoint
	EchoResponse struct {
		OriginalLength int    `json:"original_length"`
		WordCount      int    `json:"word_count"`
		CharCount      int    `json:"char_count"`
		Uppercase      string `json:"uppercase"`
		Lowercase      string `json:"lowercase"`
		SHA256Prefix   string `json:"sha256_prefix"`
		Service        string `json:"service"`
	}

	// HealthResponse for /health endpoint
	HealthResponse struct {
		Status  string `json:"status"`
		Service string `json:"service"`
		Version string `json:"version"`
	}
)