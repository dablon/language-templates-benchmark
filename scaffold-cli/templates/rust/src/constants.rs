//! Application constants

/// Service identifier for this template
pub const SERVICE_NAME: &str = "rust-template";

/// Semantic version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Content types
pub mod content_type {
    pub const HTML: &str = "text/html";
    pub const JSON: &str = "application/json";
    pub const TEXT: &str = "text/plain";
    pub const CSS: &str = "text/css";
    pub const JS: &str = "application/javascript";
}

/// HTTP Methods
pub mod method {
    pub const GET: &str = "GET";
    pub const POST: &str = "POST";
    pub const PUT: &str = "PUT";
    pub const DELETE: &str = "DELETE";
}
