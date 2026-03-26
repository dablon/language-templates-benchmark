package main

import (
	"bytes"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/gin-gonic/gin"
)

var (
	serviceName = "go-template"
	version     = "0.1.0"
	startTime   = time.Now()
)

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
    <h1>🐹 Go Web Service Template</h1>
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

	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}

	log.Printf("Go template listening on %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatal(err)
	}
}
