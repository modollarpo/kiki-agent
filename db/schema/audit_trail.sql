-- KIKI Agent™ Immutable Audit Trail
-- [I] from A-Z Roadmap - ISO 27001 Compliance
-- PostgreSQL + TimescaleDB for time-series optimization

-- Enable TimescaleDB extension (if available)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,
    
    -- Temporal metadata
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(64) NOT NULL,
    
    -- Customer context
    customer_id VARCHAR(64) NOT NULL,
    campaign_id VARCHAR(64),
    
    -- LTV prediction (from SyncValue™ AI Brain)
    predicted_ltv NUMERIC(12, 2),
    confidence NUMERIC(5, 4),
    ltv_lower_bound NUMERIC(12, 2),
    ltv_upper_bound NUMERIC(12, 2),
    model_version VARCHAR(32),
    
    -- Bid execution (from SyncFlow™ Execution Layer)
    bid_amount NUMERIC(12, 2) NOT NULL,
    bid_source VARCHAR(32) NOT NULL, -- 'AI_PREDICTION' | 'HEURISTIC_FALLBACK' | 'MANUAL_OVERRIDE'
    platform VARCHAR(32) NOT NULL,   -- 'google_ads' | 'meta' | 'tiktok' | etc.
    platform_bid_id VARCHAR(128),    -- Platform-assigned bid ID
    
    -- Outcome tracking
    bid_status VARCHAR(32) NOT NULL, -- 'ACCEPTED' | 'REJECTED' | 'FAILED' | 'BUDGET_EXCEEDED'
    circuit_state VARCHAR(16),       -- 'CLOSED' | 'OPEN' | 'HALF_OPEN'
    used_fallback BOOLEAN DEFAULT FALSE,
    
    -- Actual LTV (populated later via ingestion)
    actual_ltv NUMERIC(12, 2),
    actual_ltv_timestamp TIMESTAMPTZ,
    ltv_error_pct NUMERIC(5, 2),     -- (actual - predicted) / predicted * 100
    
    -- Performance metrics
    execution_time_ms INT,
    inference_time_us INT,
    
    -- Budget tracking
    campaign_budget NUMERIC(12, 2),
    current_spend NUMERIC(12, 2),
    remaining_budget NUMERIC(12, 2),
    
    -- Metadata (JSON for flexibility)
    metadata JSONB,
    
    -- Explanation (for AI transparency)
    explanation TEXT,
    
    -- Audit trail integrity
    created_by VARCHAR(64) DEFAULT 'syncflow',
    immutable BOOLEAN DEFAULT TRUE   -- Rows cannot be updated (only appended)
);

-- Convert to hypertable (TimescaleDB optimization for time-series data)
SELECT create_hypertable('audit_log', 'timestamp', if_not_exists => TRUE);

-- Indexes for fast queries
CREATE INDEX idx_audit_timestamp ON audit_log (timestamp DESC);
CREATE INDEX idx_audit_customer ON audit_log (customer_id, timestamp DESC);
CREATE INDEX idx_audit_campaign ON audit_log (campaign_id, timestamp DESC);
CREATE INDEX idx_audit_platform ON audit_log (platform, timestamp DESC);
CREATE INDEX idx_audit_bid_source ON audit_log (bid_source, timestamp DESC);
CREATE INDEX idx_audit_request_id ON audit_log (request_id);
CREATE INDEX idx_audit_metadata ON audit_log USING GIN (metadata);

-- Composite index for accuracy reporting
CREATE INDEX idx_audit_accuracy ON audit_log (platform, timestamp DESC) 
    WHERE actual_ltv IS NOT NULL AND predicted_ltv IS NOT NULL;

-- Trigger to enforce immutability (prevent UPDATEs)
CREATE OR REPLACE FUNCTION enforce_immutability()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.immutable = TRUE THEN
        RAISE EXCEPTION 'Cannot modify immutable audit log entry (id=%)', OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_immutability
    BEFORE UPDATE ON audit_log
    FOR EACH ROW
    EXECUTE FUNCTION enforce_immutability();

-- View: Real-time accuracy tracking (LTV Momentum Dashboard)
CREATE OR REPLACE VIEW ltv_accuracy_realtime AS
SELECT
    platform,
    COUNT(*) AS total_predictions,
    COUNT(*) FILTER (WHERE actual_ltv IS NOT NULL) AS verified_predictions,
    AVG(ltv_error_pct) AS avg_error_pct,
    STDDEV(ltv_error_pct) AS stddev_error_pct,
    COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10) AS within_tolerance,
    ROUND(
        COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10)::NUMERIC / 
        NULLIF(COUNT(*) FILTER (WHERE actual_ltv IS NOT NULL), 0) * 100, 
        2
    ) AS accuracy_pct,
    MAX(timestamp) AS last_prediction
FROM audit_log
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY platform
ORDER BY accuracy_pct DESC;

-- View: Circuit breaker performance
CREATE OR REPLACE VIEW circuit_breaker_stats AS
SELECT
    platform,
    circuit_state,
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE bid_status = 'ACCEPTED') AS successful_bids,
    COUNT(*) FILTER (WHERE used_fallback = TRUE) AS fallback_activations,
    AVG(execution_time_ms) AS avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) AS p95_latency_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms) AS p99_latency_ms
FROM audit_log
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY platform, circuit_state;

-- View: Budget utilization (Sliding Window)
CREATE OR REPLACE VIEW budget_utilization AS
SELECT
    campaign_id,
    platform,
    SUM(bid_amount) AS total_spend,
    MAX(campaign_budget) AS campaign_budget,
    MAX(campaign_budget) - SUM(bid_amount) AS remaining_budget,
    COUNT(*) AS total_bids,
    COUNT(*) FILTER (WHERE bid_status = 'ACCEPTED') AS successful_bids,
    COUNT(*) FILTER (WHERE bid_status = 'BUDGET_EXCEEDED') AS budget_rejections,
    MIN(timestamp) AS window_start,
    MAX(timestamp) AS window_end
FROM audit_log
WHERE timestamp >= NOW() - INTERVAL '10 minutes'
GROUP BY campaign_id, platform;

-- Retention policy (auto-delete after 7 years for GDPR compliance)
SELECT add_retention_policy('audit_log', INTERVAL '7 years', if_not_exists => TRUE);

-- Continuous aggregate for daily accuracy (pre-computed materialized view)
CREATE MATERIALIZED VIEW ltv_accuracy_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS day,
    platform,
    COUNT(*) AS total_predictions,
    AVG(ltv_error_pct) AS avg_error_pct,
    COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10) AS within_tolerance,
    ROUND(
        COUNT(*) FILTER (WHERE ABS(ltv_error_pct) <= 10)::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) AS accuracy_pct
FROM audit_log
WHERE actual_ltv IS NOT NULL
GROUP BY day, platform;

-- Refresh policy (update materialized view every hour)
SELECT add_continuous_aggregate_policy('ltv_accuracy_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Sample queries for compliance reports

-- 1. Get all bids for a customer (GDPR data export)
-- SELECT * FROM audit_log WHERE customer_id = 'cust_123' ORDER BY timestamp DESC;

-- 2. Check accuracy for last 24 hours
-- SELECT * FROM ltv_accuracy_realtime;

-- 3. Find all fallback activations in last hour
-- SELECT * FROM audit_log 
-- WHERE used_fallback = TRUE AND timestamp >= NOW() - INTERVAL '1 hour'
-- ORDER BY timestamp DESC;

-- 4. Budget exceeded events
-- SELECT customer_id, campaign_id, bid_amount, timestamp
-- FROM audit_log
-- WHERE bid_status = 'BUDGET_EXCEEDED'
-- AND timestamp >= NOW() - INTERVAL '24 hours';

-- 5. Platform-specific accuracy
-- SELECT platform, accuracy_pct FROM ltv_accuracy_realtime;
