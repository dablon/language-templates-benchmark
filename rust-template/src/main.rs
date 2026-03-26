//! Rust Web Service Template
//!
//! A high-performance web service template using Axum framework.
//! Designed for benchmarking across multiple programming languages.

mod config;
mod constants;
mod error;
mod models;
mod routes;

use axum::{Router, Server};
use std::net::SocketAddr;
use tower_http::trace::TraceLayer;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

pub use config::Config;
pub use error::AppError;

/// Initialize the tracing subscriber for logging
fn init_tracing() {
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_target(true)
        .with_thread_ids(true)
        .finish();

    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");
}

/// Create and configure the Axum application
fn create_app(config: &Config) -> Router {
    Router::new()
        .nest("/", routes::web::routes())
        .nest("/api", routes::api::routes())
        .route("/health", axum::routing::get(routes::health::handler))
        .with_state(config.clone())
        .layer(TraceLayer::new_for_http())
}

#[tokio::main]
async fn main() {
    init_tracing();

    let config = Config::from_env();

    info!(
        "Starting {} v{} on port {}",
        constants::SERVICE_NAME,
        constants::VERSION,
        config.port
    );

    let addr = SocketAddr::from(([0, 0, 0, 0], config.port));
    let app = create_app(&config);

    info!("Server listening on {}", addr);

    Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .expect("server failed");
}
