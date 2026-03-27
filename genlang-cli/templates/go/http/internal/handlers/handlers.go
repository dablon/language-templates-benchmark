// Package handlers - HTTP request handlers
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"{{PROJECT_NAME}}/internal/services"
)

// HealthHandler - Health check endpoint handler
type HealthHandler struct {
	serviceName string
	version     string
}

// NewHealthHandler creates a new health handler
func NewHealthHandler(serviceName, version string) *HealthHandler {
	return &HealthHandler{
		serviceName: serviceName,
		version:     version,
	}
}

// Health returns health status
func (h *HealthHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"service": h.serviceName,
		"version": h.version,
	})
}

// APIHandler - API endpoint handlers
type APIHandler struct {
	computeSvc *services.ComputeService
	echoSvc    *services.EchoService
	serviceName string
	version     string
}

// NewAPIHandler creates a new API handler
func NewAPIHandler(computeSvc *services.ComputeService, echoSvc *services.EchoService, serviceName, version string) *APIHandler {
	return &APIHandler{
		computeSvc:  computeSvc,
		echoSvc:     echoSvc,
		serviceName: serviceName,
		version:     version,
	}
}

// Hello returns greeting message
func (h *APIHandler) Hello(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message":  "Hello from " + h.serviceName + "!",
		"service":  h.serviceName,
		"version": h.version,
	})
}

// Compute handles CPU benchmark endpoint
func (h *APIHandler) Compute(c *gin.Context) {
	nStr := c.DefaultQuery("n", "30")
	result := h.computeSvc.Execute(nStr)
	c.JSON(http.StatusOK, result)
}

// Echo handles echo endpoint
func (h *APIHandler) Echo(c *gin.Context) {
	body, _ := c.GetRawData()
	result := h.echoSvc.Process(body)
	c.JSON(http.StatusOK, result)
}

// WebHandler - Web UI handler
type WebHandler struct {
	serviceName string
	version     string
}

// NewWebHandler creates a new web handler
func NewWebHandler(serviceName, version string) *WebHandler {
	return &WebHandler{
		serviceName: serviceName,
		version:     version,
	}
}