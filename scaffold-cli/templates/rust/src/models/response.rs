//! Response data models
//!
//! Shared response structures used across the application.

use serde::{Deserialize, Serialize};

/// Health check response
#[derive(Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub version: Option<String>,
}

impl HealthResponse {
    /// Create a new healthy response
    pub fn healthy(service: impl Into<String>) -> Self {
        Self {
            status: "healthy".to_string(),
            service: service.into(),
            version: None,
        }
    }

    /// Create a new healthy response with version
    pub fn healthy_with_version(service: impl Into<String>, version: impl Into<String>) -> Self {
        Self {
            status: "healthy".to_string(),
            service: service.into(),
            version: Some(version.into()),
        }
    }
}

/// Hello API response
#[derive(Serialize, Deserialize)]
pub struct HelloResponse {
    pub message: String,
    pub service: String,
    pub version: String,
}

impl HelloResponse {
    /// Create a new hello response
    pub fn new(service: impl Into<String>, version: impl Into<String>) -> Self {
        Self {
            message: "Hello from Rust!".to_string(),
            service: service.into(),
            version: version.into(),
        }
    }
}

/// Error response
#[derive(Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
    pub status: u16,
}

impl ErrorResponse {
    /// Create a new error response
    pub fn new(error: impl Into<String>, status: u16) -> Self {
        Self {
            error: error.into(),
            status,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_health_response() {
        let response = HealthResponse::healthy("test-service");
        assert_eq!(response.status, "healthy");
        assert_eq!(response.service, "test-service");
        assert!(response.version.is_none());
    }

    #[test]
    fn test_hello_response() {
        let response = HelloResponse::new("test-service", "1.0.0");
        assert_eq!(response.message, "Hello from Rust!");
        assert_eq!(response.service, "test-service");
        assert_eq!(response.version, "1.0.0");
    }
}
