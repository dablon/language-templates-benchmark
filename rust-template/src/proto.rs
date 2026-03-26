// This file is auto-generated. Do not modify.
// Run: cargo build --features="tonic-build" to regenerate

use prost::Message;

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HelloRequest {
    #[prost(string, tag="1")]
    pub name: ::prost::alloc::string::String,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HelloResponse {
    #[prost(string, tag="1")]
    pub service_name: ::prost::alloc::string::String,
    #[prost(string, tag="2")]
    pub message: ::prost::alloc::string::String,
    #[prost(string, tag="3")]
    pub version: ::prost::alloc::string::String,
    #[prost(int64, tag="4")]
    pub timestamp: i64,
    #[prost(string, tag="5")]
    pub results: ::prost::alloc::vec::Vec<::prost::alloc::string::String>,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HealthRequest {}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct ServiceHealth {
    #[prost(string, tag="1")]
    pub service_name: ::prost::alloc::string::String,
    #[prost(bool, tag="2")]
    pub healthy: bool,
    #[prost(string, tag="3")]
    pub status: ::prost::alloc::string::String,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct HealthResponse {
    #[prost(map="string, bool", tag="1")]
    pub services: ::std::collections::HashMap<::prost::alloc::string::String, bool>,
    #[prost(int64, tag="2")]
    pub timestamp: i64,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct AggregateRequest {
    #[prost(string, tag="1")]
    pub name: ::prost::alloc::string::String,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct ServiceResult {
    #[prost(string, tag="1")]
    pub service: ::prost::alloc::string::String,
    #[prost(string, tag="2")]
    pub message: ::prost::alloc::string::String,
    #[prost(uint64, tag="3")]
    pub elapsed_ms: u64,
    #[prost(bool, tag="4")]
    pub success: bool,
}

#[derive(Clone, PartialEq, ::prost::Message)]
pub struct AggregateResponse {
    #[prost(string, tag="1")]
    pub caller: ::prost::alloc::string::String,
    #[prost(message, tag="2")]
    pub results: ::prost::alloc::vec::Vec<ServiceResult>,
    #[prost(uint64, tag="3")]
    pub total_time_ms: u64,
}

// gRPC service trait
pub mod aggregator_client {
    use tonic::client::GrpcService;
    pub use crate::proto::aggregator_server::Aggregator;
}

pub mod aggregator_server {
    use tonic::transport::NamedService;
    use super::*;

    pub const SERVICE_NAME: &str = "benchmark.Aggregator";

    #[tonic::async_trait]
    pub trait Aggregator: Send + Sync + 'static {
        async fn hello(
            &self,
            request: tonic::Request<HelloRequest>,
        ) -> Result<tonic::Response<HelloResponse>, tonic::Status>;

        async fn health(
            &self,
            request: tonic::Request<HealthRequest>,
        ) -> Result<tonic::Response<HealthResponse>, tonic::Status>;

        async fn aggregate(
            &self,
            request: tonic::Request<AggregateRequest>,
        ) -> Result<tonic::Response<AggregateResponse>, tonic::Status>;
    }

    #[derive(Debug)]
    pub struct AggregatorServer<T: Aggregator> {
        inner: T,
    }

    impl<T: Aggregator> AggregatorServer<T> {
        pub fn new(inner: T) -> Self {
            Self { inner }
        }
    }

    impl<T: Aggregator> tonic::service::Service<tonic::Request<prost::bytes::Bytes>> for AggregatorServer<T> {
        type Response = prost::bytes::Bytes;
        type Error = tonic::Status;
        type Future = futures::future::Ready<Result<Self::Response, Self::Error>>;

        fn poll_ready(&mut self, _cx: &mut core::task::Context<'_>) -> core::task::Poll<Result<(), Self::Error>> {
            core::task::Poll::Ready(Ok(()))
        }

        fn call(&mut self, _req: tonic::Request<prost::bytes::Bytes>) -> Self::Future {
            futures::future::ready(Err(tonic::Status::unimplemented("Not implemented")))
        }
    }

    impl<T: Aggregator> NamedService for AggregatorServer<T> {
        const NAME: &'static str = SERVICE_NAME;
    }
}