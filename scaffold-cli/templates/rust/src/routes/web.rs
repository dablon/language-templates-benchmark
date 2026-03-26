//! Web endpoints
//!
//! HTML web endpoints that serve static content.

use axum::{
    response::{Html, IntoResponse},
    Router,
};

/// Create web routes
pub fn routes() -> Router {
    Router::new()
        .route("/", axum::routing::get(index_handler))
}

/// GET /
///
/// Serves the main HTML page.
pub async fn index_handler() -> impl IntoResponse {
    // Serve the static HTML file
    Html(include_str!("../../static/index.html"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_index_returns_html() {
        let response = index_handler().await.into_response();
        assert_eq!(response.status(), axum::http::StatusCode::OK);
    }
}
