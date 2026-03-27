//! Rust HTTP Web Service Template
//! Clean architecture with src/{handlers,services,models} structure

pub mod handlers;
pub mod models;
pub mod services;

pub const SERVICE_NAME: &str = "{{PROJECT_NAME}}";
pub const VERSION: &str = "0.1.0";