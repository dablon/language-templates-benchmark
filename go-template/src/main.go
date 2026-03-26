package main

import (
	"bytes"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
)

const (
	serviceName = "go-template"
	version     = "0.1.0"
)

func main() {
	// Configure Gin for production
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Serve static files
	r.Static("/static", "./static")
	r.GET("/", func(c *gin.Context) {
		http.ServeFile(c.Writer, c.Request, "./static/index.html")
	})

	// API Routes
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": serviceName,
			"version": version,
		})
	})

	r.GET("/api/hello", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Hello from Go!",
			"service": serviceName,
			"version": version,
		})
	})

	r.POST("/api/echo", func(c *gin.Context) {
		buf := new(bytes.Buffer)
		buf.ReadFrom(c.Request.Body)
		c.Data(http.StatusOK, "text/plain", buf.Bytes())
	})

	// Server configuration
	port := os.Getenv("PORT")
	if port == "" {
		port = "3002"
	}
	addr := ":" + port

	// Start server
	go func() {
		log.Printf("%s v%s listening on %s", serviceName, version, addr)
		if err := r.Run(addr); err != nil {
			log.Fatal(err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	time.Sleep(1 * time.Second)
}