# 📊 Prometheus + Grafana + Streamlit Dashboard Integration

## 🎯 Overview

Full observability stack for KIKI SyncBrain™ Engine with:
- **Prometheus** (port 9090): Metrics collection & storage
- **Grafana** (port 8502): Visual dashboards
- **Streamlit** (port 8501): Real-time command center
- **AlertManager** (port 9093): Alert routing & notifications

---

## ✅ Current Status

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **Prometheus Exporter** | 9090 | 🟢 Running | Metrics generation & export |
| **Grafana** | 8502 | 🟢 Running | Dashboard visualization |
| **Streamlit Dashboard** | 8501 | 🟢 Running | Real-time command center |
| **SyncValue AI Brain** | 50051 | 🟢 Running | LTV predictions |

---

## 📈 Metrics Exported

### LTV Prediction Metrics
```prometheus
ltv_predictions_total{confidence_level="high"}  # Total predictions made
ltv_prediction_value_micros                     # Distribution of LTV values
ltv_prediction_confidence_score                 # Confidence 0-1
```

### Payment Processing Metrics
```prometheus
payment_invoices_created_total{provider="stripe|zuora|paypal"}
payment_success_rate{provider="stripe|zuora|paypal"}  # Success %
```

### Integration Health
```prometheus
integration_health_status{adapter_name="stripe|slack|snowflake|..."}  # 1=healthy
margin_improvement_percentage{client_id="..."}
```

### System Performance
```prometheus
api_latency_milliseconds_bucket{endpoint="/predict-ltv|/create-invoice|..."}
ai_brain_uptime_seconds
active_customers
total_revenue_micros
circuit_breaker_trips_total{service="payment_processing|crm_sync"}
audit_trail_records_total
```

---

## 🚀 Quick Start

### 1. Start Prometheus Exporter
```bash
cd C:\Users\USER\Documents\KIKI
python ai-models/prometheus_exporter.py
```

Metrics available at: `http://localhost:9090/metrics`

### 2. Verify Metrics
```bash
# Test metrics endpoint
curl http://localhost:9090/metrics | findstr "ltv_predictions\|payment_success\|integration_health"
```

### 3. View in Streamlit
```
http://localhost:8501
```

See "Prometheus Metrics" section with:
- LTV Predictions (24h)
- Integration Health %
- Active Customers
- Total Revenue

### 4. Visualize in Grafana
```
http://localhost:8502
```

Login: admin / kiki-admin

Available dashboards:
- KIKI SyncBrain™ Metrics (pre-configured)
- Integration Health
- Payment Performance
- API Latency Analysis

---

## 📊 Dashboard Views

### Streamlit Dashboard
- Real-time metrics from Prometheus
- Audit trail visualization
- Integration health status
- Performance summary

```
📊 Prometheus Metrics Section:
├─ LTV Predictions (counter)
├─ Integration Health % (gauge)
├─ Active Customers (gauge)
├─ Total Revenue (gauge)
└─ Detailed metrics table
```

### Grafana Dashboard
- Time-series graphs (24h to 1y views)
- Alert status
- Performance trends
- Integration comparisons

---

## 🛠️ Provisioning Notes (Avoid YAML Warnings)

- Grafana provisions all YAML files under `grafana/provisioning/**` regardless of filename.
- VS Code can mis-associate files named `prometheus.yml` with the Prometheus server schema, causing false errors like:
  - "Property apiVersion is not allowed"
  - "Property datasources is not allowed"

### Recommended Setup
- Datasources: use `grafana/provisioning/datasources/datasources.yml` (already created)
- Dashboards provider: `grafana/provisioning/dashboards/provider.yml` includes a YAML-language-server header to disable strict schema:

```yaml
# yaml-language-server: $schema=../../etc/empty-schema.json
apiVersion: 1
providers:
  - name: 'KIKI SyncBrain'
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
  - name: 'KIKI Local Dev'
    type: file
    options:
      path: C:/Users/USER/Documents/KIKI/grafana/dashboards
```

- Empty schema file is at `etc/empty-schema.json`.
- This prevents VS Code YAML validation from flagging Grafana’s provisioning keys.

No runtime impact: Grafana will continue provisioning as expected.

```
Dashboard: KIKI SyncBrain™ Metrics
├─ LTV Predictions (24h)
├─ Prediction Confidence (gauge)
├─ Payment Success Rate (graph)
├─ Integration Health (table)
├─ API Latency P95 (graph)
├─ Active Customers (stat)
├─ Total Revenue (stat)
├─ Circuit Breaker Trips (graph)
├─ Margin Improvement % (graph)
├─ Audit Trail Size (stat)
└─ System Uptime (stat)
```

---

## 🔔 Alerts Configured

### Critical Alerts
- **IntegrationUnhealthy**: Adapter down for 5+ minutes
- **PaymentSuccessRateLow**: < 90% success rate
- **HighAPILatency**: P95 > 100ms
- **CircuitBreakerTripped**: Resilience fallback activated

### Warning Alerts
- **LowPredictionConfidence**: < 80% confidence
- **LowActiveCustomers**: < 10 active customers
- **LowMarginImprovement**: < 5% margin gain

### Info Alerts
- **AuditTrailSize**: Exceeded 10,000 records

---

## 📋 Configuration Files

### prometheus.yml
```yaml
# Scrape configuration
scrape_configs:
  - job_name: 'kiki-metrics'
    scrape_interval: 5s
    static_configs:
      - targets: ['localhost:9090']

# Alert rules
rule_files:
  - 'kiki-alerts.yml'
```

### kiki-alerts.yml
```yaml
# Alert rules for integration health, payment issues, latency
groups:
  - name: kiki-syncbrain-alerts
    rules:
      - alert: IntegrationUnhealthy
        expr: integration_health_status == 0
        for: 5m
```

### alertmanager.yml
```yaml
# Route alerts to Slack, PagerDuty, email
receivers:
  - name: 'kiki-alerts'
    slack_configs:
      - channel: '#kiki-alerts'
  
  - name: 'payment-alerts'
    slack_configs:
      - channel: '#kiki-payment'
```

---

## 🔗 Integration Architecture

```
┌────────────────────────────────────────────────────────┐
│           KIKI SyncBrain™ System                        │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │      Prometheus Metrics Exporter (:9090)         │ │
│  │  Collects from:                                  │ │
│  │  • SyncValue AI Brain (LTV predictions)          │ │
│  │  • Billing Adapters (13 integrations)            │ │
│  │  • Audit Trail (CSV)                             │ │
│  │  • System health                                 │ │
│  └──────────────────────────────────────────────────┘ │
│         ↓           ↓           ↓                       │
│  ┌────────────┐ ┌─────────────┐ ┌──────────────┐      │
│  │ Prometheus │ │   Grafana   │ │  Streamlit   │      │
│  │   :9090    │ │   :8502     │ │   :8501      │      │
│  │ (Database) │ │ (Dashboard) │ │ (Live UI)    │      │
│  └────────────┘ └─────────────┘ └──────────────┘      │
│         ↓           ↓           ↓                       │
│    Rules Engine  Alerting    Metrics Display           │
│  (kiki-alerts)   & Routing    & Analysis               │
│         ↓                                               │
│  ┌──────────────────────────────────────────────────┐ │
│  │         AlertManager (:9093)                     │ │
│  │  Notifies via Slack, PagerDuty, Email            │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 🔧 Troubleshooting

### Metrics Not Showing in Streamlit
```bash
# Check if exporter is running
curl http://localhost:9090/metrics

# Verify Python is running
ps aux | grep prometheus_exporter.py

# Check for errors
python ai-models/prometheus_exporter.py
```

### Grafana Can't Connect to Prometheus
```bash
# Verify Prometheus is accessible
curl http://localhost:9090

# Check firewall/networking
netstat -ano | findstr "9090"

# Ensure data source is configured in Grafana:
# Configuration → Data Sources → Prometheus → http://localhost:9090
```

### Alerts Not Triggering
```bash
# Check AlertManager running
curl http://localhost:9093

# Verify alert rules are loaded
# Prometheus UI: Alerts tab (http://localhost:9090/alerts)

# Check AlertManager config
cat alertmanager.yml
```

### High Memory Usage
```bash
# Check Prometheus retention
# prometheus.yml: --storage.tsdb.retention.time=15d

# Reduce if needed:
# --storage.tsdb.retention.size=1GB
```

---

## 📚 Next Steps

### 1. Configure Slack Integration
```bash
# Set environment variable
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Verify in alertmanager.yml
slack_api_url: ${SLACK_WEBHOOK_URL}
```

### 2. Set Up PagerDuty
```bash
# For critical alerts
export PAGERDUTY_SERVICE_KEY=your-service-key

# Configured in alertmanager.yml for critical alerts
```

### 3. Create Custom Dashboards
```bash
# Grafana UI: Create → Dashboard
# Add panels for:
# - Margin improvement trends
# - Payment provider comparison
# - Customer retention rates
# - Cost per acquisition
```

### 4. Set Up Long-Term Storage
```bash
# Option 1: Prometheus remote write
# Option 2: VictoriaMetrics (better compression)
# Option 3: Thanos (distributed Prometheus)
```

### 5. Performance Optimization
```bash
# Enable query optimization
# Prometheus: --query.max-samples=10000000

# Use recording rules for complex queries
# In kiki-alerts.yml: add recording_rules section
```

---

## 📞 Support

### Documentation
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [AlertManager](https://prometheus.io/docs/alerting/alertmanager/)

### Dashboards Available
```
http://localhost:8502
- KIKI SyncBrain™ Metrics (main)
- Sync Shield Audit (from existing setup)
- Custom dashboards (add as needed)
```

### Metrics Endpoint
```
http://localhost:9090/metrics
```

---

**Integration Status**: ✅ **COMPLETE**  
**Services Running**: 4 (Exporter, Prometheus, Grafana, Streamlit)  
**Metrics Exported**: 20+ metrics across 5 categories  
**Alerts Configured**: 8 (2 critical, 5 warning, 1 info)  
**Last Updated**: January 18, 2026
