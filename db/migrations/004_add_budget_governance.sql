-- Migration: 004_add_budget_governance
-- Description: Add real-time budget tracking for SyncShield service
-- Date: 2026-01-20
-- Author: KIKI Platform Team

-- Migration Up
BEGIN;

-- Budget allocations table
CREATE TABLE budget_allocations (
    id BIGSERIAL PRIMARY KEY,
    allocation_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- Ownership
    customer_id VARCHAR(64) NOT NULL,
    campaign_id VARCHAR(64) NOT NULL,
    
    -- Budget details
    total_budget NUMERIC(12, 2) NOT NULL,
    allocated_budget NUMERIC(12, 2) NOT NULL,
    spent_amount NUMERIC(12, 2) DEFAULT 0,
    remaining_budget NUMERIC(12, 2) GENERATED ALWAYS AS (allocated_budget - spent_amount) STORED,
    
    -- Time window
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    
    -- Pacing
    pacing_strategy VARCHAR(32) NOT NULL DEFAULT 'even', -- 'even', 'accelerated', 'decelerated', 'custom'
    daily_budget NUMERIC(12, 2),
    hourly_budget NUMERIC(12, 2),
    
    -- Thresholds
    warning_threshold NUMERIC(5, 4) DEFAULT 0.8, -- 80% spent triggers warning
    critical_threshold NUMERIC(5, 4) DEFAULT 0.95, -- 95% spent triggers critical
    
    -- Status
    status VARCHAR(32) NOT NULL DEFAULT 'active', -- 'draft', 'active', 'paused', 'exhausted', 'expired'
    
    -- Alerts
    last_warning_at TIMESTAMPTZ,
    last_critical_at TIMESTAMPTZ,
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64),
    
    -- Metadata
    metadata JSONB,
    
    -- Constraints
    CONSTRAINT valid_budget CHECK (allocated_budget <= total_budget),
    CONSTRAINT valid_dates CHECK (end_date > start_date),
    CONSTRAINT valid_thresholds CHECK (critical_threshold >= warning_threshold)
);

-- Indexes
CREATE INDEX idx_budget_customer ON budget_allocations (customer_id, status);
CREATE INDEX idx_budget_campaign ON budget_allocations (campaign_id, status);
CREATE INDEX idx_budget_status ON budget_allocations (status, end_date DESC);
CREATE INDEX idx_budget_dates ON budget_allocations (start_date, end_date);

-- Budget transactions table (real-time spending ledger)
CREATE TABLE budget_transactions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    
    -- References
    allocation_id VARCHAR(64) NOT NULL REFERENCES budget_allocations(allocation_id),
    request_id VARCHAR(64), -- Links to audit_log.request_id
    
    -- Transaction details
    transaction_type VARCHAR(32) NOT NULL, -- 'bid', 'refund', 'adjustment'
    amount NUMERIC(12, 2) NOT NULL,
    
    -- Pre/post state
    balance_before NUMERIC(12, 2) NOT NULL,
    balance_after NUMERIC(12, 2) NOT NULL,
    
    -- Approval
    approved BOOLEAN NOT NULL,
    rejection_reason VARCHAR(128),
    
    -- Metadata
    metadata JSONB,
    
    -- Immutability
    immutable BOOLEAN DEFAULT TRUE
);

-- Convert to hypertable
SELECT create_hypertable('budget_transactions', 'timestamp', if_not_exists => TRUE);

-- Indexes
CREATE INDEX idx_transactions_allocation ON budget_transactions (allocation_id, timestamp DESC);
CREATE INDEX idx_transactions_request ON budget_transactions (request_id);
CREATE INDEX idx_transactions_type ON budget_transactions (transaction_type, timestamp DESC);

-- Trigger: Update spent_amount in budget_allocations
CREATE OR REPLACE FUNCTION update_budget_spent()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.approved = TRUE AND NEW.transaction_type = 'bid' THEN
        UPDATE budget_allocations
        SET spent_amount = spent_amount + NEW.amount,
            updated_at = NOW()
        WHERE allocation_id = NEW.allocation_id;
    ELSIF NEW.approved = TRUE AND NEW.transaction_type = 'refund' THEN
        UPDATE budget_allocations
        SET spent_amount = spent_amount - NEW.amount,
            updated_at = NOW()
        WHERE allocation_id = NEW.allocation_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER budget_transaction_update
    AFTER INSERT ON budget_transactions
    FOR EACH ROW
    EXECUTE FUNCTION update_budget_spent();

-- Trigger: Check budget thresholds
CREATE OR REPLACE FUNCTION check_budget_thresholds()
RETURNS TRIGGER AS $$
DECLARE
    utilization NUMERIC(5, 4);
BEGIN
    utilization := NEW.spent_amount / NULLIF(NEW.allocated_budget, 0);
    
    -- Check critical threshold
    IF utilization >= NEW.critical_threshold AND NEW.last_critical_at IS NULL THEN
        NEW.last_critical_at := NOW();
        -- Trigger alert (would integrate with notification service)
        RAISE NOTICE 'CRITICAL: Budget % exhausted for allocation %', 
            ROUND(utilization * 100, 2), NEW.allocation_id;
    END IF;
    
    -- Check warning threshold
    IF utilization >= NEW.warning_threshold AND NEW.last_warning_at IS NULL THEN
        NEW.last_warning_at := NOW();
        RAISE NOTICE 'WARNING: Budget % used for allocation %', 
            ROUND(utilization * 100, 2), NEW.allocation_id;
    END IF;
    
    -- Auto-exhaust
    IF utilization >= 1.0 THEN
        NEW.status := 'exhausted';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER budget_threshold_check
    BEFORE UPDATE OF spent_amount ON budget_allocations
    FOR EACH ROW
    EXECUTE FUNCTION check_budget_thresholds();

-- View: Real-time budget health
CREATE OR REPLACE VIEW budget_health_realtime AS
SELECT
    ba.allocation_id,
    ba.customer_id,
    ba.campaign_id,
    ba.allocated_budget,
    ba.spent_amount,
    ba.remaining_budget,
    ROUND(ba.spent_amount / NULLIF(ba.allocated_budget, 0) * 100, 2) AS utilization_pct,
    ba.status,
    ba.pacing_strategy,
    EXTRACT(DAYS FROM ba.end_date - NOW()) AS days_remaining,
    CASE 
        WHEN ba.spent_amount / NULLIF(ba.allocated_budget, 0) >= ba.critical_threshold THEN 'critical'
        WHEN ba.spent_amount / NULLIF(ba.allocated_budget, 0) >= ba.warning_threshold THEN 'warning'
        ELSE 'healthy'
    END AS health_status,
    COUNT(bt.id) AS transaction_count,
    SUM(bt.amount) FILTER (WHERE bt.approved = TRUE) AS approved_spend,
    SUM(bt.amount) FILTER (WHERE bt.approved = FALSE) AS rejected_spend
FROM budget_allocations ba
LEFT JOIN budget_transactions bt ON ba.allocation_id = bt.allocation_id
    AND bt.timestamp >= NOW() - INTERVAL '24 hours'
WHERE ba.status IN ('active', 'exhausted')
GROUP BY ba.allocation_id, ba.customer_id, ba.campaign_id, ba.allocated_budget, 
         ba.spent_amount, ba.remaining_budget, ba.status, ba.pacing_strategy,
         ba.end_date, ba.critical_threshold, ba.warning_threshold;

-- View: Budget pacing analysis
CREATE OR REPLACE VIEW budget_pacing AS
SELECT
    allocation_id,
    campaign_id,
    allocated_budget,
    spent_amount,
    EXTRACT(DAYS FROM end_date - start_date) AS total_days,
    EXTRACT(DAYS FROM NOW() - start_date) AS elapsed_days,
    EXTRACT(DAYS FROM end_date - NOW()) AS remaining_days,
    ROUND(
        spent_amount / NULLIF(EXTRACT(DAYS FROM NOW() - start_date), 0),
        2
    ) AS avg_daily_spend,
    ROUND(
        remaining_budget / NULLIF(EXTRACT(DAYS FROM end_date - NOW()), 0),
        2
    ) AS required_daily_spend,
    pacing_strategy,
    CASE
        WHEN spent_amount / NULLIF(EXTRACT(DAYS FROM NOW() - start_date), 0) > 
             allocated_budget / NULLIF(EXTRACT(DAYS FROM end_date - start_date), 0) 
        THEN 'over_paced'
        WHEN spent_amount / NULLIF(EXTRACT(DAYS FROM NOW() - start_date), 0) < 
             allocated_budget / NULLIF(EXTRACT(DAYS FROM end_date - start_date), 0) 
        THEN 'under_paced'
        ELSE 'on_pace'
    END AS pacing_status
FROM budget_allocations
WHERE status = 'active'
  AND NOW() BETWEEN start_date AND end_date;

COMMIT;

-- Migration Down
BEGIN;

DROP VIEW IF EXISTS budget_pacing;
DROP VIEW IF EXISTS budget_health_realtime;
DROP TRIGGER IF EXISTS budget_threshold_check ON budget_allocations;
DROP TRIGGER IF EXISTS budget_transaction_update ON budget_transactions;
DROP FUNCTION IF EXISTS check_budget_thresholds();
DROP FUNCTION IF EXISTS update_budget_spent();
DROP TABLE IF EXISTS budget_transactions CASCADE;
DROP TABLE IF EXISTS budget_allocations CASCADE;

COMMIT;
