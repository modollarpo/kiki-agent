-- Migration: 002_add_creative_tracking
-- Description: Add creative generation tracking for SyncCreate service
-- Date: 2026-01-20
-- Author: KIKI Platform Team

-- Migration Up
BEGIN;

-- Creative assets table
CREATE TABLE creative_assets (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    asset_id VARCHAR(64) UNIQUE NOT NULL,
    campaign_id VARCHAR(64) NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    
    -- Asset details
    asset_type VARCHAR(32) NOT NULL, -- 'image', 'video', 'carousel'
    platform VARCHAR(32) NOT NULL,   -- 'tiktok', 'meta', 'google'
    format VARCHAR(32) NOT NULL,     -- 'tiktok_9_16', 'meta_square', etc.
    
    -- Generation metadata
    prompt TEXT NOT NULL,
    model_version VARCHAR(64),
    generation_time_ms INT,
    
    -- Brand compliance
    brand_name VARCHAR(128),
    brand_colors TEXT[],
    tone_of_voice VARCHAR(64),
    compliance_score NUMERIC(5, 4), -- 0.0 to 1.0
    safety_score NUMERIC(5, 4),     -- Content safety score
    
    -- Storage
    storage_url TEXT NOT NULL,
    cdn_url TEXT,
    file_size_bytes BIGINT,
    dimensions VARCHAR(32),          -- e.g., '1080x1920'
    
    -- Performance tracking
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions BIGINT DEFAULT 0,
    ctr NUMERIC(6, 4),               -- Click-through rate
    cvr NUMERIC(6, 4),               -- Conversion rate
    
    -- A/B testing
    variant_group VARCHAR(64),
    variant_id VARCHAR(32),
    
    -- Lifecycle
    status VARCHAR(32) NOT NULL DEFAULT 'draft', -- 'draft', 'approved', 'active', 'paused', 'archived'
    approved_by VARCHAR(64),
    approved_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB,
    
    -- Soft delete
    deleted_at TIMESTAMPTZ
);

-- Convert to hypertable (time-series optimization)
SELECT create_hypertable('creative_assets', 'created_at', if_not_exists => TRUE);

-- Indexes
CREATE INDEX idx_creative_campaign ON creative_assets (campaign_id, created_at DESC);
CREATE INDEX idx_creative_customer ON creative_assets (customer_id, created_at DESC);
CREATE INDEX idx_creative_platform ON creative_assets (platform, status, created_at DESC);
CREATE INDEX idx_creative_variant ON creative_assets (variant_group, variant_id);
CREATE INDEX idx_creative_status ON creative_assets (status, created_at DESC);
CREATE INDEX idx_creative_metadata ON creative_assets USING GIN (metadata);

-- A/B test performance view
CREATE OR REPLACE VIEW creative_ab_performance AS
SELECT
    variant_group,
    variant_id,
    platform,
    COUNT(*) AS total_assets,
    SUM(impressions) AS total_impressions,
    SUM(clicks) AS total_clicks,
    SUM(conversions) AS total_conversions,
    ROUND(SUM(clicks)::NUMERIC / NULLIF(SUM(impressions), 0) * 100, 4) AS avg_ctr,
    ROUND(SUM(conversions)::NUMERIC / NULLIF(SUM(clicks), 0) * 100, 4) AS avg_cvr,
    AVG(compliance_score) AS avg_compliance,
    AVG(safety_score) AS avg_safety
FROM creative_assets
WHERE status = 'active'
  AND deleted_at IS NULL
  AND variant_group IS NOT NULL
GROUP BY variant_group, variant_id, platform;

COMMIT;

-- Migration Down
BEGIN;

DROP VIEW IF EXISTS creative_ab_performance;
DROP TABLE IF EXISTS creative_assets CASCADE;

COMMIT;
