//! REST client for inter-service communication
//!
//! Provides utilities to call other language services.

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};

/// Service endpoint configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceEndpoint {
    pub name: String,
    pub url: String,
    pub timeout_ms: u64,
}

impl Default for ServiceEndpoint {
    fn default() -> Self {
        Self {
            name: String::new(),
            url: String::new(),
            timeout_ms: 5000,
        }
    }
}

/// Response from a service call
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceResponse {
    pub service: String,
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    pub elapsed_ms: u64,
}

/// Client for making REST calls to other services
pub struct RestClient {
    client: Client,
    endpoints: std::collections::HashMap<String, ServiceEndpoint>,
}

impl RestClient {
    /// Create a new REST client with default endpoints
    pub fn new() -> Self {
        let mut endpoints = std::collections::HashMap::new();

        // Default service endpoints (can be overridden via env)
        endpoints.insert(
            "go".to_string(),
            ServiceEndpoint {
                name: "go-template".to_string(),
                url: std::env::var("GO_SERVICE_URL").unwrap_or_else(|_| "http://localhost:3002".to_string()),
                timeout_ms: 5000,
            },
        );
        endpoints.insert(
            "python".to_string(),
            ServiceEndpoint {
                name: "python-template".to_string(),
                url: std::env::var("PYTHON_SERVICE_URL").unwrap_or_else(|_| "http://localhost:3003".to_string()),
                timeout_ms: 5000,
            },
        );
        endpoints.insert(
            "c".to_string(),
            ServiceEndpoint {
                name: "c-template".to_string(),
                url: std::env::var("C_SERVICE_URL").unwrap_or_else(|_| "http://localhost:3004".to_string()),
                timeout_ms: 5000,
            },
        );

        let client = Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to create HTTP client");

        Self { client, endpoints }
    }

    /// Call a service and get its response
    pub async fn call_service(&self, service_key: &str, path: &str) -> ServiceResponse {
        let endpoint = match self.endpoints.get(service_key) {
            Some(ep) => ep,
            None => {
                return ServiceResponse {
                    service: service_key.to_string(),
                    success: false,
                    data: None,
                    error: Some("Service not found".to_string()),
                    elapsed_ms: 0,
                };
            }
        };

        let url = format!("{}{}", endpoint.url, path);
        let start = Instant::now();

        match self.client.get(&url).send().await {
            Ok(response) => {
                let elapsed_ms = start.elapsed().as_millis() as u64;
                if response.status().is_success() {
                    match response.json().await {
                        Ok(data) => ServiceResponse {
                            service: endpoint.name.clone(),
                            success: true,
                            data: Some(data),
                            error: None,
                            elapsed_ms,
                        },
                        Err(e) => ServiceResponse {
                            service: endpoint.name.clone(),
                            success: false,
                            data: None,
                            error: Some(format!("JSON parse error: {}", e)),
                            elapsed_ms,
                        },
                    }
                } else {
                    ServiceResponse {
                        service: endpoint.name.clone(),
                        success: false,
                        data: None,
                        error: Some(format!("HTTP error: {}", response.status())),
                        elapsed_ms,
                    }
                }
            }
            Err(e) => ServiceResponse {
                service: endpoint.name.clone(),
                success: false,
                data: None,
                error: Some(format!("Connection error: {}", e)),
                elapsed_ms: start.elapsed().as_millis() as u64,
            },
        }
    }

    /// Call all registered services in parallel
    pub async fn call_all_services(&self, path: &str) -> Vec<ServiceResponse> {
        let mut handles = vec![];

        for key in self.endpoints.keys() {
            let key_clone = key.clone();
            let path_clone = path.to_string();
            let client = self.client.clone();
            let endpoints = self.endpoints.clone();

            handles.push(tokio::spawn(async move {
                let endpoint = match endpoints.get(&key_clone) {
                    Some(ep) => ep,
                    None => return ServiceResponse {
                        service: key_clone,
                        success: false,
                        data: None,
                        error: Some("Not found".to_string()),
                        elapsed_ms: 0,
                    },
                };

                let url = format!("{}{}", endpoint.url, path_clone);
                let start = Instant::now();

                match client.get(&url).send().await {
                    Ok(response) => {
                        let elapsed_ms = start.elapsed().as_millis() as u64;
                        if response.status().is_success() {
                            match response.json().await {
                                Ok(data) => ServiceResponse {
                                    service: endpoint.name.clone(),
                                    success: true,
                                    data: Some(data),
                                    error: None,
                                    elapsed_ms,
                                },
                                Err(e) => ServiceResponse {
                                    service: endpoint.name.clone(),
                                    success: false,
                                    data: None,
                                    error: Some(format!("JSON error: {}", e)),
                                    elapsed_ms,
                                },
                            }
                        } else {
                            ServiceResponse {
                                service: endpoint.name.clone(),
                                success: false,
                                data: None,
                                error: Some(format!("HTTP {}", response.status())),
                                elapsed_ms,
                            }
                        }
                    }
                    Err(e) => ServiceResponse {
                        service: endpoint.name.clone(),
                        success: false,
                        data: None,
                        error: Some(format!("Connection: {}", e)),
                        elapsed_ms: start.elapsed().as_millis() as u64,
                    },
                }
            }));
        }

        let mut results = vec![];
        for handle in handles {
            if let Ok(result) = handle.await {
                results.push(result);
            }
        }
        results
    }
}

impl Default for RestClient {
    fn default() -> Self {
        Self::new()
    }
}