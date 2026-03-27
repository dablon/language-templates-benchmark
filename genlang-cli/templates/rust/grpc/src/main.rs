//! Rust HTTP Web Service - Main Entry Point
//! Clean architecture: src/{handlers,services,models}

mod handlers;
mod models;
mod services;

use models::AppState;
use handlers::create_router;
use std::sync::Arc;
use std::env;
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_target(false)
        .init();

    // Get configuration from environment
    let service_name = env::var("SERVICE_NAME")
        .unwrap_or_else(|_| "{{PROJECT_NAME}}".to_string());
    let version = env::var("VERSION").unwrap_or_else(|_| "0.1.0".to_string());

    let state = Arc::new(AppState {
        service_name: service_name.clone(),
        version: version.clone(),
    });

    // Create router
    let app = create_router(state);

    // Server configuration
    let port = env::var("PORT")
        .unwrap_or_else(|_| "3001".to_string())
        .parse::<u16>()
        .unwrap_or(3001);

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    println!("Starting {} (HTTP) on port {}", service_name, port);

    // Start server
    let listener = tokio::net::TcpListener::bind(&addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}