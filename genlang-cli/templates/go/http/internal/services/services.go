// Package services - Business logic services
package services

import (
	"crypto/sha256"
	"encoding/hex"
	"strconv"
	"time"
)

// ComputeService - CPU-intensive benchmark operations
type ComputeService struct {
	serviceName string
}

// NewComputeService creates a new compute service
func NewComputeService(serviceName string) *ComputeService {
	return &ComputeService{serviceName: serviceName}
}

// fibonacci calculates fibonacci number recursively
func fibonacci(n int) int {
	if n <= 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2)
}

// isPrime checks if number is prime
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

// Execute performs CPU benchmark
func (s *ComputeService) Execute(nStr string) map[string]interface{} {
	n, _ := strconv.Atoi(nStr)
	if n > 35 {
		n = 35
	}
	if n < 1 {
		n = 1
	}

	start := time.Now()

	// Calculate fibonacci
	fibResult := fibonacci(n)

	// Find primes
	primes := []int{}
	for i := 2; i < n*10 && len(primes) < 500; i++ {
		if isPrime(i) {
			primes = append(primes, i)
		}
	}

	elapsed := time.Since(start).Milliseconds()

	return map[string]interface{}{
		"operation":         "compute",
		"fibonacci_input":   n,
		"fibonacci_value":   fibResult,
		"primes_found":      len(primes),
		"execution_time_ms": elapsed,
		"service":           s.serviceName,
	}
}

// EchoService - Data processing and transformation
type EchoService struct {
	serviceName string
}

// NewEchoService creates a new echo service
func NewEchoService(serviceName string) *EchoService {
	return &EchoService{serviceName: serviceName}
}

// Process transforms request body
func (s *EchoService) Process(body []byte) map[string]interface{} {
	text := string(body)

	// SHA256 hash
	h := sha256.Sum256([]byte(text))
	sha := hex.EncodeToString(h[:])[:16]

	// Word count
	words := 0
	lastSpace := true
	for _, ch := range text {
		if ch == ' ' || ch == '\n' || ch == '\t' {
			lastSpace = true
		} else if lastSpace {
			words++
			lastSpace = false
		}
	}

	return map[string]interface{}{
		"original_length": len(text),
		"word_count":      words,
		"char_count":      len(text),
		"uppercase":       text,
		"lowercase":       text,
		"sha256_prefix":   sha,
		"service":         s.serviceName,
	}
}