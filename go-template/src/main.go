package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	serviceName = "go-template"
	version     = "0.1.0"
)

// ============================================
// 1. JSON API - Simple greeting
// ============================================
func helloHandler(c *gin.Context) {
	c.JSON(200, gin.H{
		"message":  "Hello from Go!",
		"service":  serviceName,
		"version": version,
	})
}

// ============================================
// 2. CPU Computation - Fibonacci + Primes
// ============================================
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

func computeHandler(c *gin.Context) {
	nStr := c.DefaultQuery("n", "30")
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

	c.JSON(200, gin.H{
		"operation":       "compute",
		"fibonacci_35":     fibResult,
		"primes_found":    len(primes),
		"execution_time_ms": elapsed,
		"service":          serviceName,
	})
}

// ============================================
// 3. Data Processing - Echo + Transform
// ============================================
func echoHandler(c *gin.Context) {
	body, _ := c.GetRawData()
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

	c.JSON(200, gin.H{
		"original_length": len(text),
		"word_count":      words,
		"char_count":      len(text),
		"uppercase":       text,
		"lowercase":       text,
		"sha256_prefix":   sha,
	})
}

// ============================================
// Health Check
// ============================================
func healthHandler(c *gin.Context) {
	c.JSON(200, gin.H{
		"status":  "healthy",
		"service":  serviceName,
		"version": version,
	})
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Static files
	r.StaticFile("/", "./static/index.html")
	r.Static("/static", "./static")

	// Routes
	r.GET("/health", healthHandler)
	r.GET("/api/hello", helloHandler)
	r.GET("/api/compute", computeHandler)
	r.POST("/api/echo", echoHandler)

	// Server config
	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	addr := ":" + port
	log.Printf("%s v%s listening on %s", serviceName, version, addr)

	// Graceful shutdown
	go func() {
		if err := r.Run(addr); err != nil {
			log.Fatal(err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	time.Sleep(1 * time.Second)
}
