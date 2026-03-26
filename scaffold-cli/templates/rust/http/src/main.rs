//! Rust HTTP Web Service Template
//! High-performance benchmark service with pure HTTP

use axum::{
    extract::State,
    http::StatusCode,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
};
use std::sync::Arc;
use std::time::Instant;
use std::env;

struct AppState {
    service_name: String,
    version: String,
}

#[derive(Clone)]
struct BenchmarkRecord {
    id: i64,
    name: String,
    description: Option<String>,
    value: i64,
}

async fn health(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "healthy",
        "service": state.service_name,
        "version": state.version,
    }))
}

async fn hello(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    Json(serde_json::json!({
        "message": format!("Hello from {}!", state.service_name),
        "service": state.service_name,
        "version": state.version,
        "timestamp": chrono::Utc::now().timestamp(),
    }))
}

fn fibonacci(n: usize) -> usize {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn is_prime(n: usize) -> bool {
    if n < 2 {
        return false;
    }
    for i in 2..((n as f64).sqrt() as usize) + 1 {
        if n % i == 0 {
            return false;
        }
    }
    true
}

async fn compute(
    State(state): State<Arc<AppState>>,
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> impl IntoResponse {
    let n = params
        .get("n")
        .and_then(|v| v.parse::<usize>().ok())
        .unwrap_or(30)
        .min(35)
        .max(1);

    let start = Instant::now();
    let fib = fibonacci(n);
    let primes: Vec<_> = (2..n * 10).filter(|&i| is_prime(i)).take(100).collect();
    let elapsed = start.elapsed();

    Json(serde_json::json!({
        "operation": "compute",
        "fibonacci_input": n,
        "fibonacci_value": fib,
        "primes_count": primes.len(),
        "execution_time_ns": elapsed.as_nanos(),
        "service": state.service_name,
    }))
}

async fn echo(body: String) -> impl IntoResponse {
    Json(serde_json::json!({
        "original_length": body.len(),
        "uppercase": body.to_uppercase(),
        "lowercase": body.to_lowercase(),
        "service": "echo",
    }))
}

async fn index(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let html = format!(r#"<!DOCTYPE html>
<html>
<head>
    <title>{}</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #4caf50; }}
        .card {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 10px 0; }}
        a {{ color: #4caf50; }}
    </style>
</head>
<body>
    <h1>{}</h1>
    <div class="card">
        <p>Version: {}</p>
        <p>Protocol: HTTP</p>
        <p>Language: Rust (Axum)</p>
    </div>
    <div class="card">
        <h3>Endpoints</h3>
        <ul>
            <li><a href="/health">/health</a> - Health check</li>
            <li><a href="/api/hello">/api/hello</a> - JSON greeting</li>
            <li><a href="/api/compute">/api/compute</a> - CPU benchmark</li>
            <li>POST /api/echo - Echo body</li>
        </ul>
    </div>
</body>
</html>"#, state.service_name, state.service_name, state.version);
    Html(html)
}

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_target(false)
        .init();

    let service_name = env::var("SERVICE_NAME")
        .unwrap_or_else(|_| "{{PROJECT_NAME}}".to_string());
    let version = "0.1.0";

    let state = Arc::new(AppState {
        service_name: service_name.clone(),
        version: version.to_string(),
    });

    let app = Router::new()
        .route("/", get(index))
        .route("/health", get(health))
        .route("/api/hello", get(hello))
        .route("/api/compute", get(compute))
        .route("/api/echo", post(echo))
        .with_state(state);

    let port = env::var("PORT")
        .unwrap_or_else(|_| "3001".to_string())
        .parse::<u16>()
        .unwrap_or(3001);

    let addr = format!("0.0.0.0:{}", port);
    println!("Starting {} (HTTP) on port {}", service_name, port);

    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
