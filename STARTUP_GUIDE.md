# 🚀 Complete Service Startup Guide

## Current Status: Ready for Full Deployment

### ✅ ALL SERVICES OPERATIONAL

| Service | Port | Status | Type | Database |
|---------|------|--------|------|----------|
| **SyncValue** | 50051 | ✅ Ready | gRPC | PostgreSQL |
| **SyncShield** | 8081 | ✅ Ready | HTTP | Redis + PostgreSQL |
| **SyncEngage** | 8083 | ✅ Ready | HTTP | PostgreSQL |
| **SyncCreate** | 8084 | ✅ Ready | HTTP | PostgreSQL |
| **SyncFlow** | 8082 | ✅ Ready | HTTP (Health) | PostgreSQL |
| **Billing OaaS** | — | 🔴 Pending | — | — |

---

## Quick Start (5 Minutes)

### Prerequisites
```powershell
# 1. Docker Desktop must be running
# 2. Verify Docker daemon
docker ps

# 3. If Docker not running on Windows
# - Click Start Menu → Search "Docker Desktop" → Launch
# - Wait 30-60 seconds for daemon to initialize
# - Verify: docker ps (should not show "cannot connect" error)
```

### Step 1: Start Database
```powershell
cd C:\Users\USER\Documents\KIKI

# Start PostgreSQL + TimescaleDB
docker-compose up -d postgres

# Wait for database to be ready (health check should pass)
docker-compose logs -f postgres | grep -i "accepting"
# Press Ctrl+C once you see "accepting connections"
```

### Step 2: Apply Database Migrations
```powershell
# Apply all migrations
.\scripts\migrate.ps1 up

# Verify migrations applied
.\scripts\migrate.ps1 status

# Expected output shows:
# - 001_initial_schema (audit_log table)
# - 002_add_creative_tracking (creative_assets)
# - 003_add_customer_retention (retention_events)
# - 004_add_budget_governance (budget_allocations)
```

### Step 3: Start All Microservices
```powershell
# Start all services (will use database just initialized)
docker-compose up -d

# Check all services running
docker-compose ps

# Expected: All containers showing "Up" status
```

### Step 4: Verify Health
```powershell
# Test each service

# 1. SyncShield (Budget Governance) - Port 8081
curl http://localhost:8081/health
# Response: 200 OK

# 2. SyncEngage (Retention) - Port 8083
curl http://localhost:8083/health
# Response: 200 OK

# 3. SyncCreate (Creative Gen) - Port 8084
curl http://localhost:8084/health
# Response: {"status": "healthy", "timestamp": "..."}

# 4. SyncFlow (Campaign Executor) - Port 8082
curl http://localhost:8082/health
# Response: OK

# 5. SyncValue (LTV AI) - gRPC Port 50051
docker-compose logs syncvalue | grep -i "ready\|listening\|online"
# Should see "Online" message
```

---

## Testing Each Service

### 1. Test SyncShield (Budget Governance)

```powershell
# Check budget allocation
curl -X POST http://localhost:8081/api/v1/allocate `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "cust_demo_001",
    "campaign_id": "camp_001",
    "total_budget": 1000,
    "allocated_budget": 1000,
    "start_date": "'$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')+'",
    "end_date": "'$(Get-Date -Add (New-TimeSpan -Days 30) -Format 'yyyy-MM-ddTHH:mm:ss')'",
    "daily_budget": 33.33
  }'

# Place bid with compliance check
curl -X POST http://localhost:8081/api/v1/check `
  -H "Content-Type: application/json" `
  -d '{
    "campaign_id": "camp_001",
    "bid_amount": 50,
    "platform": "google_ads",
    "customer_id": "cust_demo_001"
  }'

# Expected: 200 OK + budget check result
```

### 2. Test SyncEngage (Retention)

```powershell
# Get at-risk customers (churn risk > 50%)
curl "http://localhost:8083/api/v1/churn-risk?threshold=0.5"

# Send retention message
curl -X POST http://localhost:8083/api/v1/message `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "cust_demo_001",
    "channel": "email",
    "subject": "We miss you!",
    "message": "Come back for exclusive offer",
    "personalization": true
  }'

# Get customer segments
curl "http://localhost:8083/api/v1/segments"

# Expected: 200 OK + segment data
```

### 3. Test SyncCreate (Creative Generation)

```powershell
# Generate 3 creative variants
curl -X POST http://localhost:8084/api/v1/generate `
  -H "Content-Type: application/json" `
  -d '{
    "product": {
      "name": "CloudSync Pro",
      "category": "SaaS",
      "features": ["Real-time Sync", "End-to-End Encryption", "24/7 Support"],
      "usp": "10x faster than competitors"
    },
    "brand": {
      "name": "CloudSync",
      "primary_colors": ["#3b82f6"],
      "secondary_colors": ["#1e40af"],
      "tone_of_voice": "professional yet friendly"
    },
    "variants": 3,
    "platform": "tiktok_9_16"
  }'

# Validate creative compliance
curl -X POST http://localhost:8084/api/v1/validate `
  -H "Content-Type: application/json" `
  -d '{
    "image_url": "https://example.com/creative.jpg",
    "headline": "CloudSync Pro - Sync 10x Faster",
    "brand": {"name": "CloudSync"}
  }'

# Get Prometheus metrics
curl http://localhost:8084/metrics | head -20

# Expected: 200 OK + creative data + metrics
```

### 4. Test SyncFlow (Campaign Executor)

```powershell
# Check health
curl http://localhost:8082/health

# View logs (shows bidding decisions)
docker-compose logs syncflow -f

# Expected logs show:
# - "SyncFlow gRPC Agent Online"
# - "Platform Status: Connected"
# - "Bid decision: ACCEPT/REJECT"
# - Bid amounts and decisions every 2 seconds
```

### 5. Test Database Connection

```powershell
# Connect to PostgreSQL
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform

# Inside psql shell:
# Check tables
\dt

# Check hypertables (TimescaleDB)
SELECT hypertable_name FROM timescaledb_information.hypertables;

# View recent audit log entries
SELECT timestamp, customer_id, bid_amount, bid_status FROM audit_log LIMIT 10;

# Check budget allocations
SELECT allocation_id, customer_id, spent_amount, remaining_budget FROM budget_allocations LIMIT 5;

# Exit
\q
```

---

## Integration Test (End-to-End)

```powershell
# Simulate full workflow

# 1. Allocate budget
$allocation = curl -X POST http://localhost:8081/api/v1/allocate `
  -H "Content-Type: application/json" `
  -d '{...budget data...}'

# 2. Generate creatives
$creatives = curl -X POST http://localhost:8084/api/v1/generate `
  -H "Content-Type: application/json" `
  -d '{...product data...}'

# 3. Check at-risk customers
$atrisk = curl "http://localhost:8083/api/v1/churn-risk?threshold=0.7"

# 4. Trigger campaign execution (SyncFlow processes automatically every 2 seconds)
docker-compose logs syncflow -f | grep "ACCEPT"

# Expected: All services working together, audit trail recorded
```

---

## Monitoring & Debugging

### View Service Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f syncshield
docker-compose logs -f syncengage
docker-compose logs -f synccreate
docker-compose logs -f syncflow

# Last 100 lines
docker-compose logs --tail=100 syncvalue
```

### Check Service Health
```powershell
# Detailed status
docker-compose ps

# Resource usage
docker stats

# Network inspection
docker network ls
docker network inspect kiki_default

# Database connections
docker exec kiki-postgres psql -U kiki_admin -d kiki_platform -c "SELECT count(*) FROM pg_stat_activity;"
```

### Performance Metrics
```bash
# View Prometheus metrics (if Prometheus running)
curl http://localhost:9090/api/v1/query?query=up

# View specific service metrics
curl http://localhost:8084/metrics | grep syncflo
curl http://localhost:8081/metrics | grep budget

# View database metrics
docker exec kiki-postgres psql -U kiki_admin -d kiki_platform -c "SELECT * FROM pg_stat_database WHERE datname = 'kiki_platform';"
```

---

## Stopping Services

```powershell
# Stop all services (keep data)
docker-compose down

# Stop specific service
docker-compose stop syncvalue
docker-compose stop syncshield

# Remove all data (clean slate)
docker-compose down -v

# View stopped containers
docker ps -a
```

---

## Troubleshooting

### Service won't start
```powershell
# Check logs for errors
docker-compose logs <service-name>

# Rebuild image
docker-compose build <service-name>

# Force restart
docker-compose restart <service-name>

# Nuclear option: Remove container and restart
docker-compose rm -f <service-name>
docker-compose up -d <service-name>
```

### Database connection error
```powershell
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection from service
docker-compose exec syncflow psql -h postgres -U kiki_admin -d kiki_platform -c "SELECT 1;"

# Check port binding
netstat -ano | findstr :5432
```

### Port already in use
```powershell
# Find what's using port
netstat -ano | findstr :8081
# Kill process
taskkill /PID <PID> /F

# Or use different port in docker-compose.yml
# ports:
#   - "8085:8081"
```

### Out of memory
```powershell
# Increase Docker resources
# Docker Desktop → Settings → Resources → Memory: 8GB+

# Or check service memory usage
docker stats

# Limit specific service
# In docker-compose.yml:
# services:
#   synccreate:
#     mem_limit: 2g
```

---

## Production Checklist

Before deploying to production:

- [ ] Docker images pushed to container registry (GHCR, DockerHub, ECR)
- [ ] Environment variables configured in secrets manager
- [ ] Database backups automated (30-day retention)
- [ ] Monitoring & alerting set up (Prometheus + Grafana)
- [ ] SSL/TLS certificates configured
- [ ] Load testing completed (1000+ req/sec)
- [ ] Security audit completed
- [ ] Disaster recovery procedures documented
- [ ] Rollback plan created
- [ ] Communication plan to users

---

## Next Steps

1. **Start all services:**
   ```powershell
   .\scripts\migrate.ps1 up
   docker-compose up -d
   docker-compose ps
   ```

2. **Verify all healthy:**
   ```powershell
   curl http://localhost:8081/health
   curl http://localhost:8083/health
   curl http://localhost:8084/health
   curl http://localhost:8082/health
   ```

3. **Test each service** (see Testing section above)

4. **Implement Billing OaaS** (optional for MVP)

5. **Deploy to Kubernetes** (when ready for production)

---

**Status:** ✅ All 5 core services ready for deployment
**Estimated Time:** 5 minutes to startup, 15 minutes for full validation
**Support:** See [SERVICE_STATUS_REPORT.md](SERVICE_STATUS_REPORT.md) for detailed status
