use std::time::Instant;

pub mod proto {
    tonic::include_proto!("benchmark");
}

use proto::benchmark::{
    benchmark_server::{Benchmark, BenchmarkServer},
    ComputeRequest, ComputeResponse, EchoRequest, EchoResponse,
    HealthRequest, HealthResponse, HelloRequest, HelloResponse,
};
use tonic::{Request, Response, Status};

#[derive(Default)]
pub struct BenchmarkService {
    start_time: Instant,
}

#[tonic::async_trait]
impl Benchmark for BenchmarkService {
    async fn health(
        &self,
        _request: Request<HealthRequest>,
    ) -> Result<Response<HealthResponse>, Status> {
        Ok(Response::new(HealthResponse {
            service: "{{PROJECT_NAME}}".to_string(),
            status: "healthy".to_string(),
            version: "0.1.0".to_string(),
            uptime_ns: self.start_time.elapsed().as_nanos() as i64,
            timestamp: chrono::Utc::now().timestamp(),
        }))
    }

    async fn hello(
        &self,
        _request: Request<HelloRequest>,
    ) -> Result<Response<HelloResponse>, Status> {
        Ok(Response::new(HelloResponse {
            service: "{{PROJECT_NAME}}".to_string(),
            message: format!("Hello from {} (gRPC)!", "{{PROJECT_NAME}}"),
            version: "0.1.0".to_string(),
            timestamp: chrono::Utc::now().timestamp(),
        }))
    }

    async fn compute(
        &self,
        request: Request<ComputeRequest>,
    ) -> Result<Response<ComputeResponse>, Status> {
        let n = request.into_inner().n as usize;
        let n = n.min(35).max(1);

        let start = Instant::now();
        let fib = fibonacci(n);
        let primes = compute_primes(n * 10);
        let elapsed = start.elapsed();

        Ok(Response::new(ComputeResponse {
            operation: "compute".to_string(),
            fibonacci_input: n as i64,
            fibonacci_value: fib as i64,
            primes_count: primes.len() as i64,
            execution_time_ns: elapsed.as_nanos() as i64,
            service: "{{PROJECT_NAME}}".to_string(),
        }))
    }

    async fn echo(
        &self,
        request: Request<EchoRequest>,
    ) -> Result<Response<EchoResponse>, Status> {
        let body = request.into_inner().body;
        Ok(Response::new(EchoResponse {
            original_length: body.len() as i64,
            uppercase: body.to_uppercase(),
            lowercase: body.to_lowercase(),
            service: "{{PROJECT_NAME}}".to_string(),
        }))
    }
}

fn fibonacci(n: usize) -> usize {
    if n <= 1 {
        return n;
    }
    fibonacci(n - 1) + fibonacci(n - 2)
}

fn compute_primes(max: usize) -> Vec<usize> {
    let mut primes = Vec::new();
    for i in 2..max {
        if is_prime(i) {
            primes.push(i);
            if primes.len() >= 100 {
                break;
            }
        }
    }
    primes
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

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();

    let addr = "[::]:3001".parse()?;
    let service = BenchmarkService::default();

    tracing::info!("Starting {{PROJECT_NAME}} (gRPC) on port 3001");

    tonic::build()
        .serve(addr)
        .await?;

    Ok(())
}
