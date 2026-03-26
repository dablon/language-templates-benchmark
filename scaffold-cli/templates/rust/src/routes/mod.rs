//! Route handlers module
//!
//! Organized by functionality:
//! - api: REST API endpoints
//! - health: Health check endpoint
//! - web: Web HTML endpoints
//! - internal: Service-to-service communication
//! - database: PostgreSQL CRUD operations

pub mod api;
pub mod database;
pub mod health;
pub mod internal;
pub mod web;
