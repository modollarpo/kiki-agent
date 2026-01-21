# KIKI Super-Admin Dashboard

**Enterprise-grade centralized control panel for monitoring, managing, and administering all KIKI platform services.**

---

## 🎯 Overview

The Super-Admin Dashboard provides a single pane of glass for:
- **Real-time Monitoring** - Service health, metrics, latency, errors
- **Service Control** - Restart, pause, resume services on-demand
- **Budget Management** - Campaign budgets, spend tracking, ROI
- **Alert Management** - Configure thresholds, receive notifications
- **Audit & Compliance** - Complete audit trail for regulatory requirements
- **User Management** - Role-based access control (RBAC)

### Access
- **URL:** `http://localhost:8085`
- **Port:** 8085
- **Default Credentials:** admin / (see setup)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     Browser (Admin UI - React/Vue)      │
│       http://localhost:8085             │
└──────────────┬──────────────────────────┘
               │
               │ HTTP + WebSocket
               ▼
┌─────────────────────────────────────────┐
│   Admin API (Go - Port 8085)            │
│                                         │
│  ├─ /api/admin/health                  │
│  ├─ /api/admin/metrics                 │
│  ├─ /api/admin/services                │
│  ├─ /api/admin/alerts                  │
│  ├─ /api/admin/audit-log               │
│  ├─ /live/metrics (WebSocket)          │
│  └─ Static file serving (web/admin)    │
└──────────────┬──────────────────────────┘
               │
       ┌───────┼───────┬───────┬───────┐
       ▼       ▼       ▼       ▼       ▼
    Prometheus Postgres Services Redis
```

### Components

#### 1. **Admin API Backend** (`cmd/admin/main.go`)
- REST API endpoints for metrics, alerts, actions
- WebSocket for real-time metric streaming
- Service health checking
- Admin action logging
- PostgreSQL integration for persistent storage

#### 2. **Admin UI Frontend** (`web/admin/`)
- Single Page Application (SPA)
- Dark theme optimized for operations
- Real-time dashboard updates via WebSocket
- Responsive design (mobile, tablet, desktop)
- Bootstrap 5 + Chart.js for charts

#### 3. **Database Schema** (`db/migrations/005_admin_dashboard.sql`)
- `admin_actions` - Immutable audit trail
- `alert_config` - Alert threshold configurations
- `alert_history` - Alert event tracking
- `admin_sessions` - Login/session tracking
- `admin_users` - User accounts and API keys
- `admin_roles` - RBAC role definitions

---

## 📊 Dashboard Features

### 1. **Home/Overview Tab**

Displays overall platform health at a glance:

```
┌─────────────────────────────────────────────┐
│  System Uptime: 45d 12h 33m                 │
│  Active Campaigns: 847                      │
│  Daily Revenue: $45,320.50                 │
│  Services Up: 6/6 ✅                       │
└─────────────────────────────────────────────┘

Service Health:
┌──────────────┬────────┬────────┬──────────┐
│ Service      │ Status │ Uptime │ Req/s    │
├──────────────┼────────┼────────┼──────────┤
│ SyncShield   │ 🟢 Up  │ 99.99% │ 2,100    │
│ SyncEngage   │ 🟢 Up  │ 99.95% │ 650      │
│ SyncFlow     │ 🟢 Up  │ 99.97% │ 1,200    │
│ SyncCreate   │ 🟡 Slow│ 99.80% │ 120      │
│ SyncValue    │ 🟢 Up  │ 99.98% │ 850      │
│ PostgreSQL   │ 🟢 Up  │ 100%   │ -        │
└──────────────┴────────┴────────┴──────────┘

Recent Alerts:
✅ SyncCreate p95 latency elevated (5.2s)
🔴 Budget warning: campaign_001 at 95%
✅ Migration 005 completed successfully
```

### 2. **Services Tab**

Detailed view of each microservice:

**For Each Service:**
- Current status (Up/Down/Degraded)
- Uptime percentage
- Request rate (req/s)
- Error rate (%)
- Latency percentiles (p50, p95, p99)
- Action buttons (Restart, Pause, View Logs)

**Quick Actions:**
```
[🔄 Restart]  [⏸️  Pause]  [📋 Logs]
```

### 3. **Budgets Tab**

Campaign budget tracking:

- Total allocated budget
- Spend to date (24h, 7d, 30d, all-time)
- Daily pacing vs forecast
- Budget utilization by platform (Google, Meta, TikTok, LinkedIn)
- ROI by campaign
- Budget exhaustion warnings (80%, 95%, 100%)

### 4. **Alerts Tab**

Alert configuration and management:

**View Alerts:**
- All active alerts with severity
- Alert history and trends
- Most frequent alerts
- False positive rate

**Configure Alerts:**
- Metric thresholds
- Severity levels
- Notification channels (Email, Slack, Webhook)
- Cooldown periods

### 5. **Audit Log Tab**

Complete compliance audit trail:

```
Timestamp            │ Admin    │ Action      │ Resource      │ Status
─────────────────────┼──────────┼─────────────┼───────────────┼──────────
2026-01-20 14:32:15 │ admin    │ restart     │ syncflow      │ completed
2026-01-20 14:15:42 │ admin    │ pause       │ campaign_001  │ completed
2026-01-20 13:50:19 │ analyst  │ export      │ audit_log     │ completed
```

---

## 🔐 Role-Based Access Control (RBAC)

### Roles

#### **Super Admin**
- Full platform access
- Restart/pause services
- Configure alerts
- Manage budgets
- Manage users and roles
- Export data

#### **Manager**
- View all metrics
- Restart/pause services
- Manage campaign budgets
- View audit logs

#### **Analyst**
- View metrics (read-only)
- View budgets (read-only)
- Generate reports
- View audit logs (read-only)

#### **Operator**
- View service status
- Restart services
- View logs (tail)

---

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+ (in docker-compose)
- All 5 core services running

### Installation

#### 1. **Build Admin API**
```bash
cd cmd/admin
go mod download
go build -o admin-api
```

#### 2. **Start with Docker Compose**
```bash
docker-compose up -d postgres
./scripts/migrate.ps1 up  # Run migration 005
docker-compose up -d admin-api
```

#### 3. **Access Dashboard**
```
http://localhost:8085
```

---

## 📡 API Endpoints

### Health & Status

```http
GET /health
GET /api/admin/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-20T14:30:45Z",
  "services_up": 6,
  "services_total": 6
}
```

### Metrics

```http
GET /api/admin/metrics
```

Response:
```json
{
  "timestamp": "2026-01-20T14:30:45Z",
  "services": {
    "syncshield": {
      "name": "syncshield",
      "status": "up",
      "uptime": 99.99,
      "requests_per_sec": 2100.5,
      "error_rate": 0.1,
      "latency": {
        "p50": 8,
        "p95": 15,
        "p99": 25
      }
    },
    ...
  },
  "active_campaigns": 847,
  "daily_revenue": 45320.50
}
```

### Services

```http
GET /api/admin/services
POST /api/admin/services/{service}/restart
POST /api/admin/services/{service}/pause
```

### Alerts

```http
GET /api/admin/alerts
POST /api/admin/alerts/config
```

### Audit Log

```http
GET /api/admin/audit-log
```

### WebSocket (Real-time Metrics)

```javascript
const ws = new WebSocket('ws://localhost:8085/live/metrics');

ws.onmessage = (event) => {
    const { type, data } = JSON.parse(event.data);
    // { type: 'metrics', data: {...} }
};
```

---

## 🔧 Configuration

### Environment Variables

```env
PORT=8085
PROMETHEUS_URL=http://localhost:9090
SYNCSHIELD_URL=http://localhost:8081/health
SYNCENGAGE_URL=http://localhost:8083/health
SYNCFLOW_URL=http://localhost:8082/health
SYNCCREATE_URL=http://localhost:8084/health
SYNCVALUE_URL=http://localhost:50051/health
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kiki_platform
DB_USER=kiki_admin
DB_PASSWORD=kiki_dev_password
```

### Alert Configuration

Configure alerts in `alert_config` table:

```sql
INSERT INTO alert_config (
  alert_id, alert_name, metric_name, service_name,
  condition, threshold, severity, email_recipients
) VALUES (
  'alert_custom_001',
  'High Latency Warning',
  'syncshield.latency_p95',
  'syncshield',
  'greater_than',
  100.0,
  'warning',
  ARRAY['ops@kiki.ai', 'admin@kiki.ai']
);
```

---

## 📊 Real-time Monitoring

### WebSocket Connection

The dashboard connects to the Admin API via WebSocket for real-time updates:

```javascript
// Automatic reconnection with 5-second backoff
// Receives metric updates every 10 seconds
// Zero-latency alerts and status changes
```

### Metric Update Frequency
- **Service Health:** Every 10 seconds
- **Alerts:** Real-time on trigger
- **Audit Log:** Real-time on action

---

## 🛡️ Security

### Authentication
- Username/password (bcrypt hashed)
- Optional: OAuth2 (Google, Azure AD)
- Optional: 2FA (TOTP)
- Session tokens with expiration

### Authorization
- Role-based access control (RBAC)
- API key support for service-to-service
- Granular permission model

### Audit Trail
- All admin actions logged
- Immutable audit table
- Timestamp and IP tracking
- User agent logging

### Data Protection
- HTTPS/TLS in production
- Password hashing (bcrypt)
- API rate limiting
- CORS configuration

---

## 📈 Metrics Collected

### Per-Service Metrics
- Uptime percentage
- Requests per second
- Error rate (%)
- Latency percentiles (p50, p95, p99)
- Memory usage
- CPU usage

### Platform Metrics
- Total active campaigns
- Daily revenue
- Budget utilization
- Model accuracy (SyncValue)
- GPU utilization (SyncCreate)

### Alert Metrics
- Alert trigger count
- False positive rate
- Mean time to resolution (MTTR)

---

## 🚨 Alert Thresholds (Default)

| Alert | Threshold | Severity |
|-------|-----------|----------|
| SyncShield Error Rate | > 5% | Critical |
| SyncEngage Latency (p95) | > 1000ms | Warning |
| SyncFlow Budget | > 95% | Warning |
| SyncCreate GPU | > 90% | Warning |
| SyncValue Accuracy | < 90% | Critical |
| Database Connections | > 80% | Warning |
| Redis Memory | > 85% | Warning |

---

## 🔄 Integration Points

### With Services
- **Health Endpoints:** Polls `/health` for status
- **Metrics:** Via Prometheus scraping
- **Actions:** Direct service API calls (restart, pause)

### With Database
- **Audit Trail:** Reads from `admin_actions`
- **Alert Config:** Reads/writes to `alert_config`
- **Sessions:** Reads from `admin_sessions`

### With External Systems
- **Email Alerts:** SMTP integration
- **Slack Alerts:** Webhook integration
- **Custom Webhooks:** HTTP POST to configured URLs

---

## 📚 Documentation

### API Documentation
See [Admin API Endpoints](#-api-endpoints)

### Database Schema
See `db/migrations/005_admin_dashboard.sql`

### Frontend Code
- `web/admin/index.html` - Main dashboard
- `web/admin/css/dashboard.css` - Styling
- `web/admin/js/app.js` - Client logic

### Backend Code
- `cmd/admin/main.go` - Admin API server

---

## 🐛 Troubleshooting

### Connection Issues

**"Cannot connect to http://localhost:8085"**
```bash
# Check if Admin API is running
docker-compose ps admin-api

# Check logs
docker-compose logs admin-api

# Restart
docker-compose restart admin-api
```

### WebSocket Connection Failed

**"WebSocket connection refused"**
- Ensure Admin API is running
- Check firewall (port 8085)
- Check browser console for errors

### Alerts Not Triggering

**"Alert configuration saved but alerts not firing"**
1. Check `alert_config` table has alert enabled (`enabled = true`)
2. Verify metric name matches actual metric (from Prometheus)
3. Check alert history in `alert_history` table
4. Review Admin API logs for errors

### Permission Denied

**"You don't have permission to restart services"**
- Check your user role in `admin_users` table
- Verify role has `restart_services` permission in `admin_roles` table
- Contact Super Admin to update permissions

---

## 📅 Maintenance

### Daily
- Check dashboard health status
- Review recent alerts
- Verify budget utilization

### Weekly
- Review audit log for unusual activity
- Check model accuracy trends (SyncValue)
- Review service latency trends

### Monthly
- Export audit log for compliance
- Review alert false positive rate
- Archive old logs (> 90 days)

---

## 🎯 Next Steps

1. ✅ Deploy Admin API to production
2. ✅ Configure RBAC roles for your team
3. ✅ Set up alert notifications
4. ✅ Configure HTTPS/TLS
5. ✅ Integrate with log aggregation (ELK, Splunk)
6. ✅ Set up automated backups
7. ✅ Train team on dashboard usage

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review Admin API logs
3. Check database audit trail
4. Contact platform team

---

**Version:** 1.0.0  
**Last Updated:** January 20, 2026  
**Status:** Production Ready ✅
