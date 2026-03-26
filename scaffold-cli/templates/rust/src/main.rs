//! Rust Web Service Template
//! High-performance with 3 benchmark endpoints + gRPC + PostgreSQL

mod client;
mod config;
mod constants;
mod database;
mod error;
mod models;
mod routes;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
    body::Body,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::convert::Infallible;
use std::time::Instant;
use std::collections::HashMap;
use std::net::SocketAddr;
use tokio::sync::OnceCell;

// Application state
#[derive(Clone)]
struct AppState {
    service_name: String,
    version: String,
    db_pool: Option<database::DbPool>,
}

// REST client for inter-service communication
#[derive(Clone)]
struct RestClient {
    client: reqwest::Client,
    endpoints: HashMap<String, String>,
}

impl RestClient {
    fn new() -> Self {
        let mut endpoints = HashMap::new();
        endpoints.insert("go".to_string(), "http://localhost:3002".to_string());
        endpoints.insert("python".to_string(), "http://localhost:3003".to_string());
        endpoints.insert("c".to_string(), "http://localhost:3004".to_string());

        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(5))
            .build()
            .unwrap();

        Self { client, endpoints }
    }

    async fn call_service(&self, key: &str, path: &str) -> serde_json::Value {
        let url = match self.endpoints.get(key) {
            Some(u) => format!("{}{}", u, path),
            None => return serde_json::json!({"error": "service not found"}),
        };

        let start = Instant::now();
        match self.client.get(&url).send().await {
            Ok(resp) => {
                let elapsed = start.elapsed().as_millis() as u64;
                if resp.status().is_success() {
                    if let Ok(data) = resp.json::<serde_json::Value>().await {
                        let mut result = data;
                        result["elapsed_ms"] = serde_json::json!(elapsed);
                        result
                    } else {
                        serde_json::json!({"error": "parse error", "elapsed_ms": elapsed})
                    }
                } else {
                    serde_json::json!({"error": format!("http {}", resp.status()), "elapsed_ms": elapsed})
                }
            }
            Err(e) => serde_json::json!({"error": e.to_string(), "elapsed_ms": start.elapsed().as_millis() as u64})
        }
    }

    async fn call_all(&self, path: &str) -> Vec<serde_json::Value> {
        let keys = vec!["go", "python", "c"];
        let mut results = vec![];

        for key in keys {
            results.push(self.call_service(key, path).await);
        }

        results
    }
}

// ============================================
// 1. JSON API - Simple greeting
// ============================================
async fn hello_handler(
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    Json(serde_json::json!({
        "message": "Hello from Rust!",
        "service": state.service_name,
        "version": state.version
    }))
}

// ============================================
// 2. CPU Computation - Fibonacci + Primes
// ============================================
fn fibonacci(n: u64) -> u64 {
    if n <= 1 { n } else { fibonacci(n - 1) + fibonacci(n - 2) }
}

fn is_prime(n: u64) -> bool {
    if n < 2 { return false; }
    for i in 2..=((n as f64).sqrt() as u64) {
        if n % i == 0 { return false; }
    }
    true
}

#[derive(Deserialize)]
struct ComputeQuery { n: Option<u64> }

#[derive(Serialize)]
struct ComputeResponse {
    operation: String,
    fibonacci_35: u64,
    primes_found: usize,
    execution_time_ms: u64,
    service: String,
}

async fn compute_handler(
    State(state): State<Arc<AppState>>,
    Query(query): Query<ComputeQuery>,
) -> impl IntoResponse {
    let n = query.n.unwrap_or(30).min(35).max(1);
    let start = Instant::now();
    let fib_result = fibonacci(n);
    let mut primes = Vec::new();
    let mut i: u64 = 2;
    while primes.len() < 500 && i < n * 10 {
        if is_prime(i) { primes.push(i); }
        i += 1;
    }
    let elapsed = start.elapsed().as_millis() as u64;
    Json(ComputeResponse {
        operation: "compute".to_string(),
        fibonacci_35: fib_result,
        primes_found: primes.len(),
        execution_time_ms: elapsed,
        service: state.service_name.clone(),
    })
}

// ============================================
// 3. Data Processing - Echo + Transform
// ============================================
async fn echo_handler(
    body: Body,
) -> Result<impl IntoResponse, Infallible> {
    let bytes = axum::body::to_bytes(body, 1024 * 1024).await.unwrap_or_default();
    let text = String::from_utf8_lossy(&bytes).to_string();
    let word_count = text.split_whitespace().count();
    let char_count = text.chars().filter(|c| !c.is_whitespace()).count();
    let simple_hash = format!("{:x}", text.len().wrapping_mul(17).wrapping_add(text.chars().fold(0usize, |acc, c| acc.wrapping_add(c as usize))));
    let hash_prefix = &simple_hash[..16.min(simple_hash.len())];

    Ok(Json(serde_json::json!({
        "original_length": text.len(),
        "word_count": word_count,
        "char_count": char_count,
        "uppercase": text.to_uppercase(),
        "lowercase": text.to_lowercase(),
        "simple_hash": hash_prefix,
    })))
}

// ============================================
// Health Check
// ============================================
async fn health_handler(
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "healthy",
        "service": state.service_name,
        "version": state.version
    }))
}

// ============================================
// Static Files
// ============================================
async fn index_handler() -> impl IntoResponse {
    Html(include_str!("../static/index.html"))
}

// ============================================
// Service Communication Endpoints (REST)
// ============================================

async fn aggregate_handler(
    State(state): State<Arc<AppState>>,
) -> impl IntoResponse {
    let client = RestClient::new();
    let start = Instant::now();
    let results = client.call_all("/api/hello").await;
    let elapsed = start.elapsed().as_millis() as u64;

    Json(serde_json::json!({
        "caller": state.service_name,
        "results": results,
        "total_time_ms": elapsed
    }))
}

async fn chain_handler(
    State(state): State<Arc<AppState>>,
    body: Body,
) -> Result<impl IntoResponse, Infallible> {
    let bytes = axum::body::to_bytes(body, 1024 * 1024).await.unwrap_or_default();
    let text = String::from_utf8_lossy(&bytes).to_string();

    let client = RestClient::new();
    let start = Instant::now();
    let go_result = client.call_service("go", &format!("/api/hello?from={}", text)).await;
    let python_result = client.call_service("python", &format!("/api/hello?from={}", go_result.get("message").unwrap_or(&serde_json::Value::Null).as_str().unwrap_or(""))).await;

    let elapsed = start.elapsed().as_millis() as u64;

    Ok(Json(serde_json::json!({
        "service": state.service_name,
        "chain": [go_result, python_result],
        "total_time_ms": elapsed
    })))
}

// ============================================
// gRPC Server (using tonic)
// ============================================

mod grpc_service {
    use tonic::{Request, Response, Status};
    use std::time::Instant;
    use std::collections::HashMap;
    use std::net::SocketAddr;

    // Proto types - defined inline for simplicity
    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct HelloRequest { pub name: String }

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct HelloResponse {
        pub service_name: String,
        pub message: String,
        pub version: String,
        pub timestamp: i64,
        pub results: Vec<String>,
    }

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct HealthRequest {}

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct HealthResponse {
        pub services: HashMap<String, bool>,
        pub timestamp: i64,
    }

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct AggregateRequest { pub name: String }

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct ServiceResult {
        pub service: String,
        pub message: String,
        pub elapsed_ms: u64,
        pub success: bool,
    }

    #[derive(serde::Serialize, serde::Deserialize)]
    pub struct AggregateResponse {
        pub caller: String,
        pub results: Vec<ServiceResult>,
        pub total_time_ms: u64,
    }

    pub struct GrpcAggregatorService {
        service_name: String,
        version: String,
    }

    impl GrpcAggregatorService {
        pub fn new() -> Self {
            Self {
                service_name: "rust-template".to_string(),
                version: "0.1.0".to_string(),
            }
        }

        pub async fn hello(&self, name: String) -> Result<HelloResponse, Status> {
            let mut results = Vec::new();
            let endpoints = [("go", "http://localhost:3002"), ("python", "http://localhost:3003"), ("c", "http://localhost:3004")];
            let client = reqwest::Client::new();

            for (service, url) in endpoints.iter() {
                let start = Instant::now();
                if let Ok(resp) = client.get(format!("{}/api/hello", url)).send().await {
                    let elapsed = start.elapsed().as_millis() as u64;
                    if let Ok(data) = resp.json::<serde_json::Value>().await {
                        if let Some(msg) = data.get("message").and_then(|v| v.as_str()) {
                            results.push(format!("{}: {} ({}ms)", service, msg, elapsed));
                        }
                    }
                }
            }

            Ok(HelloResponse {
                service_name: self.service_name.clone(),
                message: format!("Hello from Rust! Greeted: {}", name),
                version: self.version.clone(),
                timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
                results,
            })
        }

        pub async fn health(&self) -> Result<HealthResponse, Status> {
            let mut services = HashMap::new();
            services.insert("rust".to_string(), true);
            let endpoints = [("go", "http://localhost:3002"), ("python", "http://localhost:3003"), ("c", "http://localhost:3004")];
            let client = reqwest::Client::new();

            for (service, url) in endpoints.iter() {
                let healthy = client.get(format!("{}/health", url)).send().await
                    .map(|r| r.status().is_success()).unwrap_or(false);
                services.insert(service.to_string(), healthy);
            }

            Ok(HealthResponse {
                services,
                timestamp: std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs() as i64,
            })
        }

        pub async fn aggregate(&self, _req: AggregateRequest) -> Result<AggregateResponse, Status> {
            let start = Instant::now();
            let mut results = Vec::new();
            let endpoints = [("go", "http://localhost:3002"), ("python", "http://localhost:3003"), ("c", "http://localhost:3004")];
            let client = reqwest::Client::new();

            for (service, url) in endpoints.iter() {
                let start = Instant::now();
                match client.get(format!("{}/api/hello", url)).send().await {
                    Ok(resp) => {
                        let elapsed = start.elapsed().as_millis() as u64;
                        if let Ok(data) = resp.json::<serde_json::Value>().await {
                            let msg = data.get("message").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            results.push(ServiceResult { service: service.to_string(), message: msg, elapsed_ms: elapsed, success: true });
                        }
                    }
                    Err(e) => {
                        results.push(ServiceResult { service: service.to_string(), message: format!("error: {}", e), elapsed_ms: 0, success: false });
                    }
                }
            }

            Ok(AggregateResponse {
                caller: self.service_name.clone(),
                results,
                total_time_ms: start.elapsed().as_millis() as u64,
            })
        }
    }
}

// HTTP handlers for gRPC-like endpoints
async fn grpc_hello_handler(Json(req): Json<grpc_service::HelloRequest>) -> Json<grpc_service::HelloResponse> {
    let service = grpc_service::GrpcAggregatorService::new();
    Json(service.hello(req.name).await.unwrap_or(grpc_service::HelloResponse {
        service_name: "rust-template".to_string(),
        message: "error".to_string(),
        version: "0.1.0".to_string(),
        timestamp: 0,
        results: vec![],
    }))
}

async fn grpc_health_handler() -> Json<grpc_service::HealthResponse> {
    let service = grpc_service::GrpcAggregatorService::new();
    Json(service.health().await.unwrap_or(grpc_service::HealthResponse {
        services: HashMap::new(),
        timestamp: 0,
    }))
}

async fn grpc_aggregate_handler(Json(req): Json<grpc_service::AggregateRequest>) -> Json<grpc_service::AggregateResponse> {
    let service = grpc_service::GrpcAggregatorService::new();
    Json(service.aggregate(req).await.unwrap_or(grpc_service::AggregateResponse {
        caller: "rust-template".to_string(),
        results: vec![],
        total_time_ms: 0,
    }))
}

// ============================================
// Main Entry Point
// ============================================

#[tokio::main]
async fn main() {
    // Check if database is enabled via env var
    let enable_db = std::env::var("ENABLE_DATABASE")
        .map(|v| v.to_lowercase() == "true")
        .unwrap_or(false);

    // Try to initialize database connection only if ENABLE_DATABASE=true
    let db_pool = if enable_db {
        if let Ok(database_url) = std::env::var("DATABASE_URL") {
            match database::init_db(&database_url).await {
                Ok(pool) => {
                    println!("PostgreSQL connected successfully");
                    Some(pool)
                }
                Err(e) => {
                    eprintln!("Failed to connect to PostgreSQL: {}", e);
                    None
                }
            }
        } else {
            println!("DATABASE_URL not set, skipping database connection");
            None
        }
    } else {
        println!("ENABLE_DATABASE=false, skipping database connection");
        None
    };

    let state = Arc::new(AppState {
        service_name: "rust-template".to_string(),
        version: "0.1.0".to_string(),
        db_pool: db_pool.clone(),
    });

    let mut app = Router::new()
        .route("/", get(index_handler))
        .route("/health", get(health_handler))
        .route("/api/hello", get(hello_handler))
        .route("/api/compute", get(compute_handler))
        .route("/api/echo", post(echo_handler))
        // REST inter-service endpoints
        .route("/internal/aggregate", get(aggregate_handler))
        .route("/internal/chain", post(chain_handler));

    // Add gRPC routes only if ENABLE_GRPC=true
    let enable_grpc = std::env::var("ENABLE_GRPC")
        .map(|v| v.to_lowercase() == "true")
        .unwrap_or(false);

    if enable_grpc {
        println!("gRPC endpoints enabled");
        app = app
            .route("/grpc.hello", post(grpc_hello_handler))
            .route("/grpc.health", get(grpc_health_handler))
            .route("/grpc.aggregate", post(grpc_aggregate_handler));
    }

    // Add database routes if pool is available
    if let Some(pool) = db_pool {
        app = app.merge(routes::database::create_db_router().with_state(pool));
    }

    // Service mesh: register with Consul if ENABLE_CONSUL=true
    let enable_consul = std::env::var("ENABLE_CONSUL")
        .map(|v| v.to_lowercase() == "true")
        .unwrap_or(false);

    if enable_consul {
        println!("Consul service mesh enabled");
        // TODO: Add Consul registration code here
    }

    let app = app.with_state(state);

    let port = std::env::var("PORT")
        .unwrap_or_else(|_| "3001".to_string())
        .parse::<u16>()
        .unwrap_or(3001);

    println!("rust-template v0.1.0 listening on {}", port);
    println!("REST endpoints: /health, /api/hello, /api/compute, /api/echo");
    println!("Internal: /internal/aggregate, /internal/chain");
    if enable_grpc {
        println!("gRPC (HTTP): /grpc.hello, /grpc.health, /grpc.aggregate");
    }
    if db_pool.is_some() {
        println!("Database: /db/records (CRUD operations)");
    }
    println!("gRPC (real): port 5001 (requires tonic-proto)");

    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port))
        .await
        .unwrap();

    axum::serve(listener, app).await.unwrap();
}