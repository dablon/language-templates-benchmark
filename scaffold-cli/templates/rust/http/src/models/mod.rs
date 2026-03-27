//! Models module - Data structures

use serde::{Deserialize, Serialize};

/// Application state shared across handlers
#[derive(Clone, Debug)]
pub struct AppState {
    pub service_name: String,
    pub version: String,
}

/// Health check response
#[derive(Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    #[serde(rename = "service")]
    pub service_name: String,
    pub version: String,
}

/// Hello endpoint response
#[derive(Serialize, Deserialize)]
pub struct HelloResponse {
    pub message: String,
    #[serde(rename = "service")]
    pub service_name: String,
    pub version: String,
}

/// Compute benchmark response
#[derive(Serialize, Deserialize)]
pub struct ComputeResponse {
    pub operation: String,
    #[serde(rename = "fibonacci_input")]
    pub fib_input: usize,
    #[serde(rename = "fibonacci_value")]
    pub fib_value: usize,
    #[serde(rename = "primes_count")]
    pub primes_count: usize,
    #[serde(rename = "execution_time_ns")]
    pub exec_time_ns: u64,
    #[serde(rename = "service")]
    pub service_name: String,
}

/// Echo response
#[derive(Serialize, Deserialize)]
pub struct EchoResponse {
    #[serde(rename = "original_length")]
    pub orig_len: usize,
    pub uppercase: String,
    pub lowercase: String,
    #[serde(rename = "service")]
    pub service_name: String,
}