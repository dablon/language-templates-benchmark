//! Integration tests for Rust web service template

use rust_template::{config::Config, routes, create_app};
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use tower::ServiceExt;

/// Create a test app instance
fn test_app() -> axum::Router {
    let config = Config::default();
    create_app(&config)
}

#[tokio::test]
async fn test_health_endpoint() {
    let app = test_app();

    let response = app
        .oneshot(Request::builder()
            .uri("/health")
            .body(Body::empty())
            .unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_index_endpoint() {
    let app = test_app();

    let response = app
        .oneshot(Request::builder()
            .uri("/")
            .body(Body::empty())
            .unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_api_hello_endpoint() {
    let app = test_app();

    let response = app
        .oneshot(Request::builder()
            .uri("/api/hello")
            .body(Body::empty())
            .unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_not_found() {
    let app = test_app();

    let response = app
        .oneshot(Request::builder()
            .uri("/nonexistent")
            .body(Body::empty())
            .unwrap())
        .await
        .unwrap();

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}
