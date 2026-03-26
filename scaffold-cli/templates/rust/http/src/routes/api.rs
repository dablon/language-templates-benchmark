//! API endpoints
//!
//! REST API endpoints that return JSON responses.

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
    Router,
};
use std::sync::Arc;

use crate::config::Config;
use crate::constants;
use crate::models::response::HelloResponse;

/// Create API routes
pub fn routes() -> Router<Arc<Config>> {
    Router::new()
        .route("/hello", axum::routing::get(hello_handler))
        .route("/echo", axum::routing::post(echo_handler))
        .with_state(Arc::new(Config::default()))
}

/// GET /api/hello
///
/// Returns a JSON greeting message.
pub async fn hello_handler(
    State(config): State<Arc<Config>>,
) -> impl IntoResponse {
    let response = HelloResponse::new(
        constants::SERVICE_NAME,
        constants::VERSION,
    );

    (StatusCode::OK, Json(response))
}

/// POST /api/echo
///
/// Echoes back the request body.
pub async fn echo_handler(
    body: String,
) -> impl IntoResponse {
    (StatusCode::OK, body)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_hello_returns_json() {
        let config = Arc::new(Config::default());
        let response = hello_handler(State(config)).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);
    }

    #[tokio::test]
    async fn test_echo_returns_body() {
        let body = "test content".to_string();
        let response = echo_handler(body).await.into_response();
        assert_eq!(response.status(), StatusCode::OK);
    }
}
