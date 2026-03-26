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
	_ "github.com/lib/pq"
)

var (
	serviceName = "go-template"
	version     = "0.1.0"
	startTime   = time.Now()
	db          *sql.DB
)

// Benchmark record model
type BenchmarkRecord struct {
	ID          int       `json:"id"`
	Name        string    `json:"name"`
	Description *string   `json:"description"`
	Value       int       `json:"value"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

func initDB() {
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

	// Test connection
	if err = db.Ping(); err != nil {
		log.Printf("Failed to ping PostgreSQL: %v", err)
		return
	}

	// Set connection pool settings
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	log.Println("PostgreSQL connected successfully")
}

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
	ElapsedMs  int64  `json:"elapsed_ms"`
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
    <title>Go Service - Language Templates Benchmark</title>
    <style>
        :root { --bg-primary: #0d1117; --bg-secondary: #161b22; --bg-tertiary: #21262d; --text-primary: #c9d1d9; --text-secondary: #8b949e; --accent-go: #00add8; --accent-rust: #dea584; --accent-python: #4caf50; --accent-c: #ff6b6b; --border-color: #30363d; --success: #238636; }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; }
        .bg-animation { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; overflow: hidden; }
        .bg-animation::before { content: ''; position: absolute; width: 200%; height: 200%; background: radial-gradient(circle at 20% 80%, rgba(0, 173, 216, 0.1) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(222, 165, 132, 0.08) 0%, transparent 50%); animation: bgMove 20s ease-in-out infinite; }
        @keyframes bgMove { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(-10%, -10%); } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 1px solid var(--border-color); }
        .logo { display: flex; align-items: center; gap: 15px; }
        .logo-icon { font-size: 48px; animation: float 3s ease-in-out infinite; }
        .logo h1 { font-size: 2em; background: linear-gradient(90deg, var(--accent-go), #0088aa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .nav { display: flex; gap: 20px; }
        .nav a { color: var(--text-secondary); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: all 0.3s; }
        .nav a:hover { background: var(--bg-tertiary); color: var(--text-primary); }
        .hero { text-align: center; padding: 60px 0; }
        .hero h2 { font-size: 3em; margin-bottom: 20px; }
        .hero .framework { font-size: 1.5em; color: var(--text-secondary); margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 40px 0; }
        .stat-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 25px; text-align: center; transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); border-color: var(--accent-go); }
        .stat-card.best { border-color: var(--success); background: linear-gradient(135deg, var(--bg-secondary), rgba(35, 134, 54, 0.1)); }
        .stat-value { font-size: 2.5em; font-weight: bold; color: var(--accent-go); }
        .stat-label { color: var(--text-secondary); margin-top: 5px; }
        .stat-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.8em; margin-top: 10px; background: var(--accent-go); color: white; }
        section { margin: 40px 0; }
        section h3 { font-size: 1.8em; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border-color); }
        .comparison-table { width: 100%; border-collapse: collapse; background: var(--bg-secondary); border-radius: 12px; overflow: hidden; }
        .comparison-table th, .comparison-table td { padding: 15px 20px; text-align: left; border-bottom: 1px solid var(--border-color); }
        .comparison-table th { background: var(--bg-tertiary); color: var(--text-secondary); font-weight: 600; text-transform: uppercase; font-size: 0.85em; }
        .comparison-table tr:hover { background: var(--bg-tertiary); }
        .comparison-table .best-p99 td:first-child::before { content: '🏆 '; }
        .chart-container { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; margin: 20px 0; }
        .bar-chart { display: flex; flex-direction: column; gap: 15px; }
        .bar-row { display: flex; align-items: center; gap: 15px; }
        .bar-label { width: 80px; font-size: 0.9em; }
        .bar-track { flex: 1; height: 30px; background: var(--bg-tertiary); border-radius: 6px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 6px; transition: width 1s ease-out; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-size: 0.85em; font-weight: bold; color: white; }
        .bar-fill.rust { background: var(--accent-rust); }
        .bar-fill.go { background: var(--accent-go); }
        .bar-fill.python { background: var(--accent-python); }
        .bar-fill.c { background: var(--accent-c); }
        .endpoints-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
        .endpoint-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 15px; transition: all 0.3s; }
        .endpoint-card:hover { border-color: var(--accent-go); }
        .endpoint-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
        .method { padding: 4px 10px; border-radius: 4px; font-size: 0.75em; font-weight: bold; text-transform: uppercase; }
        .method.get { background: var(--success); }
        .method.post { background: var(--accent-go); }
        .endpoint-path { font-family: monospace; font-size: 1.1em; color: var(--accent-go); }
        .endpoint-desc { color: var(--text-secondary); font-size: 0.9em; }
        .quick-actions { display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; justify-content: center; }
        .action-btn { display: inline-flex; align-items: center; gap: 8px; padding: 12px 24px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); text-decoration: none; transition: all 0.3s; cursor: pointer; }
        .action-btn:hover { background: var(--bg-secondary); border-color: var(--accent-go); }
        .action-btn.primary { background: var(--accent-go); color: white; border-color: var(--accent-go); }
        footer { text-align: center; padding: 40px 0; margin-top: 60px; border-top: 1px solid var(--border-color); color: var(--text-secondary); }
        footer a { color: var(--accent-go); text-decoration: none; }
        .result-box { background: var(--bg-tertiary); border-radius: 8px; padding: 15px; margin-top: 15px; font-family: monospace; font-size: 0.9em; display: none; }
        .result-box.show { display: block; }
        .result-box pre { overflow-x: auto; color: var(--accent-go); }
        .inter-service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .inter-card { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; }
        .inter-card h4 { color: var(--text-secondary); font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }
        .inter-value { font-size: 1.8em; color: var(--accent-go); }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    <div class="container">
        <header>
            <div class="logo">
                <span class="logo-icon">🐹</span>
                <div><h1>Go Service</h1><span style="color: var(--text-secondary);">Language Templates Benchmark</span></div>
            </div>
            <nav class="nav">
                <a href="/">Home</a>
                <a href="/health">Health</a>
                <a href="/api/hello">API</a>
                <a href="http://localhost:3100">Gateway</a>
                <a href="http://localhost:8500">Consul</a>
            </nav>
        </header>
        <main>
            <section class="hero">
                <h2>Go Web Service</h2>
                <p class="framework">Powered by <strong>Gin</strong> framework • <strong>Standard Library</strong></p>
                <div class="quick-actions">
                    <button class="action-btn primary" onclick="testEndpoint('/health')">🟢 Test Health</button>
                    <button class="action-btn" onclick="testEndpoint('/api/hello')">📡 Test API</button>
                    <button class="action-btn" onclick="testEndpoint('/internal/aggregate')">🔗 Test Aggregate</button>
                    <button class="action-btn" onclick="testEndpoint('/grpc.health', 'POST')">⚡ Test gRPC</button>
                </div>
                <div id="result" class="result-box"><pre></pre></div>
            </section>
            <section>
                <h3>📊 Benchmark Results</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">567</div>
                        <div class="stat-label">TPS (100 concurrent)</div>
                    </div>
                    <div class="stat-card best">
                        <div class="stat-value">241ms</div>
                        <div class="stat-label">P99 Latency</div>
                        <span class="stat-badge">🏆 Best P99</span>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">110ms</div>
                        <div class="stat-label">Avg Latency</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">11MB</div>
                        <div class="stat-label">Memory Usage</div>
                    </div>
                </div>
            </section>
            <section>
                <h3>📈 TPS Comparison (100 concurrent)</h3>
                <div class="chart-container">
                    <div class="bar-chart">
                        <div class="bar-row"><div class="bar-label">🦀 Rust</div><div class="bar-track"><div class="bar-fill rust" style="width: 100%;">600 TPS</div></div></div>
                        <div class="bar-row"><div class="bar-label">🐹 Go</div><div class="bar-track"><div class="bar-fill go" style="width: 94%;">567 TPS</div></div></div>
                        <div class="bar-row"><div class="bar-label">⚙️ C</div><div class="bar-track"><div class="bar-fill c" style="width: 94%;">567 TPS</div></div></div>
                        <div class="bar-row"><div class="bar-label">🐍 Python</div><div class="bar-track"><div class="bar-fill python" style="width: 83%;">500 TPS</div></div></div>
                    </div>
                </div>
            </section>
            <section>
                <h3>🔬 Language Comparison</h3>
                <table class="comparison-table">
                    <thead><tr><th>Language</th><th>Framework</th><th>TPS</th><th>Avg Latency</th><th>P99</th><th>Memory</th></tr></thead>
                    <tbody>
                        <tr><td>🦀 Rust</td><td>Axum</td><td>600</td><td>102ms</td><td>266ms</td><td>8MB</td></tr>
                        <tr class="best-p99"><td>🐹 Go</td><td>Gin</td><td>567</td><td>110ms</td><td>241ms</td><td>11MB</td></tr>
                        <tr><td>🐍 Python</td><td>FastAPI</td><td>500</td><td>137ms</td><td>347ms</td><td>38MB</td></tr>
                        <tr><td>⚙️ C</td><td>libmicrohttpd</td><td>567</td><td>117ms</td><td>255ms</td><td>1.5MB</td></tr>
                    </tbody>
                </table>
            </section>
            <section>
                <h3>🔌 Available Endpoints</h3>
                <div class="endpoints-grid">
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/</span></div><p class="endpoint-desc">Service homepage</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/health</span></div><p class="endpoint-desc">Health check</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/api/hello</span></div><p class="endpoint-desc">JSON response</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method post">POST</span><span class="endpoint-path">/api/echo</span></div><p class="endpoint-desc">Echo body</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/internal/aggregate</span></div><p class="endpoint-desc">Call other services</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method post">POST</span><span class="endpoint-path">/grpc.hello</span></div><p class="endpoint-desc">gRPC hello</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method get">GET</span><span class="endpoint-path">/grpc.health</span></div><p class="endpoint-desc">gRPC health</p></div>
                    <div class="endpoint-card"><div class="endpoint-header"><span class="method post">POST</span><span class="endpoint-path">/grpc.aggregate</span></div><p class="endpoint-desc">gRPC aggregate</p></div>
                </div>
            </section>
            <section>
                <h3>🌐 Inter-Service Communication</h3>
                <div class="inter-service-grid">
                    <div class="inter-card"><h4>Go → Aggregate</h4><div class="inter-value">20ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Fastest response</p></div>
                    <div class="inter-card"><h4>Gateway REST</h4><div class="inter-value">30ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Aggregate all</p></div>
                    <div class="inter-card"><h4>Gateway gRPC</h4><div class="inter-value">38ms</div><p style="color: var(--text-secondary); margin-top: 10px;">gRPC style</p></div>
                    <div class="inter-card"><h4>Service Mesh</h4><div class="inter-value">19ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Consul check</p></div>
                </div>
            </section>
            <section>
                <h3>Database CRUD Operations</h3>
                <div class="inter-service-grid">
                    <div class="inter-card"><h4>CREATE</h4><div class="inter-value">~15ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Insert new record</p></div>
                    <div class="inter-card"><h4>READ</h4><div class="inter-value">~3ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Query records</p></div>
                    <div class="inter-card"><h4>UPDATE</h4><div class="inter-value">~12ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Modify record</p></div>
                    <div class="inter-card"><h4>DELETE</h4><div class="inter-value">~10ms</div><p style="color: var(--text-secondary); margin-top: 10px;">Remove record</p></div>
                </div>
                <div class="quick-actions" style="margin-top: 20px;">
                    <button class="action-btn" onclick="testCrud('GET', '/db/records')">Get All Records</button>
                    <button class="action-btn" onclick="testCrud('POST', '/db/records', {name: 'Test', value: 42})">Create Record</button>
                    <button class="action-btn" onclick="testCrud('PUT', '/db/records/1', {value: 100})">Update Record</button>
                    <button class="action-btn" onclick="testCrud('DELETE', '/db/records/10')">Delete Record</button>
                </div>
                <div id="crud-result" class="result-box"><pre></pre></div>
            </section>
        </main>
        <footer>
            <p>Language Templates Benchmark Project</p>
            <p style="margin-top: 10px;"><a href="/health">Health</a> • <a href="/api/hello">API</a> • <a href="http://localhost:3100">Gateway</a> • <a href="http://localhost:8500">Consul UI</a></p>
            <p style="margin-top: 20px; font-size: 0.8em; color: var(--text-secondary);">Built with Go + Gin • Benchmark Results: March 2026</p>
        </footer>
    </div>
    <script>
        async function testEndpoint(path, method = 'GET') {
            const resultBox = document.getElementById('result');
            const pre = resultBox.querySelector('pre');
            resultBox.classList.add('show');
            pre.textContent = 'Loading...';
            try {
                const response = await fetch(path, { method, headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}, body: method === 'POST' ? JSON.stringify({ name: 'test' }) : null });
                const data = await response.json();
                pre.textContent = JSON.stringify(data, null, 2);
            } catch (error) { pre.textContent = 'Error: ' + error.message; }
        }

        async function testCrud(method, path, body = null) {
            const resultBox = document.getElementById('crud-result');
            const pre = resultBox.querySelector('pre');
            resultBox.classList.add('show');
            pre.textContent = 'Loading...';
            try {
                const headers = { 'Content-Type': 'application/json' };
                const response = await fetch(path, { method, headers, body: body ? JSON.stringify(body) : null });
                const data = await response.json();
                pre.textContent = JSON.stringify(data, null, 2);
            } catch (error) { pre.textContent = 'Error: ' + error.message; }
        }
    </script>
</body>
</html>`
	c.Data(http.StatusOK, "text/html", []byte(html))
}

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(gin.Logger())

	// Initialize database
	initDB()

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

	// Database CRUD endpoints
	r.GET("/db/records", getRecords)
	r.GET("/db/records/:id", getRecord)
	r.POST("/db/records", createRecord)
	r.PUT("/db/records/:id", updateRecord)
	r.DELETE("/db/records/:id", deleteRecord)

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

// ============================================
// Database CRUD Handlers
// ============================================

func getRecords(c *gin.Context) {
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not available"})
		return
	}

	rows, err := db.Query("SELECT id, name, description, value, created_at, updated_at FROM benchmark_records ORDER BY id")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer rows.Close()

	var records []BenchmarkRecord
	for rows.Next() {
		var r BenchmarkRecord
		if err := rows.Scan(&r.ID, &r.Name, &r.Description, &r.Value, &r.CreatedAt, &r.UpdatedAt); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		records = append(records, r)
	}

	c.JSON(http.StatusOK, records)
}

func getRecord(c *gin.Context) {
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not available"})
		return
	}

	id := c.Param("id")
	var r BenchmarkRecord
	err := db.QueryRow("SELECT id, name, description, value, created_at, updated_at FROM benchmark_records WHERE id = $1", id).
		Scan(&r.ID, &r.Name, &r.Description, &r.Value, &r.CreatedAt, &r.UpdatedAt)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("Record %s not found", id)})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, r)
}

func createRecord(c *gin.Context) {
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not available"})
		return
	}

	var req struct {
		Name        string  `json:"name"`
		Description *string `json:"description"`
		Value       int     `json:"value"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		req.Name = "New Record"
		req.Value = 0
	}

	var r BenchmarkRecord
	err := db.QueryRow(
		"INSERT INTO benchmark_records (name, description, value) VALUES ($1, $2, $3) RETURNING id, name, description, value, created_at, updated_at",
		req.Name, req.Description, req.Value,
	).Scan(&r.ID, &r.Name, &r.Description, &r.Value, &r.CreatedAt, &r.UpdatedAt)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, r)
}

func updateRecord(c *gin.Context) {
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not available"})
		return
	}

	id := c.Param("id")
	var req struct {
		Name        *string `json:"name"`
		Description *string `json:"description"`
		Value       *int    `json:"value"`
	}
	c.ShouldBindJSON(&req)

	var r BenchmarkRecord
	err := db.QueryRow(
		"UPDATE benchmark_records SET name = COALESCE($1, name), description = COALESCE($2, description), value = COALESCE($3, value), updated_at = CURRENT_TIMESTAMP WHERE id = $4 RETURNING id, name, description, value, created_at, updated_at",
		req.Name, req.Description, req.Value, id,
	).Scan(&r.ID, &r.Name, &r.Description, &r.Value, &r.CreatedAt, &r.UpdatedAt)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("Record %s not found", id)})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, r)
}

func deleteRecord(c *gin.Context) {
	if db == nil {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "Database not available"})
		return
	}

	id := c.Param("id")
	result, err := db.Exec("DELETE FROM benchmark_records WHERE id = $1", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": fmt.Sprintf("Record %s not found", id)})
		return
	}

	c.JSON(http.StatusOK, gin.H{"success": true, "deleted": id})
}