package main

import (
	"bytes"
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	_ "github.com/lib/pq"
)

var (
	serviceName = "{{PROJECT_NAME}}"
	version     = "0.1.0"
	startTime   = time.Now()
	db          *sql.DB
)

// Database model
type BenchmarkRecord struct {
	ID          int       `json:"id"`
	Name        string    `json:"name"`
	Description *string   `json:"description"`
	Value       int       `json:"value"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

func initDB() {
	enableDB := os.Getenv("ENABLE_DATABASE")
	if enableDB != "true" {
		log.Println("ENABLE_DATABASE=false, skipping database connection")
		return
	}

	databaseURL := os.Getenv("DATABASE_URL")
	if databaseURL == "" {
		log.Println("DATABASE_URL not set, skipping database connection")
		return
	}

	var err error
	db, err = sql.Open("postgres", databaseURL)
	if err != nil {
		log.Printf("Failed to connect to PostgreSQL: %v", err)
		return
	}

	if err = db.Ping(); err != nil {
		log.Printf("Failed to ping PostgreSQL: %v", err)
		return
	}

	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)
	log.Println("PostgreSQL connected successfully")
}

// ============================================
// HTTP Handlers
// ============================================

func health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"service":    serviceName,
		"version":    version,
		"uptime_seconds": time.Since(startTime).Seconds(),
	})
}

func hello(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message":   fmt.Sprintf("Hello from %s!", serviceName),
		"service":   serviceName,
		"version":   version,
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
		"operation":       "compute",
		"fibonacci_input": n,
		"fibonacci_value": fib,
		"primes_count":    len(primes),
		"execution_time_ns": elapsed.Nanoseconds(),
		"service":         serviceName,
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
	})
}

func index(c *gin.Context) {
	html := fmt.Sprintf(`<!DOCTYPE html>
<html>
<head>
    <title>%s</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }
        h1 { color: #4caf50; }
        .card { background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }
        a { color: #4caf50; }
    </style>
</head>
<body>
    <h1>%s</h1>
    <div class="card">
        <p>Version: %s</p>
        <p>Protocol: HTTP</p>
        <p>Language: Go</p>
    </div>
    <div class="card">
        <h3>Endpoints</h3>
        <ul>
            <li><a href="/health">/health</a> - Health check</li>
            <li><a href="/api/hello">/api/hello</a> - JSON greeting</li>
            <li><a href="/api/compute">/api/compute</a> - CPU benchmark</li>
            <li>POST /api/echo - Echo body</li>
        </ul>
    </div>
</body>
</html>`, serviceName, serviceName, version)
	c.Data(http.StatusOK, "text/html", []byte(html))
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	initDB()

	r.GET("/", index)
	r.GET("/health", health)
	r.GET("/api/hello", hello)
	r.GET("/api/compute", compute)
	r.POST("/api/echo", echo)

	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	log.Printf("Starting %s (HTTP) on port %s", serviceName, port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
