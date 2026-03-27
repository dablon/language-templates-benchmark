//! Services module - Business logic

use crate::models::{ComputeResponse, EchoResponse};

/// Compute service - CPU-intensive benchmark operations
pub struct ComputeService;

impl ComputeService {
    /// Execute CPU benchmark: fibonacci + prime calculation
    pub fn execute(n: usize, service_name: &str) -> ComputeResponse {
        let n_capped = n.min(35).max(1);

        let start = std::time::Instant::now();
        let fib_value = fibonacci(n_capped);
        let primes_count = count_primes(n_capped);
        let elapsed = start.elapsed();

        ComputeResponse {
            operation: "compute".to_string(),
            fib_input: n_capped,
            fib_value,
            primes_count,
            exec_time_ns: elapsed.as_nanos() as u64,
            service_name: service_name.to_string(),
        }
    }
}

/// Echo service - Data transformation
pub struct EchoService;

impl EchoService {
    /// Process and transform request body
    pub fn process(body: String, service_name: &str) -> EchoResponse {
        EchoResponse {
            orig_len: body.len(),
            uppercase: body.to_uppercase(),
            lowercase: body.to_lowercase(),
            service_name: service_name.to_string(),
        }
    }
}

// Private helper functions
fn fibonacci(n: usize) -> usize {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn count_primes(n: usize) -> usize {
    (2..n * 10).filter(|&i| is_prime(i)).take(100).count()
}

fn is_prime(n: usize) -> bool {
    if n < 2 {
        return false;
    }
    for i in 2..((n as f64).sqrt() as usize) + 1 {
        if n % i == 0 {
            return false;
        }
    }
    true
}