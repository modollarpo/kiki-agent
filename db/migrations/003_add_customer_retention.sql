-- Migration: 003_add_customer_retention
-- Description: Add customer retention tracking for SyncEngage service
-- Date: 2026-01-20
-- Author: KIKI Platform Team

-- Migration Up
BEGIN;

-- Customer retention events table
CREATE TABLE retention_events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Customer context
    customer_id VARCHAR(64) NOT NULL,
    campaign_id VARCHAR(64),
    
    -- Event details
    event_type VARCHAR(64) NOT NULL, -- 'email_sent', 'sms_sent', 'push_sent', 'opened', 'clicked', 'converted', 'unsubscribed'
    channel VARCHAR(32) NOT NULL,    -- 'email', 'sms', 'push', 'in_app'
    
    -- Engagement metadata
    subject_line TEXT,
    content_variant VARCHAR(64),
    personalization_level VARCHAR(32), -- 'none', 'basic', 'advanced', 'ai_generated'
    
    -- Timing
    send_time TIMESTAMPTZ,
    open_time TIMESTAMPTZ,
    click_time TIMESTAMPTZ,
    convert_time TIMESTAMPTZ,
    
    -- Churn prediction (from SyncEngage AI)
    churn_risk NUMERIC(5, 4),        -- 0.0 to 1.0 (probability)
    churn_score VARCHAR(16),         -- 'low', 'medium', 'high', 'critical'
    retention_score NUMERIC(5, 4),   -- 0.0 to 1.0
    
    -- Recommended action
    recommended_action VARCHAR(64),  -- 'nurture', 'discount', 'win_back', 'upsell'
    action_taken BOOLEAN DEFAULT FALSE,
    action_result VARCHAR(32),       -- 'success', 'failed', 'pending'
    
    -- Performance
    response_time_ms INT,
    
    -- Metadata
    metadata JSONB,
    
    -- Attribution
    triggered_by VARCHAR(64) DEFAULT 'synkengage'
);

-- Convert to hypertable
SELECT create_hypertable('retention_events', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX idx_retention_timestamp ON retention_events (timestamp DESC);
CREATE INDEX idx_retention_customer ON retention_events (customer_id, timestamp DESC);
CREATE INDEX idx_retention_campaign ON retention_events (campaign_id, timestamp DESC);
CREATE INDEX idx_retention_event_type ON retention_events (event_type, timestamp DESC);
CREATE INDEX idx_retention_channel ON retention_events (channel, timestamp DESC);
CREATE INDEX idx_retention_churn ON retention_events (churn_score, timestamp DESC);

-- Customer cohort analysis table
CREATE TABLE customer_cohorts (
    cohort_id VARCHAR(64) PRIMARY KEY,
    cohort_name VARCHAR(128) NOT NULL,
    cohort_date DATE NOT NULL,
    
    -- Cohort criteria
    criteria JSONB NOT NULL,
    
    -- Metrics
    initial_size INT NOT NULL,
    current_size INT,
    churned_count INT DEFAULT 0,
    retention_rate NUMERIC(5, 4),
    
    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB
);

CREATE INDEX idx_cohort_date ON customer_cohorts (cohort_date DESC);
CREATE INDEX idx_cohort_retention ON customer_cohorts (retention_rate DESC);

-- View: Real-time churn risk
CREATE OR REPLACE VIEW churn_risk_realtime AS
SELECT
    customer_id,
    MAX(churn_risk) AS current_churn_risk,
    MAX(churn_score) AS churn_category,
    MAX(retention_score) AS retention_score,
    COUNT(*) AS total_interactions,
    COUNT(*) FILTER (WHERE event_type = 'opened') AS opens,
    COUNT(*) FILTER (WHERE event_type = 'clicked') AS clicks,
    COUNT(*) FILTER (WHERE event_type = 'converted') AS conversions,
    MAX(timestamp) AS last_interaction,
    EXTRACT(DAYS FROM NOW() - MAX(timestamp)) AS days_since_interaction
FROM retention_events
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY customer_id
HAVING MAX(churn_risk) >= 0.5 -- High risk threshold
ORDER BY MAX(churn_risk) DESC;

-- View: Channel performance
CREATE OR REPLACE VIEW channel_performance AS
SELECT
    channel,
    DATE_TRUNC('day', timestamp) AS day,
    COUNT(*) FILTER (WHERE event_type LIKE '%_sent') AS sends,
    COUNT(*) FILTER (WHERE event_type = 'opened') AS opens,
    COUNT(*) FILTER (WHERE event_type = 'clicked') AS clicks,
    COUNT(*) FILTER (WHERE event_type = 'converted') AS conversions,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'opened')::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE event_type LIKE '%_sent'), 0) * 100,
        2
    ) AS open_rate,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'clicked')::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE event_type = 'opened'), 0) * 100,
        2
    ) AS ctr,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'converted')::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE event_type = 'clicked'), 0) * 100,
        2
    ) AS cvr
FROM retention_events
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY channel, day
ORDER BY day DESC, channel;

COMMIT;

-- Migration Down
BEGIN;

DROP VIEW IF EXISTS channel_performance;
DROP VIEW IF EXISTS churn_risk_realtime;
DROP TABLE IF EXISTS customer_cohorts CASCADE;
DROP TABLE IF EXISTS retention_events CASCADE;

COMMIT;
