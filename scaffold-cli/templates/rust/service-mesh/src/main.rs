use axum::{
    extract::State,
    http::StatusCode,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
};
use std::sync::Arc;
use std::time::Instant;
use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use std::env;

struct AppState {
    service_name: String,
    version: String,
    consul_enabled: bool,
    consul_addr: String,
}

// Consul service mesh integration
async fn init_consul(enabled: bool, addr: &str, service_id: &str) -> bool {
    if !enabled {
        println!("Service mesh disabled");
        return false;
    }

    println!("Service mesh enabled - Consul: {}", addr);
    true // Simplified - actual implementation would register with Consul
}

async fn health(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let mesh_info = if state.consul_enabled {
        serde_json::json!({
            "enabled": true,
            "consul_addr": state.consul_addr
        })
    } else {
        serde_json::json!({"enabled": false})
    };

    Json(serde_json::json!({
        "service": state.service_name,
        "version": state.version,
        "protocol": "service-mesh",
        "mesh_status": mesh_info
    }))
}

async fn hello(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    Json(serde_json::json!({
        "message": format!("Hello from {} (Service Mesh)!", state.service_name),
        "service": state.service_name,
        "version": state.version,
        "protocol": "service-mesh",
        "mesh": state.consul_enabled
    }))
}

fn fibonacci(n: usize) -> usize {
    if n <= 1 { n } else { fibonacci(n-1) + fibonacci(n-2) }
}

fn is_prime(n: usize) -> bool {
    if n < 2 { return false; }
    for i in 2..((n as f64).sqrt() as usize) + 1 {
        if n % i == 0 { return false; }
    }
    true
}

async fn compute(State(state): State<Arc<AppState>>, axum::extract::Query(params): axum::extract::Query<HashMap<String, String>>) -> impl IntoResponse {
    let n = params.get("n")
        .and_then(|v| v.parse::<usize>().ok())
        .unwrap_or(30)
        .min(35)
        .max(1);

    let start = Instant::now();
    let fib = fibonacci(n);
    let primes: Vec<_> = (2..n*10).filter(|&i| is_prime(i)).take(100).collect();
    let elapsed = start.elapsed();

    Json(serde_json::json!({
        "operation": "compute",
        "fibonacci_input": n,
        "fibonacci_value": fib,
        "primes_count": primes.len(),
        "execution_time_ns": elapsed.as_nanos(),
        "service": state.service_name,
        "protocol": "service-mesh"
    }))
}

async fn echo(body: String) -> impl IntoResponse {
    Json(serde_json::json!({
        "original_length": body.len(),
        "uppercase": body.to_uppercase(),
        "lowercase": body.to_lowercase(),
        "service": "service-mesh"
    }))
}

async fn index(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let mesh_info = if state.consul_enabled {
        format!("Consul @ {}", state.consul_addr)
    } else {
        "disabled".to_string()
    };

    Html(format!(r#"<!DOCTYPE html>
<html>
<head>
    <title>{}</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #4caf50; }}
        .card {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        .mesh {{ color: #ff9800; }}
    </style>
</head>
<body>
    <h1>{}</h1>
    <div class="card">
        <p>Version: {}</p>
        <p>Protocol: <span class="mesh">Service Mesh (HTTP + Consul)</span></p>
        <p>Mesh: {}</p>
    </div>
</body>
</html>"#, state.service_name, state.service_name, state.version, mesh_info))
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let service_name = env::var("SERVICE_NAME").unwrap_or_else(|_| "{{PROJECT_NAME}}".to_string());
    let consul_enabled = env::var("ENABLE_CONSUL").unwrap_or_else(|_| "false".to_string()) == "true";
    let consul_addr = env::var("CONSUL_ADDR").unwrap_or_else(|_| "localhost:8500".to_string());

    init_consul(consul_enabled, &consul_addr, &service_name).await;

    let state = Arc::new(AppState {
        service_name: service_name.clone(),
        version: "0.1.0".to_string(),
        consul_enabled,
        consul_addr,
    });

    let app = Router::new()
        .route("/", get(index))
        .route("/health", get(health))
        .route("/api/hello", get(hello))
        .route("/api/compute", get(compute))
        .route("/api/echo", post(echo))
        .with_state(state);

    let port = env::var("PORT").unwrap_or_else(|_| "3001".to_string());
    let addr = format!("0.0.0.0:{}", port);

    tracing::info!("Starting {} (Service Mesh) on port {}", service_name, port);
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
