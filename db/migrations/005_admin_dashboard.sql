-- Migration 005: Admin Dashboard & Audit Configuration
-- Adds tables for Super-Admin dashboard: audit actions and alert configuration

BEGIN;

-- Admin Actions Table (Audit Trail)
CREATE TABLE admin_actions (
    id BIGSERIAL PRIMARY KEY,
    action_id VARCHAR(64) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    admin_id VARCHAR(64) NOT NULL,
    admin_username VARCHAR(128),
    action VARCHAR(64) NOT NULL,         -- restart, pause, resume, config, etc.
    resource VARCHAR(128) NOT NULL,     -- service name, campaign id, etc.
    resource_type VARCHAR(64),          -- service, campaign, budget, etc.
    status VARCHAR(32) DEFAULT 'pending', -- pending, completed, failed
    details JSONB,                      -- additional action details
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX idx_admin_actions_timestamp ON admin_actions(timestamp DESC);
CREATE INDEX idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX idx_admin_actions_action ON admin_actions(action);
CREATE INDEX idx_admin_actions_resource ON admin_actions(resource);
CREATE INDEX idx_admin_actions_status ON admin_actions(status);

-- Alert Configuration Table
CREATE TABLE alert_config (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    alert_name VARCHAR(128) NOT NULL,
    metric_name VARCHAR(256) NOT NULL,  -- e.g., 'syncshield.error_rate', 'synccreate.latency_p95'
    service_name VARCHAR(64),
    condition VARCHAR(32) NOT NULL,     -- 'greater_than', 'less_than', 'equals', 'between'
    threshold NUMERIC(10, 2) NOT NULL,
    threshold_min NUMERIC(10, 2),       -- for 'between' condition
    severity VARCHAR(32) NOT NULL,      -- 'info', 'warning', 'critical'
    enabled BOOLEAN DEFAULT TRUE,
    cooldown_seconds INT DEFAULT 300,   -- minimum time between alert notifications
    webhook_url TEXT,
    email_recipients TEXT[],
    slack_channel VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_config_service ON alert_config(service_name);
CREATE INDEX idx_alert_config_enabled ON alert_config(enabled);
CREATE INDEX idx_alert_config_metric ON alert_config(metric_name);

-- Alert History (for tracking alert events)
CREATE TABLE alert_history (
    id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(64) NOT NULL REFERENCES alert_config(alert_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    value NUMERIC(15, 4),
    triggered BOOLEAN DEFAULT FALSE,
    message TEXT,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alert_history_alert_id ON alert_history(alert_id);
CREATE INDEX idx_alert_history_timestamp ON alert_history(timestamp DESC);
CREATE INDEX idx_alert_history_triggered ON alert_history(triggered);

-- Admin Sessions (for tracking login activity)
CREATE TABLE admin_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(256) UNIQUE NOT NULL,
    admin_id VARCHAR(64) NOT NULL,
    admin_username VARCHAR(128),
    ip_address INET,
    user_agent TEXT,
    login_at TIMESTAMPTZ DEFAULT NOW(),
    logout_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_admin_sessions_admin_id ON admin_sessions(admin_id);
CREATE INDEX idx_admin_sessions_is_active ON admin_sessions(is_active);

-- Admin Roles Table (for RBAC)
CREATE TABLE admin_roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT[], -- e.g., ['view_metrics', 'restart_services', 'pause_campaigns']
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admin_roles_name ON admin_roles(role_name);

-- Admin Users Table
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    admin_id VARCHAR(64) UNIQUE NOT NULL,
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT REFERENCES admin_roles(id),
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32),
    api_key VARCHAR(256) UNIQUE,
    api_key_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_admin_users_username ON admin_users(username);
CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_api_key ON admin_users(api_key_hash);

-- Insert default roles
INSERT INTO admin_roles (role_name, description, permissions) VALUES
('super_admin', 'Full platform access', 
 ARRAY['view_all', 'restart_services', 'pause_campaigns', 'manage_budgets', 'manage_alerts', 'manage_users', 'export_data']),

('manager', 'Service and budget management',
 ARRAY['view_metrics', 'restart_services', 'pause_campaigns', 'manage_budgets', 'view_audit_log']),

('analyst', 'Read-only monitoring and reporting',
 ARRAY['view_metrics', 'view_budgets', 'view_audit_log', 'export_reports']),

('operator', 'Service operations only',
 ARRAY['view_status', 'restart_services', 'view_logs']);

-- Insert default alerts
INSERT INTO alert_config (alert_id, alert_name, metric_name, service_name, condition, threshold, severity, email_recipients) VALUES
('alert_001', 'SyncShield High Error Rate', 'syncshield.error_rate', 'syncshield', 'greater_than', 5.0, 'critical', ARRAY['admin@kiki.ai']),
('alert_002', 'SyncEngage Latency Spike', 'syncengage.latency_p95', 'syncengage', 'greater_than', 1000.0, 'warning', ARRAY['admin@kiki.ai']),
('alert_003', 'SyncFlow Budget Threshold', 'syncflow.budget_utilization', 'syncflow', 'greater_than', 95.0, 'warning', ARRAY['admin@kiki.ai']),
('alert_004', 'SyncCreate GPU Memory', 'synccreate.gpu_memory_used', 'synccreate', 'greater_than', 90.0, 'warning', ARRAY['admin@kiki.ai']),
('alert_005', 'SyncValue Model Accuracy', 'syncvalue.model_accuracy', 'syncvalue', 'less_than', 90.0, 'critical', ARRAY['admin@kiki.ai']),
('alert_006', 'Database Connection Pool', 'database.connection_pool_utilization', 'database', 'greater_than', 80.0, 'warning', ARRAY['admin@kiki.ai']),
('alert_007', 'Redis Memory Usage', 'redis.memory_used', 'redis', 'greater_than', 85.0, 'warning', ARRAY['admin@kiki.ai']);

-- Immutability trigger for audit_actions (prevent tampering)
CREATE OR REPLACE FUNCTION prevent_admin_action_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Admin actions are immutable and cannot be modified';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER admin_actions_immutable
    BEFORE UPDATE ON admin_actions
    FOR EACH ROW
    EXECUTE FUNCTION prevent_admin_action_modification();

CREATE TRIGGER admin_actions_no_delete
    BEFORE DELETE ON admin_actions
    FOR EACH ROW
    EXECUTE FUNCTION prevent_admin_action_modification();

-- View for admin activity summary
CREATE VIEW admin_activity_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as total_actions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    COUNT(DISTINCT admin_id) as unique_admins
FROM admin_actions
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC;

-- View for alert statistics
CREATE VIEW alert_stats AS
SELECT 
    ac.service_name,
    ac.alert_name,
    COUNT(ah.id) as total_alerts,
    COUNT(CASE WHEN ah.triggered THEN 1 END) as triggered_count,
    MAX(ah.timestamp) as last_triggered,
    AVG(ah.value) as avg_value
FROM alert_config ac
LEFT JOIN alert_history ah ON ac.id = ah.alert_id
GROUP BY ac.service_name, ac.alert_name;

-- Audit table for tracking admin table changes
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(128),
    operation VARCHAR(10),
    record_id VARCHAR(128),
    old_values JSONB,
    new_values JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at DESC);

COMMIT;
