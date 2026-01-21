# Database Configuration Guide

## Quick Start

### 1. Start PostgreSQL + TimescaleDB

```powershell
# Using Docker Compose (Recommended)
docker-compose up -d postgres

# Wait for database to be ready
docker-compose logs -f postgres
```

### 2. Apply Migrations

```powershell
# Option A: Automated script
.\scripts\migrate.ps1 up

# Option B: Manual (PowerShell)
$env:DB_PASSWORD = "kiki_dev_password"
.\scripts\migrate.ps1 up

# Option C: Direct psql
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -f /docker-entrypoint-initdb.d/audit_trail.sql
```

### 3. Verify Setup

```powershell
# Check tables
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -c "\dt"

# Check hypertables (TimescaleDB)
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -c "SELECT * FROM timescaledb_information.hypertables;"

# Test connection from services
docker-compose exec syncflow env | grep DB_
```

---

## Environment Variables

### Required Variables

```bash
# Database connection
DB_HOST=postgres              # Docker service name or hostname
DB_PORT=5432                  # PostgreSQL port
DB_NAME=kiki_platform         # Database name
DB_USER=kiki_admin            # Database user
DB_PASSWORD=your_password     # Database password (use secrets in prod!)

# Connection pool (optional, defaults shown)
DB_MAX_CONNECTIONS=20         # Max concurrent connections
DB_IDLE_CONNECTIONS=5         # Idle connections to maintain
DB_CONN_MAX_LIFETIME=300s     # Max connection lifetime

# SSL (required for production)
DB_SSL_MODE=require           # Options: disable, require, verify-ca, verify-full
```

### Local Development

Create `.env` file:

```bash
cp .env.example .env
# Edit .env with your local settings
```

### Production

Use Kubernetes secrets:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kiki-db-credentials
type: Opaque
stringData:
  DB_HOST: kiki-prod-db.xxxxx.rds.amazonaws.com
  DB_PORT: "5432"
  DB_NAME: kiki_platform
  DB_USER: kiki_admin
  DB_PASSWORD: <from-secrets-manager>
```

---

## Connection Strings

### Go Services (SyncFlow, SyncShield, SyncEngage)

```go
import (
    "database/sql"
    "fmt"
    "os"
    _ "github.com/lib/pq"
)

// Build connection string
connStr := fmt.Sprintf(
    "host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
    os.Getenv("DB_HOST"),
    os.Getenv("DB_PORT"),
    os.Getenv("DB_USER"),
    os.Getenv("DB_PASSWORD"),
    os.Getenv("DB_NAME"),
    os.Getenv("DB_SSL_MODE"),
)

// Connect
db, err := sql.Open("postgres", connStr)
if err != nil {
    log.Fatal(err)
}
defer db.Close()

// Test connection
err = db.Ping()
if err != nil {
    log.Fatal("Cannot connect to database:", err)
}
```

### Python Services (SyncCreate, SyncValue AI)

```python
import os
import psycopg2
from psycopg2 import pool

# Create connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # min, max connections
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    sslmode=os.getenv('DB_SSL_MODE', 'disable')
)

# Get connection
conn = db_pool.getconn()
try:
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
finally:
    db_pool.putconn(conn)
```

---

## Database Schema

### Tables Overview

| Table | Purpose | Service | Hypertable |
|-------|---------|---------|------------|
| `audit_log` | Bid execution tracking | SyncFlow, SyncValue | ✅ |
| `creative_assets` | Creative generation tracking | SyncCreate | ✅ |
| `retention_events` | Customer retention events | SyncEngage | ✅ |
| `budget_allocations` | Campaign budgets | SyncShield | ❌ |
| `budget_transactions` | Real-time spending ledger | SyncShield | ✅ |
| `customer_cohorts` | Cohort analysis | SyncEngage | ❌ |

### Views

- `ltv_accuracy_realtime` - Real-time LTV prediction accuracy
- `circuit_breaker_stats` - Circuit breaker performance
- `budget_health_realtime` - Budget utilization health
- `churn_risk_realtime` - High-risk churn customers
- `creative_ab_performance` - A/B test results

---

## Production Deployment

### AWS RDS (Recommended)

```bash
# Create RDS PostgreSQL instance with TimescaleDB
# Note: Use custom parameter group with TimescaleDB extension enabled

aws rds create-db-instance \
  --db-instance-identifier kiki-prod-db \
  --db-instance-class db.r6g.2xlarge \
  --engine postgres \
  --engine-version 15.3 \
  --master-username kiki_admin \
  --master-user-password <from-secrets-manager> \
  --allocated-storage 500 \
  --storage-type gp3 \
  --storage-encrypted \
  --multi-az \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --vpc-security-group-ids sg-xxxxxx \
  --db-subnet-group-name kiki-db-subnet
```

### Google Cloud SQL

```bash
gcloud sql instances create kiki-prod-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-8-32768 \
  --region=us-central1 \
  --storage-size=500GB \
  --storage-type=SSD \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4
```

### Azure Database for PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group kiki-prod \
  --name kiki-prod-db \
  --location eastus \
  --admin-user kiki_admin \
  --admin-password <from-keyvault> \
  --sku-name Standard_D8s_v3 \
  --tier GeneralPurpose \
  --storage-size 512 \
  --version 15 \
  --high-availability Enabled \
  --backup-retention 30
```

---

## Monitoring

### Health Checks

```sql
-- Check database size
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) 
FROM pg_database;

-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'kiki_platform';

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check hypertable chunks (TimescaleDB)
SELECT * FROM timescaledb_information.chunks 
WHERE hypertable_name = 'audit_log';
```

### Performance Metrics

```sql
-- Slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Cache hit ratio (should be >99%)
SELECT 
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit)  as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

---

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify port binding
netstat -ano | findstr :5432

# Test connection manually
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform
```

### Migration Failures

```bash
# Check migration status
.\scripts\migrate.ps1 status

# Validate checksums
.\scripts\migrate.ps1 validate

# Rollback last migration
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -c "DROP TABLE budget_transactions CASCADE;"
```

### Performance Issues

```sql
-- Rebuild indexes
REINDEX DATABASE kiki_platform;

-- Vacuum and analyze
VACUUM ANALYZE;

-- Update statistics
ANALYZE;

-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY abs(correlation) DESC;
```

---

## Backup & Restore

### Backup

```bash
# Full backup
docker exec kiki-postgres pg_dump -U kiki_admin -F c -b -v -f /tmp/backup.dump kiki_platform

# Copy from container
docker cp kiki-postgres:/tmp/backup.dump ./backups/kiki_backup_$(date +%Y%m%d).dump

# Using migration script
.\scripts\migrate.ps1 backup
```

### Restore

```bash
# Copy to container
docker cp ./backups/kiki_backup_20260120.dump kiki-postgres:/tmp/restore.dump

# Restore
docker exec kiki-postgres pg_restore -U kiki_admin -d kiki_platform -v /tmp/restore.dump
```

---

## Security Checklist

- [ ] Change default password from `kiki_dev_password`
- [ ] Use SSL/TLS in production (`DB_SSL_MODE=require`)
- [ ] Store passwords in secrets manager (AWS Secrets Manager, HashiCorp Vault)
- [ ] Enable encryption at rest (RDS: `--storage-encrypted`)
- [ ] Configure VPC security groups (whitelist only service IPs)
- [ ] Enable audit logging (`log_statement = 'all'`)
- [ ] Set up automated backups (30 day retention minimum)
- [ ] Configure point-in-time recovery
- [ ] Implement read replicas for scaling
- [ ] Use connection pooling (PgBouncer/pgpool)

---

## Next Steps

1. **Start Database:**
   ```powershell
   docker-compose up -d postgres
   ```

2. **Apply Migrations:**
   ```powershell
   .\scripts\migrate.ps1 up
   ```

3. **Update Services:**
   - Add database connection code to Go/Python services
   - Implement audit logging in SyncFlow
   - Add creative tracking in SyncCreate
   - Enable retention events in SyncEngage

4. **Test Integration:**
   ```powershell
   docker-compose up -d
   docker-compose logs -f
   ```
