-- Admin audit trail for Super-Admin Dashboard
CREATE TABLE IF NOT EXISTS admin_actions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    admin_id VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource VARCHAR(128),
    changes JSONB,
    ip_address INET
);

-- Alert configuration for admin dashboard
CREATE TABLE IF NOT EXISTS alert_config (
    id SERIAL PRIMARY KEY,
    alert_name VARCHAR(64) UNIQUE,
    metric_name VARCHAR(128),
    threshold NUMERIC(10, 2),
    condition VARCHAR(32), -- 'greater_than', 'less_than', 'equals'
    enabled BOOLEAN DEFAULT TRUE,
    webhook_url TEXT,
    email_recipients TEXT[]
);
