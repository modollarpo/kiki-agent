# SyncEngage™ - Post-Acquisition Loyalty Agent

## Overview

**SyncEngage™** is KIKI's automated retention and loyalty optimization agent. It monitors customer behavior via CRM integration, predicts churn risk, and executes intelligent retention triggers to maximize customer lifetime value (LTV).

## Core Capabilities

### 1. **Automated Retention Triggers**
- **Churn Risk Detection**: Analyzes recency and engagement patterns
- **Smart Segmentation**: High-value, medium-risk, and dormant customer identification
- **Personalized Actions**: Email campaigns, discount offers, feedback surveys

### 2. **CRM Integration**
- Polling customer data from CRM systems (Salesforce, HubSpot, custom APIs)
- Real-time sync of purchase history, engagement scores, and customer profiles
- Audit trail for all retention actions

### 3. **LTV-Driven Decision Making**
- Integrates with **SyncValue™ AI Brain** (gRPC port 50051)
- Predicts customer LTV to prioritize retention efforts
- Optimizes discount levels based on predicted value

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SyncEngage™ Agent                    │
│                                                         │
│  ┌──────────────┐    ┌─────────────┐    ┌───────────┐ │
│  │ CRM Polling  │───▶│ Churn Risk  │───▶│ Retention │ │
│  │   Engine     │    │  Analysis   │    │ Triggers  │ │
│  └──────────────┘    └─────────────┘    └───────────┘ │
│         │                   │                   │       │
│         │                   ▼                   │       │
│         │          ┌─────────────────┐          │       │
│         │          │  SyncValue™ AI  │          │       │
│         │          │   (LTV Service) │          │       │
│         │          └─────────────────┘          │       │
│         │                                        │       │
│         ▼                                        ▼       │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Audit Log (CSV)                        │  │
│  │  timestamp | customer_id | trigger | action     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Retention Logic

### Churn Risk Assessment
- **High Risk**: Last purchase > 90 days OR last engagement > 60 days
- **Medium Risk**: Last purchase > 45 days OR last engagement > 30 days
- **Low Risk**: Active recent engagement

### Trigger Matrix

| Churn Risk | LTV Range | Action | Discount | Message Type |
|------------|-----------|--------|----------|--------------|
| High | > $200 | Offer | 20% | Win-back campaign |
| High | < $200 | Email | 10% | Re-engagement |
| Medium | > $300 | Survey | - | Premium feedback |
| Medium | < $300 | Email | - | Content update |
| Low | > $500 | Offer | 15% | VIP appreciation |
| Low | < $500 | - | - | No trigger (active) |

## API Endpoints

### Health Check
```bash
GET http://localhost:8083/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "SyncEngage™ Retention Agent",
  "ltv_client": true,
  "timestamp": "2026-01-20T10:30:00Z"
}
```

### Trigger Retention Check
```bash
POST http://localhost:8083/trigger
Content-Type: application/json

{
  "customer_id": "cust_001",
  "email": "alice@example.com",
  "last_purchase": "2025-10-15T10:00:00Z",
  "total_spend": 450.0,
  "purchase_count": 12,
  "engagement_score": 8.5,
  "last_engagement": "2025-11-10T15:30:00Z"
}
```

**Response:**
```json
{
  "customer_id": "cust_001",
  "trigger_type": "churn_risk_high_value",
  "action": "offer",
  "message": "We miss you! Here's 20% off your next order (LTV: $540)",
  "discount_pct": 20.0,
  "executed_at": "2026-01-20T10:35:00Z",
  "predicted_ltv": 540.0
}
```

## Running the Agent

### Local Development
```bash
cd cmd/syncengage
go build -o syncengage
./syncengage
```

### Docker
```bash
docker build -t kiki-syncengage ./cmd/syncengage
docker run -p 8083:8083 kiki-syncengage
```

### Windows
```bash
cd cmd\syncengage
go build -o syncengage.exe
.\syncengage.exe
```

## Configuration

Environment variables (optional):
- `LTV_SERVICE_URL`: LTV gRPC service endpoint (default: `localhost:50051`)
- `CRM_POLL_INTERVAL`: Polling interval in seconds (default: `10`)
- `AUDIT_LOG_PATH`: Audit log file path (default: `syncengage_audit.csv`)

## Integration with KIKI Ecosystem

### Dependencies
- **SyncValue™** (port 50051): LTV predictions
- **CRM System**: Customer data source (Salesforce, HubSpot, etc.)

### Connected Services
- **SyncFlow™**: Can trigger ads based on retention campaign success
- **SyncShield™**: Budget compliance for discount offers
- **Dashboard**: Metrics visualization (port 8502)

## Metrics & Monitoring

SyncEngage™ exports the following metrics:
- `syncengage_triggers_total{type}`: Count of retention triggers by type
- `syncengage_ltv_predictions`: LTV distribution histogram
- `syncengage_churn_risk{level}`: Customer count by churn risk level
- `syncengage_crm_sync_duration_ms`: CRM polling latency

## Audit Trail

All retention actions are logged to `syncengage_audit.csv`:

```csv
timestamp,customer_id,trigger_type,action,message,discount_pct,predicted_ltv
2026-01-20T10:35:00Z,cust_001,churn_risk_high_value,offer,We miss you!,20.0,540.0
2026-01-20T10:35:02Z,cust_003,churn_risk_standard,email,Welcome back,10.0,132.0
```

## Future Enhancements

- [ ] Multi-channel support (SMS, push notifications, in-app)
- [ ] A/B testing for retention messages
- [ ] Dynamic discount optimization using reinforcement learning
- [ ] Real-time CRM webhooks (instead of polling)
- [ ] Integration with email service providers (SendGrid, Mailchimp)
- [ ] Customer journey analytics dashboard

## Support

For issues or questions:
- GitHub: [KIKI Agent Issues](https://github.com/user/kiki-agent/issues)
- Docs: `docs/SYNCENGAGE_ARCHITECTURE.md`
