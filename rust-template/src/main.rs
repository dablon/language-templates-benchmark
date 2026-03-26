use axum::{
    body::Body,
    extract::State,
    http::{Method, StatusCode},
    response::{Html, IntoResponse, Response},
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tower_http::trace::TraceLayer;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

#[derive(Clone)]
struct AppState {
    name: String,
    version: String,
}

async fn health() -> impl IntoResponse {
    let health = serde_json::json!({
        "status": "healthy",
        "service": "rust-template"
    });
    (StatusCode::OK, axum::Json(health))
}

async fn hello(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let response = serde_json::json!({
        "message": "Hello from Rust!",
        "service": state.name,
        "version": state.version
    });
    (StatusCode::OK, axum::Json(response))
}

async fn echo(body: String) -> impl IntoResponse {
    (StatusCode::OK, body)
}

async fn index() -> Html<&'static str> {
    Html(std::include_str!("../index.html"))
}

fn create_app() -> Router {
    let state = Arc::new(AppState {
        name: "rust-template".to_string(),
        version: "0.1.0".to_string(),
    });

    Router::new()
        .route("/", get(index))
        .route("/health", get(health))
        .route("/api/hello", get(hello))
        .route("/api/echo", post(echo))
        .with_state(state)
        .layer(TraceLayer::new_for_http())
}

#[tokio::main]
async fn main() {
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");

    let app = create_app();

    let addr = SocketAddr::from(([0, 0, 0, 0], 3001));
    info!("Rust template listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
