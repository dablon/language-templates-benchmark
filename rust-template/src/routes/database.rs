//! Database CRUD routes

use crate::database::{self, BenchmarkRecord, CreateRecordRequest, DbPool, UpdateRecordRequest};
use axum::{
    extract::State,
    routing::{delete, get, post, put},
    Json, Router,
};
use serde_json::{json, Value};
use std::sync::Arc;

/// Create database router
pub fn create_db_router(pool: DbPool) -> Router {
    Router::new()
        .route("/db/records", get(get_records))
        .route("/db/records", post(create_record))
        .route("/db/records/:id", get(get_record))
        .route("/db/records/:id", put(update_record))
        .route("/db/records/:id", delete(delete_record))
        .with_state(pool)
}

/// Get all records
async fn get_records(State(pool): State<Arc<database::DbPool>>) -> Result<Json<Vec<BenchmarkRecord>>, (axum::http::StatusCode, Json<Value>)> {
    database::get_all_records(&pool)
        .await
        .map_err(|e| (axum::http::StatusCode::INTERNAL_SERVER_ERROR, json!({"error": format!("Database error: {}", e)})))
        .map(Json)
}

/// Get record by ID
async fn get_record(
    State(pool): State<Arc<database::DbPool>>,
    axum::extract::Path(id): axum::extract::Path<i32>,
) -> Result<Json<Option<BenchmarkRecord>>, (axum::http::StatusCode, Json<Value>)> {
    database::get_record_by_id(&pool, id)
        .await
        .map_err(|e| (axum::http::StatusCode::INTERNAL_SERVER_ERROR, json!({"error": format!("Database error: {}", e)})))
        .map(Json)
}

/// Create a new record
async fn create_record(
    State(pool): State<Arc<database::DbPool>>,
    Json(payload): Json<CreateRecordRequest>,
) -> Result<Json<BenchmarkRecord>, (axum::http::StatusCode, Json<Value>)> {
    database::create_record(
        &pool,
        &payload.name,
        payload.description.as_deref(),
        payload.value,
    )
    .await
    .map_err(|e| (axum::http::StatusCode::INTERNAL_SERVER_ERROR, json!({"error": format!("Database error: {}", e)})))
    .map(Json)
}

/// Update an existing record
async fn update_record(
    State(pool): State<Arc<database::DbPool>>,
    axum::extract::Path(id): axum::extract::Path<i32>,
    Json(payload): Json<UpdateRecordRequest>,
) -> Result<Json<BenchmarkRecord>, (axum::http::StatusCode, Json<Value>)> {
    database::update_record(
        &pool,
        id,
        payload.name.as_deref(),
        payload.description.as_deref(),
        payload.value,
    )
    .await
    .map_err(|e| (axum::http::StatusCode::INTERNAL_SERVER_ERROR, json!({"error": format!("Database error: {}", e)})))
    .and_then(|opt| {
        match opt {
            Some(r) => Ok(Json(r)),
            None => Err((axum::http::StatusCode::NOT_FOUND, json!({"error": format!("Record {} not found", id)})))
        }
    })
}

/// Delete a record
async fn delete_record(
    State(pool): State<Arc<database::DbPool>>,
    axum::extract::Path(id): axum::extract::Path<i32>,
) -> Result<Json<serde_json::Value>, (axum::http::StatusCode, Json<Value>)> {
    database::delete_record(&pool, id)
        .await
        .map_err(|e| (axum::http::StatusCode::INTERNAL_SERVER_ERROR, json!({"error": format!("Database error: {}", e)})))
        .and_then(|deleted| {
            if deleted {
                Ok(json!({"success": true, "deleted": id}))
            } else {
                Err((axum::http::StatusCode::NOT_FOUND, json!({"error": format!("Record {} not found", id)})))
            }
        })
}
