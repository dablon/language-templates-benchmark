//! Handlers module - HTTP request handlers

use crate::models::{AppState, HealthResponse, HelloResponse};
use crate::services::{ComputeService, EchoService};
use axum::{
    extract::State,
    response::{Html, IntoResponse, Json},
    routing::{get, post},
    Router,
};
use std::sync::Arc;

/// Health check handler
pub async fn health(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    Json(HealthResponse {
        status: "healthy".to_string(),
        service_name: state.service_name.clone(),
        version: state.version.clone(),
    })
}

/// Hello endpoint handler
pub async fn hello(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    Json(HelloResponse {
        message: format!("Hello from {}!", state.service_name),
        service_name: state.service_name.clone(),
        version: state.version.clone(),
    })
}

/// Compute benchmark handler
pub async fn compute(
    State(state): State<Arc<AppState>>,
    axum::extract::Query(params): axum::extract::Query<std::collections::HashMap<String, String>>,
) -> impl IntoResponse {
    let n = params
        .get("n")
        .and_then(|v| v.parse::<usize>().ok())
        .unwrap_or(30)
        .min(35)
        .max(1);

    let result = ComputeService::execute(n, &state.service_name);
    Json(result)
}

/// Echo handler
pub async fn echo(
    State(state): State<Arc<AppState>>,
    body: String,
) -> impl IntoResponse {
    let result = EchoService::process(body, &state.service_name);
    Json(result)
}

/// Web index handler
pub async fn index(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let html = format!(
        r#"<!DOCTYPE html>
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
</html>"#,
        state.service_name, state.service_name, state.version
    );
    Html(html)
}

/// Create and configure the router
pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/", get(index))
        .route("/health", get(health))
        .route("/api/hello", get(hello))
        .route("/api/compute", get(compute))
        .route("/api/echo", post(echo))
        .with_state(state)
}