//! Health check endpoint
//!
//! Provides a simple health check endpoint for load balancers and monitoring.

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use std::sync::Arc;

use crate::config::Config;
use crate::constants;
use crate::models::response::HealthResponse;

/// Health check handler
///
/// Returns a JSON response indicating service health.
pub async fn handler(
    State(config): State<Arc<Config>>,
) -> impl IntoResponse {
    let response = HealthResponse::healthy_with_version(
        constants::SERVICE_NAME,
        constants::VERSION,
    );

    (StatusCode::OK, Json(response))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_health_returns_200() {
        let config = Arc::new(Config::default());
        let response = handler(State(config)).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);
    }
}
