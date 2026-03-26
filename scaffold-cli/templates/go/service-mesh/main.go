package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/hashicorp/consul/api"
	_ "github.com/lib/pq"
)

var (
	serviceName  = "{{PROJECT_NAME}}"
	version      = "0.1.0"
	startTime    = time.Now()
	db           *sql.DB
	consulClient *api.Client
)

// ============================================
// Service Mesh Configuration
// ============================================

type ServiceMeshConfig struct {
	Enabled    bool
	ConsulAddr string
	ServiceID  string
}

var meshConfig ServiceMeshConfig

func initMesh() {
	enableConsul := os.Getenv("ENABLE_CONSUL", "false")
	if enableConsul != "true" {
		log.Println("ENABLE_CONSUL=false, running without service mesh")
		meshConfig = ServiceMeshConfig{Enabled: false}
		return
	}

	consulAddr := os.Getenv("CONSUL_ADDR", "localhost:8500")
	serviceID := os.Getenv("SERVICE_NAME", serviceName)

	cfg := api.DefaultConfig()
	cfg.Address = consulAddr
	client, err := api.NewClient(cfg)
	if err != nil {
		log.Printf("Failed to connect to Consul at %s: %v", consulAddr, err)
		meshConfig = ServiceMeshConfig{Enabled: false}
		return
	}

	consulClient = client
	meshConfig = ServiceMeshConfig{
		Enabled:    true,
		ConsulAddr: consulAddr,
		ServiceID:  serviceID,
	}

	// Register service with Consul
	registerService()

	log.Printf("Service mesh enabled - Consul: %s, ServiceID: %s", consulAddr, serviceID)
}

func registerService() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	svc := &api.AgentServiceRegistration{
		ID:   meshConfig.ServiceID + "-" + port,
		Name: meshConfig.ServiceID,
		Port: 3002,
		Check: &api.AgentServiceCheck{
			HTTP:     fmt.Sprintf("http://localhost:%s/health", port),
			Interval: "10s",
			Done:     "30s",
		},
	}

	if err := consulClient.Agent().ServiceRegister(svc); err != nil {
		log.Printf("Failed to register service with Consul: %v", err)
	}
}

func deregisterService() {
	if meshConfig.Enabled && consulClient != nil {
		consulClient.Agent().ServiceDeregister(meshConfig.ServiceID + "-3002")
	}
}

// ============================================
// Service Discovery via Consul
// ============================================

func getServiceEndpoint(serviceKey string) string {
	if !meshConfig.Enabled || consulClient == nil {
		// Fallback to default endpoints
		defaults := map[string]string{
			"rust":   "localhost:3001",
			"python": "localhost:3003",
			"c":      "localhost:3004",
		}
		return defaults[serviceKey]
	}

	services, _, err := consulClient.Health().Service(serviceKey, "", true, nil)
	if err != nil || len(services) == 0 {
		log.Printf("Service %s not found in Consul, using fallback", serviceKey)
		defaults := map[string]string{
			"rust":   "localhost:3001",
			"python": "localhost:3003",
			"c":      "localhost:3004",
		}
		return defaults[serviceKey]
	}

	return fmt.Sprintf("localhost:%d", services[0].Service.Port)
}

// ============================================
// HTTP Handlers
// ============================================

func health(c *gin.Context) {
	svcStatus := map[string]string{"status": "healthy"}
	if meshConfig.Enabled {
		svcStatus["mesh"] = "consul"
		svcStatus["consul_addr"] = meshConfig.ConsulAddr
	}

	c.JSON(http.StatusOK, gin.H{
		"service":        serviceName,
		"version":        version,
		"uptime_seconds": time.Since(startTime).Seconds(),
		"protocol":       "service-mesh",
		"mesh_status":    svcStatus,
	})
}

func hello(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message":   fmt.Sprintf("Hello from %s (Service Mesh)!", serviceName),
		"service":   serviceName,
		"version":   version,
		"protocol":  "service-mesh",
		"mesh":      meshConfig.Enabled,
		"timestamp": time.Now().Unix(),
	})
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

func compute(c *gin.Context) {
	n := 30
	if p := c.Query("n"); p != "" {
		fmt.Sscanf(p, "%d", &n)
	}
	if n > 35 {
		n = 35
	}

	start := time.Now()
	fib := fibonacci(n)
	var primes []int
	for i := 2; i < n*10; i++ {
		if isPrime(i) {
			primes = append(primes, i)
			if len(primes) >= 100 {
				break
			}
		}
	}
	elapsed := time.Since(start)

	c.JSON(http.StatusOK, gin.H{
		"operation":        "compute",
		"fibonacci_input":  n,
		"fibonacci_value":  fib,
		"primes_count":     len(primes),
		"execution_time_ns": elapsed.Nanoseconds(),
		"service":          serviceName,
		"protocol":         "service-mesh",
	})
}

func echo(c *gin.Context) {
	buf := new(bytes.Buffer)
	buf.ReadFrom(c.Request.Body)
	body := buf.String()

	c.JSON(http.StatusOK, gin.H{
		"original_length": len(body),
		"uppercase":       bytes.ToUpper([]byte(body)),
		"lowercase":       bytes.ToLower([]byte(body)),
		"service":         serviceName,
		"protocol":        "service-mesh",
	})
}

func index(c *gin.Context) {
	meshInfo := "disabled"
	if meshConfig.Enabled {
		meshInfo = fmt.Sprintf("Consul @ %s", meshConfig.ConsulAddr)
	}

	html := fmt.Sprintf(`<!DOCTYPE html>
<html>
<head>
    <title>%s</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #4caf50; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }
        a { color: #4caf50; }
        .mesh { color: #ff9800; }
    </style>
</head>
<body>
    <h1>%s</h1>
    <div class="card">
        <p>Version: %s</p>
        <p>Protocol: <span class="mesh">Service Mesh (HTTP + Consul)</span></p>
        <p>Mesh: %s</p>
    </div>
</body>
</html>`, serviceName, serviceName, version, meshInfo)
	c.Data(http.StatusOK, "text/html", []byte(html))
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	initMesh()
	defer deregisterService()

	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	log.Printf("Starting %s (Service Mesh) on port %s", serviceName, port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
