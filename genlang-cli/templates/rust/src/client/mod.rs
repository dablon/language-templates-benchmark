//! Client module for inter-service communication

pub mod rest;

pub use rest::{RestClient, ServiceEndpoint, ServiceResponse};