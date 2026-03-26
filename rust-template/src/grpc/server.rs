//! gRPC Server for inter-service communication
//!
//! Uses tonic to expose gRPC endpoints on port 5001.

use tonic::{Request, Response, Status};
use std::time::Instant;
use std::collections::HashMap;
use reqwest::Client;
use serde_json::Value;

pub mod proto {
    include!("proto.rs");
}

use proto::{
    aggregate_request::AggregateRequest,
    aggregate_response::AggregateResponse,
    hello_response::HelloResponse as ProtoHelloResponse,
};

// Service endpoints for gRPC calls
fn get_service_endpoints() -> HashMap<&'static str, &'static str> {
    let mut endpoints = HashMap::new();
    endpoints.insert("go", "http://localhost:3002");
    endpoints.insert("python", "http://localhost:3003");
    endpoints.insert("c", "http://localhost:3004");
    endpoints
}

#[derive(Default)]
pub struct AggregatorService {
    service_name: String,
    version: String,
}

impl AggregatorService {
    pub fn new() -> Self {
        Self {
            service_name: "rust-template".to_string(),
            version: "0.1.0".to_string(),
        }
    }
}

#[tonic::async_trait]
impl proto::aggregator_server::Aggregator for AggregatorService {
    async fn hello(
        &self,
        request: Request<proto::HelloRequest>,
    ) -> Result<Response<proto::HelloResponse>, Status> {
        let name = request.into_inner().name;

        // Call all other services
        let endpoints = get_service_endpoints();
        let client = Client::new();
        let mut results = Vec::new();

        for (service, url) in endpoints {
            let start = Instant::now();
            let url = format!("{}/api/hello", url);

            match client.get(&url).send().await {
                Ok(resp) => {
                    let elapsed = start.elapsed().as_millis() as u64;
                    if resp.status().is_success() {
                        if let Ok(data) = resp.json::<Value>().await {
                            let msg = data.get("message")
                                .and_then(|v| v.as_str())
                                .unwrap_or("unknown")
                                .to_string();
                            results.push(format!("{}: {} ({}ms)", service, msg, elapsed));
                        }
                    }
                }
                Err(_) => {}
            }
        }

        let response = proto::HelloResponse {
            service_name: self.service_name.clone(),
            message: format!("Hello from Rust! Greeted: {}", name),
            version: self.version.clone(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
            results,
        };

        Ok(Response::new(response))
    }

    async fn health(
        &self,
        _request: Request<proto::HealthRequest>,
    ) -> Result<Response<proto::HealthResponse>, Status> {
        let endpoints = get_service_endpoints();
        let client = Client::new();
        let mut services = std::collections::HashMap::new();

        services.insert("rust".to_string(), true);

        for (service, url) in endpoints {
            let url = format!("{}/health", url);
            let healthy = client.get(&url).send().await
                .map(|r| r.status().is_success())
                .unwrap_or(false);
            services.insert(service.to_string(), healthy);
        }

        let response = proto::HealthResponse {
            services,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
        };

        Ok(Response::new(response))
    }

    async fn aggregate(
        &self,
        request: Request<proto::AggregateRequest>,
    ) -> Result<Response<proto::AggregateResponse>, Status> {
        let _request = request.into_inner();
        let start = Instant::now();

        let endpoints = get_service_endpoints();
        let client = Client::new();
        let mut results = Vec::new();

        for (service, url) in endpoints {
            let start = Instant::now();
            let url = format!("{}/api/hello", url);

            match client.get(&url).send().await {
                Ok(resp) => {
                    let elapsed = start.elapsed().as_millis() as u64;
                    if let Ok(data) = resp.json::<Value>().await {
                        results.push(proto::hello_response::Result {
                            service: service.to_string(),
                            message: data.get("message")
                                .and_then(|v| v.as_str())
                                .unwrap_or("")
                                .to_string(),
                            elapsed_ms: elapsed,
                            success: true,
                        });
                    }
                }
                Err(e) => {
                    results.push(proto::hello_response::Result {
                        service: service.to_string(),
                        message: format!("error: {}", e),
                        elapsed_ms: 0,
                        success: false,
                    });
                }
            }
        }

        let total_time_ms = start.elapsed().as_millis() as u64;

        let response = proto::AggregateResponse {
            caller: self.service_name.clone(),
            results,
            total_time_ms,
        };

        Ok(Response::new(response))
    }
}