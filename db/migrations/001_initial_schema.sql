-- Migration: 001_initial_schema
-- Description: Create initial audit_log table with TimescaleDB hypertable
-- Date: 2026-01-20
-- Author: KIKI Platform Team

-- Migration Up
BEGIN;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main audit log table
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(64) NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    campaign_id VARCHAR(64),
    predicted_ltv NUMERIC(12, 2),
    confidence NUMERIC(5, 4),
    ltv_lower_bound NUMERIC(12, 2),
    ltv_upper_bound NUMERIC(12, 2),
    model_version VARCHAR(32),
    bid_amount NUMERIC(12, 2) NOT NULL,
    bid_source VARCHAR(32) NOT NULL,
    platform VARCHAR(32) NOT NULL,
    platform_bid_id VARCHAR(128),
    bid_status VARCHAR(32) NOT NULL,
    circuit_state VARCHAR(16),
    used_fallback BOOLEAN DEFAULT FALSE,
    actual_ltv NUMERIC(12, 2),
    actual_ltv_timestamp TIMESTAMPTZ,
    ltv_error_pct NUMERIC(5, 2),
    execution_time_ms INT,
    inference_time_us INT,
    campaign_budget NUMERIC(12, 2),
    current_spend NUMERIC(12, 2),
    remaining_budget NUMERIC(12, 2),
    metadata JSONB,
    explanation TEXT,
    created_by VARCHAR(64) DEFAULT 'syncflow',
    immutable BOOLEAN DEFAULT TRUE
);

-- Convert to hypertable
SELECT create_hypertable('audit_log', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX idx_audit_customer ON audit_log (customer_id, timestamp DESC);
CREATE INDEX idx_audit_campaign ON audit_log (campaign_id, timestamp DESC);
CREATE INDEX idx_audit_platform ON audit_log (platform, timestamp DESC);
CREATE INDEX idx_audit_request_id ON audit_log (request_id);

COMMIT;

-- Migration Down
BEGIN;

DROP TABLE IF EXISTS audit_log CASCADE;

COMMIT;
