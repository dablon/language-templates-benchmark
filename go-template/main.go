package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"google.golang.org/grpc"
)

var (
	serviceName = "go-template"
	version     = "0.1.0"
	startTime   = time.Now()
)

// ============================================
// Service endpoints configuration
// ============================================
var serviceEndpoints = map[string]string{
	"rust":   getEnv("RUST_SERVICE_URL", "http://localhost:3001"),
	"python": getEnv("PYTHON_SERVICE_URL", "http://localhost:3003"),
	"c":      getEnv("C_SERVICE_URL", "http://localhost:3004"),
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// ============================================
// gRPC Protocol Message Definitions
// ============================================

type GrpcHelloRequest struct {
	Name string `json:"name"`
}

type GrpcHelloResponse struct {
	ServiceName string   `json:"service_name"`
	Message     string   `json:"message"`
	Version     string   `json:"version"`
	Timestamp   int64    `json:"timestamp"`
	Results     []string `json:"results"`
}

type GrpcHealthRequest struct{}

type GrpcHealthResponse struct {
	Services map[string]bool `json:"services"`
	Timestamp int64          `json:"timestamp"`
}

type GrpcAggregateRequest struct {
	Name *string `json:"name"`
}

type ServiceResult struct {
	Service    string `json:"service"`
	Message    string `json:"message"`
	ElapsedMs  uint64 `json:"elapsed_ms"`
	Success    bool   `json:"success"`
}

type GrpcAggregateResponse struct {
	Caller        string          `json:"caller"`
	Results       []ServiceResult `json:"results"`
	TotalTimeMs   uint64          `json:"total_time_ms"`
}

// HTTP client for inter-service calls
var httpClient = &http.Client{
	Timeout: 5 * time.Second,
}

// ============================================
// gRPC Service Implementation
// ============================================

func callService(serviceKey, path string) map[string]interface{} {
	url, ok := serviceEndpoints[serviceKey]
	if !ok {
		return map[string]interface{}{
			"service": serviceKey,
			"error":   "service not found",
			"success": false,
		}
	}

	fullURL := url + path
	start := time.Now()

	resp, err := httpClient.Get(fullURL)
	elapsed := time.Since(start).Milliseconds()

	if err != nil {
		return map[string]interface{}{
			"service":    serviceKey,
			"error":      err.Error(),
			"success":    false,
			"elapsed_ms": elapsed,
		}
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		var data map[string]interface{}
		if err := json.NewDecoder(resp.Body).Decode(&data); err == nil {
			data["success"] = true
			data["elapsed_ms"] = elapsed
			return data
		}
	}

	return map[string]interface{}{
		"service":    serviceKey,
		"error":      http.StatusText(resp.StatusCode),
		"status":     resp.StatusCode,
		"success":    false,
		"elapsed_ms": elapsed,
	}
}

// CallAllServices calls all registered services in parallel
func callAllServices(path string) []map[string]interface{} {
	results := make([]map[string]interface{}, 0, len(serviceEndpoints))

	for key := range serviceEndpoints {
		results = append(results, callService(key, path))
	}

	return results
}

// gRPC-style Hello handler
func grpcHello(req GrpcHelloRequest) GrpcHelloResponse {
	results := make([]string, 0)

	for service, url := range serviceEndpoints {
		start := time.Now()
		resp, err := httpClient.Get(url + "/api/hello")
		elapsed := time.Since(start).Milliseconds()

		if err == nil && resp.StatusCode == http.StatusOK {
			var data map[string]interface{}
			if json.NewDecoder(resp.Body).Decode(&data) == nil {
				if msg, ok := data["message"].(string); ok {
					results = append(results, fmt.Sprintf("%s: %s (%dms)", service, msg, elapsed))
				}
			}
		}
	}

	return GrpcHelloResponse{
		ServiceName: serviceName,
		Message:     fmt.Sprintf("Hello from Go! Greeted: %s", req.Name),
		Version:     version,
		Timestamp:  time.Now().Unix(),
		Results:    results,
	}
}

// gRPC-style Health handler
func grpcHealth() GrpcHealthResponse {
	services := make(map[string]bool)
	services["go"] = true

	for service, url := range serviceEndpoints {
		resp, err := httpClient.Get(url + "/health")
		services[service] = err == nil && resp != nil && resp.StatusCode == http.StatusOK
	}

	return GrpcHealthResponse{
		Services:  services,
		Timestamp: time.Now().Unix(),
	}
}

// gRPC-style Aggregate handler
func grpcAggregate(req GrpcAggregateRequest) GrpcAggregateResponse {
	start := time.Now()
	results := make([]ServiceResult, 0)

	for service, url := range serviceEndpoints {
		start := time.Now()
		resp, err := httpClient.Get(url + "/api/hello")
		elapsed := time.Since(start).Milliseconds()

		if err == nil && resp.StatusCode == http.StatusOK {
			var data map[string]interface{}
			if json.NewDecoder(resp.Body).Decode(&data) == nil {
				msg, _ := data["message"].(string)
				results = append(results, ServiceResult{
					Service:   service,
					Message:   msg,
					ElapsedMs: elapsed,
					Success:   true,
				})
			}
		} else {
			errMsg := "error"
			if err != nil {
				errMsg = err.Error()
			}
			results = append(results, ServiceResult{
				Service:   service,
				Message:   errMsg,
				ElapsedMs: 0,
				Success:   false,
			})
		}
	}

	return GrpcAggregateResponse{
		Caller:      serviceName,
		Results:     results,
		TotalTimeMs: uint64(time.Since(start).Milliseconds()),
	}
}

// ============================================
// Standard REST Handlers
// ============================================

func health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": serviceName,
	})
}

func hello(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "Hello from Go!",
		"service": serviceName,
		"version": version,
	})
}

func echo(c *gin.Context) {
	buf := new(bytes.Buffer)
	buf.ReadFrom(c.Request.Body)
	c.Data(http.StatusOK, "text/plain", buf.Bytes())
}

// Aggregate handler - call all services and aggregate
func aggregate(c *gin.Context) {
	start := time.Now()
	results := callAllServices("/api/hello")
	elapsed := time.Since(start).Milliseconds()

	c.JSON(http.StatusOK, gin.H{
		"caller":        serviceName,
		"results":       results,
		"total_time_ms": elapsed,
	})
}

// Chain handler - sequential service calls
func chain(c *gin.Context) {
	start := time.Now()

	// Read body if present
	var body struct {
		Payload string `json:"payload"`
	}
	c.ShouldBindJSON(&body)

	// Chain: Go -> Rust -> Python -> C
	results := make([]map[string]interface{}, 0)

	// First hop: Go -> Rust
	results = append(results, callService("rust", "/api/hello"))

	// Second hop: Rust -> Python
	results = append(results, callService("python", "/api/hello"))

	elapsed := time.Since(start).Milliseconds()

	c.JSON(http.StatusOK, gin.H{
		"service":      serviceName,
		"chain":        results,
		"total_time_ms": elapsed,
	})
}

// ============================================
// gRPC-style HTTP Handlers
// ============================================

func grpcHelloHandler(c *gin.Context) {
	var req GrpcHelloRequest
	c.ShouldBindJSON(&req)

	if req.Name == "" {
		req.Name = "world"
	}

	response := grpcHello(req)
	c.JSON(http.StatusOK, response)
}

func grpcHealthHandler(c *gin.Context) {
	response := grpcHealth()
	c.JSON(http.StatusOK, response)
}

func grpcAggregateHandler(c *gin.Context) {
	var req GrpcAggregateRequest
	c.ShouldBindJSON(&req)

	response := grpcAggregate(req)
	c.JSON(http.StatusOK, response)
}

func index(c *gin.Context) {
	html := `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Go Template - Web Service</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #00add8; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }
        code { background: #0f3460; padding: 2px 6px; border-radius: 4px; }
        a { color: #00add8; }
    </style>
</head>
<body>
    <h1>Go Web Service Template</h1>
    <div class="card">
        <h2>Language: Go</h2>
        <p>Framework: <code>Gin</code></p>
        <p>Port: <code>3002</code></p>
    </div>
    <div class="card">
        <h2>Endpoints</h2>
        <ul>
            <li><a href="/health">GET /health</a> - Health check</li>
            <li><a href="/api/hello">GET /api/hello</a> - JSON response</li>
            <li>POST /api/echo - Echo body</li>
            <li>GET /internal/aggregate - Call all services</li>
            <li>POST /internal/chain - Chain services</li>
            <li>POST /grpc/hello - gRPC-style hello</li>
            <li>GET /grpc/health - gRPC-style health</li>
            <li>POST /grpc/aggregate - gRPC-style aggregate</li>
        </ul>
    </div>
</body>
</html>`
	c.Data(http.StatusOK, "text/html", []byte(html))
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	r.GET("/", index)
	r.GET("/health", health)
	r.GET("/api/hello", hello)
	r.POST("/api/echo", echo)

	// Inter-service communication
	r.GET("/internal/aggregate", aggregate)
	r.POST("/internal/chain", chain)

	// gRPC-style endpoints
	r.POST("/grpc/hello", grpcHelloHandler)
	r.GET("/grpc/health", grpcHealthHandler)
	r.POST("/grpc/aggregate", grpcAggregateHandler)

	// Register with Consul for service mesh (placeholder)
	go registerWithConsul()

	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	log.Printf("Go template listening on %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatal(err)
	}
}

// Placeholder for Consul service mesh registration
func registerWithConsul() {
	// In production, this would register with Consul
	// consul agent service register -name=go-template -port=3002 -http=3002
	time.Sleep(2 * time.Second)
	log.Println("Service mesh: ready for Consul registration (placeholder)")
}