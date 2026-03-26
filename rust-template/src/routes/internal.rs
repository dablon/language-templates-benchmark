//! Service-to-service communication endpoints
//!
//! Endpoints that allow other services to call this service.

use axum::{
    extract::State,
    response::IntoResponse,
    Json,
    Router,
};
use std::sync::Arc;
use std::time::Instant;

use crate::client::RestClient;
use crate::config::Config;
use crate::constants;
use crate::models::response::HelloResponse;

/// Create service communication routes
pub fn routes() -> Router<Arc<Config>> {
    Router::new()
        .route("/aggregate", axum::routing::get(aggregate_handler))
        .route("/chain", axum::routing::post(chain_handler))
        .with_state(Arc::new(Config::default()))
}

/// GET /internal/aggregate
///
/// Call all other services and aggregate responses.
pub async fn aggregate_handler(
    State(config): State<Arc<Config>>,
) -> impl IntoResponse {
    let client = RestClient::new();
    let start = Instant::now();

    let results = client.call_all_services("/api/hello").await;
    let total_time_ms = start.elapsed().as_millis() as u64;

    Json(serde_json::json!({
        "caller": constants::SERVICE_NAME,
        "results": results,
        "total_time_ms": total_time_ms,
    }))
}

/// POST /internal/chain
///
/// Chain: call next service and pass result.
pub async fn chain_handler(
    body: String,
) -> impl IntoResponse {
    // Simple echo for now - chain logic would be implemented in gateway
    Json(serde_json::json!({
        "service": constants::SERVICE_NAME,
        "received": body,
        "next_hop": "go-template",
    }))
}