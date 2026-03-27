//! Database module for PostgreSQL operations

use sqlx::{postgres::PgPoolOptions, Pool, Postgres};
use std::sync::Arc;
use std::time::Duration;

pub type DbPool = Pool<Postgres>;

/// Initialize database connection pool
pub async fn init_db(database_url: &str) -> Result<DbPool, sqlx::Error> {
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .acquire_timeout(Duration::from_secs(5))
        .connect(database_url)
        .await?;

    Ok(pool)
}

/// Benchmark record model
#[derive(Debug, serde::Serialize, serde::Deserialize, sqlx::FromRow)]
pub struct BenchmarkRecord {
    pub id: i32,
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

/// Create new record request
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct CreateRecordRequest {
    pub name: String,
    pub description: Option<String>,
    pub value: i32,
}

/// Update record request
#[derive(Debug, serde::Serialize, serde::Deserialize)]
pub struct UpdateRecordRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub value: Option<i32>,
}

/// Get all records
pub async fn get_all_records(pool: &DbPool) -> Result<Vec<BenchmarkRecord>, sqlx::Error> {
    let records = sqlx::query_as::<_, BenchmarkRecord>(
        "SELECT id, name, description, value, created_at, updated_at FROM benchmark_records ORDER BY id"
    )
    .fetch_all(pool)
    .await?;

    Ok(records)
}

/// Get record by ID
pub async fn get_record_by_id(pool: &DbPool, id: i32) -> Result<Option<BenchmarkRecord>, sqlx::Error> {
    let record = sqlx::query_as::<_, BenchmarkRecord>(
        "SELECT id, name, description, value, created_at, updated_at FROM benchmark_records WHERE id = $1"
    )
    .bind(id)
    .fetch_optional(pool)
    .await?;

    Ok(record)
}

/// Create a new record
pub async fn create_record(
    pool: &DbPool,
    name: &str,
    description: Option<&str>,
    value: i32,
) -> Result<BenchmarkRecord, sqlx::Error> {
    let record = sqlx::query_as::<_, BenchmarkRecord>(
        "INSERT INTO benchmark_records (name, description, value) VALUES ($1, $2, $3)
         RETURNING id, name, description, value, created_at, updated_at"
    )
    .bind(name)
    .bind(description)
    .bind(value)
    .fetch_one(pool)
    .await?;

    Ok(record)
}

/// Update an existing record
pub async fn update_record(
    pool: &DbPool,
    id: i32,
    name: Option<&str>,
    description: Option<&str>,
    value: Option<i32>,
) -> Result<Option<BenchmarkRecord>, sqlx::Error> {
    let record = sqlx::query_as::<_, BenchmarkRecord>(
        "UPDATE benchmark_records SET name = COALESCE($1, name), description = COALESCE($2, description), value = COALESCE($3, value), updated_at = CURRENT_TIMESTAMP WHERE id = $4 RETURNING id, name, description, value, created_at, updated_at"
    )
    .bind(name)
    .bind(description)
    .bind(value)
    .bind(id)
    .fetch_optional(pool)
    .await?;

    Ok(record)
}

/// Delete a record
pub async fn delete_record(pool: &DbPool, id: i32) -> Result<bool, sqlx::Error> {
    let result = sqlx::query("DELETE FROM benchmark_records WHERE id = $1")
        .bind(id)
        .execute(pool)
        .await?;

    Ok(result.rows_affected() > 0)
}
