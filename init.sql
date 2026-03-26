-- Benchmark Database Schema
-- Table for CRUD operations benchmarking

-- Create benchmark_records table
CREATE TABLE IF NOT EXISTS benchmark_records (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    value INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO benchmark_records (name, description, value) VALUES
    ('Record 1', 'Sample record for benchmarking', 100),
    ('Record 2', 'Another sample record', 200),
    ('Record 3', 'Third sample record', 300),
    ('Record 4', 'Fourth sample record', 400),
    ('Record 5', 'Fifth sample record', 500)
ON CONFLICT DO NOTHING;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_benchmark_records_name ON benchmark_records(name);
CREATE INDEX IF NOT EXISTS idx_benchmark_records_value ON benchmark_records(value);

-- Create a table for tracking benchmark results
CREATE TABLE IF NOT EXISTS benchmark_results (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    duration_ms INTEGER NOT NULL,
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_benchmark_results_service ON benchmark_results(service_name);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_created ON benchmark_results(created_at);
