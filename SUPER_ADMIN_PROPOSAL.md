# KIKI Super-Admin Dashboard

A centralized administrative console for monitoring, managing, and controlling all KIKI platform services.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│               KIKI Super-Admin Dashboard                      │
│                    (Web-Based Admin UI)                       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Overview   │  │  Monitoring  │  │  Analytics   │      │
│  │   (Home)     │  │  (Real-time) │  │  (Reports)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │   Budgets    │  │   Audit Log  │      │
│  │  (Control)   │  │ (Management) │  │  (Compliance)│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Alerts      │  │  Users/Roles │  │  Settings    │      │
│  │  (Config)    │  │  (Auth)      │  │  (System)    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          API Gateway (REST + WebSocket)            │    │
│  └─────────────────────────────────────────────────────┘    │
│                      ▲                                       │
├──────────────────────┼───────────────────────────────────────┤
│                      │                                        │
│  ┌────────────────────┴────────────────────────────────┐    │
│  │                                                     │     │
│  │  SyncValue │ SyncShield │ SyncEngage │ SyncFlow │  │    │
│  │  SyncCreate │ PostgreSQL │ Redis │ Prometheus     │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Features by Section

### 1. **Dashboard Overview (Home)**
- Real-time service health status (✅/🟡/❌)
- Key metrics (requests/sec, errors, latency p99)
- Revenue metrics (if using Billing OaaS)
- Top alerts & critical issues
- Quick action buttons

**Metrics Displayed:**
```
┌─────────────────────────────────────────┐
│ KIKI Platform - Super Admin Dashboard   │
├─────────────────────────────────────────┤
│                                         │
│  Status: 🟢 ALL SYSTEMS OPERATIONAL    │
│  Uptime: 45d 12h 33m                   │
│  Active Users: 12,450                  │
│  Campaigns Running: 847                │
│  Daily Revenue: $45,320.50             │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Service Health                  │   │
│  ├─────────────────────────────────┤   │
│  │ SyncValue      ✅ 99.98%        │   │
│  │ SyncShield     ✅ 99.99%        │   │
│  │ SyncEngage     ✅ 99.95%        │   │
│  │ SyncFlow       ✅ 99.97%        │   │
│  │ SyncCreate     🟡 99.80% (slow) │   │
│  │ PostgreSQL     ✅ 100%          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Recent Alerts (5)               │   │
│  ├─────────────────────────────────┤   │
│  │ ⚠️  SyncCreate p95 latency >5s  │   │
│  │ 🔴 Budget exhausted: camp_001  │   │
│  │ ✅ Deployed: syncflow v1.2.3   │   │
│  │ ✅ Migration completed (004)    │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

### 2. **Service Monitoring (Real-time)**
Track each microservice with detailed metrics:

**SyncShield (Budget Governance)**
- Active budget allocations
- Budget utilization rate
- Compliance violations
- Circuit breaker trips
- Spend trending

**SyncEngage (Retention)**
- At-risk customers (churn risk > 70%)
- Message sends/opens/clicks
- Cohort retention rates
- CRM sync status
- Engagement trends

**SyncValue (LTV AI)**
- Model accuracy (current: 92.3%)
- Inference latency p50/p95/p99
- Prediction cache hit rate
- Drift detection alerts
- Model version status

**SyncFlow (Campaign Executor)**
- Active campaigns
- Bids placed (24h)
- Budget pacing vs target
- Platform connector status
- Error rate & circuit breaker state

**SyncCreate (Creative AI)**
- Creatives generated (24h)
- Brand compliance scores
- Toxicity detection rate
- Model loading time
- GPU/CPU utilization

---

### 3. **Budget Management Dashboard**
- Campaign budget allocation grid
- Real-time spend tracking
- Daily pacing vs forecast
- Budget exhaustion warnings
- ROI by campaign/platform
- Spend forecasting

---

### 4. **Audit & Compliance**
- All bid decisions logged
- Budget check history
- Model prediction accuracy
- User actions (GDPR)
- Data export requests
- Consent management

---

### 5. **Alerts & Notifications**
Configure thresholds for:
- Service downtime
- High error rates
- Budget threshold (80%, 95%, 100%)
- Latency SLO violations
- Model accuracy degradation
- Churn risk spikes
- Failed integrations

---

### 6. **User & Role Management**
- Role-based access control (RBAC)
- Admin / Manager / Viewer roles
- API key management
- Audit trail of admin actions
- 2FA enforcement

**Roles:**
- **Super Admin**: Full access (you)
- **Manager**: Service/budget control
- **Analyst**: Read-only monitoring
- **Operator**: Restart services, view logs

---

### 7. **System Settings**
- Service auto-scaling config
- Alert thresholds
- Data retention policies
- Backup schedule
- Log levels
- API rate limits

---

## Implementation Plan

### Phase 1: Admin API (Backend)
**Location:** `cmd/admin/` (new Go service)

```go
// cmd/admin/main.go
- Aggregates metrics from all services
- Provides REST API for dashboard
- WebSocket for real-time updates
- Authentication/Authorization
- Audit logging
```

**Endpoints:**
```
GET  /api/admin/health              - Overall platform health
GET  /api/admin/services            - Status of all services
GET  /api/admin/metrics             - Aggregated metrics
GET  /api/admin/alerts              - Active alerts
POST /api/admin/alerts/config       - Update alert thresholds
GET  /api/admin/audit-log           - Compliance audit trail
GET  /api/admin/budgets             - Budget overview
POST /api/admin/budgets/:id/pause   - Pause campaign
GET  /api/admin/creatives           - Creative performance
POST /api/admin/services/:id/restart - Restart service
```

### Phase 2: Admin UI (Frontend)
**Location:** `web/admin/` (new SPA)

```
web/admin/
├── index.html
├── css/
│   ├── dashboard.css
│   ├── responsive.css
│   └── dark-mode.css
├── js/
│   ├── app.js
│   ├── api.js
│   ├── charts.js
│   ├── auth.js
│   └── websocket.js
├── components/
│   ├── navbar.html
│   ├── sidebar.html
│   ├── service-card.html
│   ├── metric-gauge.html
│   ├── budget-grid.html
│   └── alert-panel.html
└── pages/
    ├── overview.html
    ├── services.html
    ├── budgets.html
    ├── audit-log.html
    ├── alerts.html
    ├── users.html
    └── settings.html
```

**Tech Stack:**
- Vue.js 3 or React for interactivity
- Chart.js for metrics visualization
- WebSocket for real-time updates
- Bootstrap 5 for responsive design

### Phase 3: Database Schema
```sql
-- Admin audit trail
CREATE TABLE admin_actions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    admin_id VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    resource VARCHAR(128),
    changes JSONB,
    ip_address INET
);

-- Alert configuration
CREATE TABLE alert_config (
    id SERIAL PRIMARY KEY,
    alert_name VARCHAR(64) UNIQUE,
    metric_name VARCHAR(128),
    threshold NUMERIC(10, 2),
    condition VARCHAR(32), -- 'greater_than', 'less_than', 'equals'
    enabled BOOLEAN DEFAULT TRUE,
    webhook_url TEXT,
    email_recipients TEXT[]
);
```

---

## Access & Security

### Authentication
- Admin username/password (bcrypt hashed)
- Optional: OAuth2 with Google/Azure AD
- Session tokens with expiration
- 2FA support (TOTP)

### Authorization
```
Super Admin:
  ├─ View all services/metrics
  ├─ Pause/restart campaigns
  ├─ Pause/resume services
  ├─ Configure alerts
  ├─ Manage users/roles
  └─ Export audit logs

Manager:
  ├─ View all services/metrics
  ├─ Pause campaigns
  ├─ View budgets
  └─ View audit logs (read-only)

Analyst:
  ├─ View metrics (read-only)
  ├─ View budgets (read-only)
  └─ Export reports

Operator:
  ├─ View service status
  ├─ Restart services
  └─ View logs (tail)
```

---

## Real-time Updates with WebSocket

```javascript
// Client connects to admin WebSocket
const ws = new WebSocket('ws://localhost:8085/live/metrics');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // {
    //   service: 'syncshield',
    //   metric: 'requests_per_sec',
    //   value: 1250,
    //   timestamp: '2026-01-20T15:30:45Z'
    // }
    updateDashboardMetric(update);
};
```

---

## Dashboard Mockup

```
┌──────────────────────────────────────────────────────────────┐
│  KIKI Super-Admin                          [Settings] [Logout]│
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Dashboard  Services  Budgets  Audit  Alerts  Users Settings │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  System Status: 🟢 ALL OPERATIONAL                          │
│  ├─ Uptime: 45 days                                         │
│  ├─ Active Campaigns: 847                                   │
│  └─ Daily Revenue: $45,320.50                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Service Health                                      │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Service         │ Status │ Uptime │ Req/s │ Latency│   │
│  ├─────────────────┼────────┼────────┼───────┼─────────┤   │
│  │ SyncValue       │ ✅     │ 99.98% │ 850   │ 45ms   │   │
│  │ SyncShield      │ ✅     │ 99.99% │ 2100  │ 12ms   │   │
│  │ SyncEngage      │ ✅     │ 99.95% │ 650   │ 85ms   │   │
│  │ SyncFlow        │ ✅     │ 99.97% │ 1200  │ 25ms   │   │
│  │ SyncCreate      │ 🟡     │ 99.80% │ 120   │ 1.2s   │   │
│  │ PostgreSQL      │ ✅     │ 100%   │ -     │ 8ms    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Requests Per Second (Last 24h)        [View Details]│   │
│  │                                                      │   │
│  │         █ SyncFlow  │ 1,200 req/s                  │   │
│  │      ███ SyncShield │ 2,100 req/s                  │   │
│  │        █ SyncEngage │   650 req/s                  │   │
│  │       ██ SyncValue  │   850 req/s                  │   │
│  │        █ SyncCreate │   120 req/s                  │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────────┐  ┌────────────────────────────┐   │
│  │ Top Campaigns      │  │ Budget Status              │   │
│  ├────────────────────┤  ├────────────────────────────┤   │
│  │ camp_google_001    │  │ Total Allocated: $500k    │   │
│  │ camp_meta_012      │  │ Spent (24h): $12,450      │   │
│  │ camp_tiktok_045    │  │ Remaining: $487,550 (97%) │   │
│  │ camp_linkedin_089  │  │ ⚠️ Near limit: camp_001  │   │
│  └────────────────────┘  └────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Recent Alerts (5)                                  │   │
│  ├────────────────────────────────────────────────────┤   │
│  │ ⚠️  [2:15pm] SyncCreate latency spike (p95: 5.2s) │   │
│  │ 🔴 [1:45pm] Budget alert: camp_001 at 95%        │   │
│  │ ✅ [12:30pm] Deployed: syncflow v1.2.3           │   │
│  │ ✅ [11:00am] Migration 004_budget completed      │   │
│  │ 🟡 [9:15am] Model accuracy: 91.2% (↓0.8%)       │   │
│  └────────────────────────────────────────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Actions (Admin Menu)

```
┌─────────────────────────────────────┐
│ Quick Actions                       │
├─────────────────────────────────────┤
│ 🚀 Restart Service                  │
│ ⏸️  Pause Campaign                   │
│ 🔧 Update Alert Threshold           │
│ 📊 Export Metrics Report            │
│ 🔑 Rotate API Key                   │
│ 📋 View Audit Trail                 │
│ 📧 Send Alert Notification          │
│ 🗑️  Archive Old Logs                │
│ 🔄 Trigger Manual Migration         │
│ 📱 Check Service Logs               │
└─────────────────────────────────────┘
```

---

## Integration with Existing Services

### Prometheus Metrics
Admin dashboard queries Prometheus for:
- Request counts
- Error rates
- Latency percentiles
- Service up/down status

### Database Queries
Direct access to PostgreSQL audit trail:
- Bid decisions
- Budget transactions
- Customer retention events
- Creative performance

### Service APIs
Calls to each microservice:
- /health endpoints
- /metrics endpoints
- Control endpoints (pause, restart)

---

## Implementation Timeline

| Phase | Component | Time | Status |
|-------|-----------|------|--------|
| 1 | Admin API backend | 1-2 days | Not started |
| 2 | Admin UI frontend | 2-3 days | Not started |
| 3 | WebSocket integration | 1 day | Not started |
| 4 | Authentication/RBAC | 1 day | Not started |
| 5 | Testing & deployment | 1 day | Not started |
| **Total** | | **1 week** | |

---

## Benefits

✅ **Visibility** - See all platform activity in one place  
✅ **Control** - Pause campaigns, restart services immediately  
✅ **Compliance** - Complete audit trail for regulatory requirements  
✅ **Debugging** - Quick access to logs and metrics  
✅ **Alerts** - Get notified of issues immediately  
✅ **Reporting** - Export metrics and compliance reports  
✅ **Security** - Role-based access control & API key management  
✅ **Multi-tenant** - Support multiple organizations (future)  

---

**Should we build this?** Yes! It's a critical piece for enterprise-grade operations. Want me to create the initial files and structure?
