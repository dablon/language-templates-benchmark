// Package main - Go HTTP Web Service Template
// Clean Architecture with cmd/internal/pkg structure
package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"{{PROJECT_NAME}}/internal/handlers"
	"{{PROJECT_NAME}}/internal/services"
)

const (
	serviceName = "{{PROJECT_NAME}}"
	version     = "0.1.0"
)

func main() {
	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Initialize services
	computeSvc := services.NewComputeService(serviceName)
	echoSvc := services.NewEchoService(serviceName)

	// Initialize handlers
	healthHandler := handlers.NewHealthHandler(serviceName, version)
	apiHandler := handlers.NewAPIHandler(computeSvc, echoSvc, serviceName, version)

	// Static files
	r.StaticFile("/", "./static/index.html")
	r.Static("/static", "./static")

	// Routes
	r.GET("/health", healthHandler.Health)
	r.GET("/api/hello", apiHandler.Hello)
	r.GET("/api/compute", apiHandler.Compute)
	r.POST("/api/echo", apiHandler.Echo)

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