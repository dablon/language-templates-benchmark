//! gRPC Server Implementation using Tonic
//!
//! Provides real gRPC endpoints on port 5001 using protobuf.

use tonic::{Request, Response, Status};
use std::time::Instant;
use std::collections::HashMap;
use std::net::SocketAddr;

// Generated proto types
pub mod proto {
    include!("proto.rs");
}

use proto::{HelloRequest, HelloResponse, HealthRequest, HealthResponse, AggregateRequest, AggregateResponse, ServiceResult};

// Service endpoints
fn get_service_endpoints() -> HashMap<&'static str, &'static str> {
    let mut endpoints = HashMap::new();
    endpoints.insert("go", "http://localhost:3002");
    endpoints.insert("python", "http://localhost:3003");
    endpoints.insert("c", "http://localhost:3004");
    endpoints
}

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
        request: Request<HelloRequest>,
    ) -> Result<Response<HelloResponse>, Status> {
        let name = request.into_inner().name;
        let mut results = Vec::new();

        // Call other services via REST (gRPC would call gRPC endpoints)
        let endpoints = get_service_endpoints();
        let client = reqwest::Client::new();

        for (service, url) in endpoints {
            let start = Instant::now();
            let target = format!("{}/api/hello", url);

            match client.get(&target).send().await {
                Ok(resp) => {
                    let elapsed = start.elapsed().as_millis() as u64;
                    if let Ok(data) = resp.json::<serde_json::Value>().await {
                        if let Some(msg) = data.get("message").and_then(|v| v.as_str()) {
                            results.push(format!("{}: {} ({}ms)", service, msg, elapsed));
                        }
                    }
                }
                Err(_) => {}
            }
        }

        let response = HelloResponse {
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
        _request: Request<HealthRequest>,
    ) -> Result<Response<HealthResponse>, Status> {
        let endpoints = get_service_endpoints();
        let client = reqwest::Client::new();
        let mut services = HashMap::new();

        services.insert("rust".to_string(), true);

        for (service, url) in endpoints {
            let target = format!("{}/health", url);
            let healthy = client.get(&target).send().await
                .map(|r| r.status().is_success())
                .unwrap_or(false);
            services.insert(service.to_string(), healthy);
        }

        let response = HealthResponse {
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
        _request: Request<AggregateRequest>,
    ) -> Result<Response<AggregateResponse>, Status> {
        let start = Instant::now();
        let endpoints = get_service_endpoints();
        let client = reqwest::Client::new();
        let mut results = Vec::new();

        for (service, url) in endpoints {
            let start = Instant::now();
            let target = format!("{}/api/hello", url);

            match client.get(&target).send().await {
                Ok(resp) => {
                    let elapsed = start.elapsed().as_millis() as u64;
                    if let Ok(data) = resp.json::<serde_json::Value>().await {
                        let msg = data.get("message")
                            .and_then(|v| v.as_str())
                            .unwrap_or("")
                            .to_string();
                        results.push(ServiceResult {
                            service: service.to_string(),
                            message: msg,
                            elapsed_ms: elapsed,
                            success: true,
                        });
                    }
                }
                Err(e) => {
                    results.push(ServiceResult {
                        service: service.to_string(),
                        message: format!("error: {}", e),
                        elapsed_ms: 0,
                        success: false,
                    });
                }
            }
        }

        let total_time_ms = start.elapsed().as_millis() as u64;

        let response = AggregateResponse {
            caller: self.service_name.clone(),
            results,
            total_time_ms,
        };

        Ok(Response::new(response))
    }
}

/// Start the gRPC server
pub async fn run_grpc_server() -> Result<(), Box<dyn std::error::Error>> {
    let addr = SocketAddr::from(([0, 0, 0, 0], 5001));

    let service = AggregatorService::new();

    println!("Starting gRPC server on {}", addr);
    println!("gRPC endpoints available:");

    tonic::build::configure()
        .build_server(true);

    // Use a simple tower service to expose gRPC
    use tonic::transport::Server;
    use tower::util::ServiceExt;

    Server::builder()
        .add_service(proto::aggregator_server::AggregatorServer::new(service))
        .serve(addr)
        .await?;

    Ok(())
}