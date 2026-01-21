# Database Migrations Guide

## Overview

This directory contains versioned SQL migrations for the KIKI platform database. Each migration is designed to be idempotent and reversible.

## Migration Files

| Migration | Description | Services |
|-----------|-------------|----------|
| `001_initial_schema.sql` | Initial audit_log table with TimescaleDB | SyncFlow, SyncValue |
| `002_add_creative_tracking.sql` | Creative assets tracking | SyncCreate |
| `003_add_customer_retention.sql` | Retention events and churn prediction | SyncEngage |
| `004_add_budget_governance.sql` | Real-time budget tracking | SyncShield |

---

## Migration Strategy

### Up Migration (Apply)

```bash
# Apply all migrations
psql -h localhost -U kiki_admin -d kiki_platform -f db/migrations/001_initial_schema.sql
psql -h localhost -U kiki_admin -d kiki_platform -f db/migrations/002_add_creative_tracking.sql
psql -h localhost -U kiki_admin -d kiki_platform -f db/migrations/003_add_customer_retention.sql
psql -h localhost -U kiki_admin -d kiki_platform -f db/migrations/004_add_budget_governance.sql
```

### Down Migration (Rollback)

Each migration has a `Migration Down` section at the bottom for rollback.

```bash
# Rollback specific migration
psql -h localhost -U kiki_admin -d kiki_platform -c "BEGIN; DROP TABLE IF EXISTS budget_allocations CASCADE; DROP TABLE IF EXISTS budget_transactions CASCADE; COMMIT;"
```

---

## Using Migration Tools

### Flyway (Recommended)

1. **Install Flyway:**

   ```bash
   wget -qO- https://repo1.maven.org/maven2/org/flywaydb/flyway-commandline/9.22.3/flyway-commandline-9.22.3-linux-x64.tar.gz | tar xvz
   ```

2. **Configure `flyway.conf`:**

   ```properties
   flyway.url=jdbc:postgresql://localhost:5432/kiki_platform
   flyway.user=kiki_admin
   flyway.password=${POSTGRES_PASSWORD}
   flyway.schemas=public
   flyway.locations=filesystem:db/migrations
   ```

3. **Run Migrations:**

   ```bash
   ./flyway migrate
   ./flyway info      # Check migration status
   ./flyway validate  # Validate checksums
   ```

### Liquibase

1. **Create `liquibase.properties`:**

   ```properties
   changeLogFile=db/changelog.xml
   url=jdbc:postgresql://localhost:5432/kiki_platform
   username=kiki_admin
   password=${POSTGRES_PASSWORD}
   ```

2. **Run Migrations:**

   ```bash
   liquibase update
   liquibase rollback --count=1
   liquibase status
   ```

### Golang Migrate

```bash
# Install
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Run migrations
migrate -path db/migrations -database "postgresql://kiki_admin:password@localhost:5432/kiki_platform?sslmode=disable" up

# Rollback
migrate -path db/migrations -database "postgresql://..." down 1
```

---

## Docker Setup

### Start PostgreSQL + TimescaleDB

```bash
docker run -d \
  --name kiki-postgres \
  -e POSTGRES_DB=kiki_platform \
  -e POSTGRES_USER=kiki_admin \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -v kiki_pgdata:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg15
```

### Apply Migrations in Docker

```bash
# Copy migration files to container
docker cp db/migrations kiki-postgres:/tmp/migrations

# Execute migrations
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -f /tmp/migrations/001_initial_schema.sql
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -f /tmp/migrations/002_add_creative_tracking.sql
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -f /tmp/migrations/003_add_customer_retention.sql
docker exec -it kiki-postgres psql -U kiki_admin -d kiki_platform -f /tmp/migrations/004_add_budget_governance.sql
```

---

## Kubernetes Deployment

### Using Init Container

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: kiki-db-migrations
  namespace: kiki
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: flyway/flyway:9-alpine
        env:
        - name: FLYWAY_URL
          value: "jdbc:postgresql://kiki-postgres:5432/kiki_platform"
        - name: FLYWAY_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: FLYWAY_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        volumeMounts:
        - name: migrations
          mountPath: /flyway/sql
      volumes:
      - name: migrations
        configMap:
          name: kiki-migrations
      restartPolicy: Never
```

### Create ConfigMap

```bash
kubectl create configmap kiki-migrations \
  --from-file=db/migrations \
  --namespace=kiki
```

---

## Testing Migrations

### Test Schema Creation

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check hypertables (TimescaleDB)
SELECT hypertable_name, num_dimensions 
FROM timescaledb_information.hypertables;

-- Check indexes
SELECT tablename, indexname 
FROM pg_indexes 
WHERE schemaname = 'public';
```

### Test Data Integrity

```sql
-- Test immutability trigger
INSERT INTO audit_log (request_id, customer_id, bid_amount, bid_source, platform, bid_status)
VALUES ('test_001', 'cust_123', 10.50, 'AI_PREDICTION', 'google_ads', 'ACCEPTED');

-- This should FAIL (immutability enforced)
UPDATE audit_log SET bid_amount = 20.00 WHERE request_id = 'test_001';

-- Clean up test data
DELETE FROM audit_log WHERE request_id = 'test_001';
```

### Test Budget Triggers

```sql
-- Create test budget
INSERT INTO budget_allocations (allocation_id, customer_id, campaign_id, total_budget, allocated_budget, start_date, end_date)
VALUES ('budget_test_001', 'cust_123', 'camp_456', 1000.00, 1000.00, NOW(), NOW() + INTERVAL '30 days');

-- Test transaction (should update spent_amount)
INSERT INTO budget_transactions (transaction_id, allocation_id, transaction_type, amount, balance_before, balance_after, approved)
VALUES ('txn_001', 'budget_test_001', 'bid', 850.00, 1000.00, 150.00, TRUE);

-- Check warning triggered (should have last_warning_at populated)
SELECT allocation_id, spent_amount, last_warning_at, last_critical_at 
FROM budget_allocations 
WHERE allocation_id = 'budget_test_001';

-- Clean up
DELETE FROM budget_transactions WHERE allocation_id = 'budget_test_001';
DELETE FROM budget_allocations WHERE allocation_id = 'budget_test_001';
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Database Migrations

on:
  push:
    branches: [main]
    paths:
      - 'db/migrations/**'

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Flyway
        uses: joshuaavalon/flyway-action@v3
        with:
          url: jdbc:postgresql://${{ secrets.DB_HOST }}:5432/${{ secrets.DB_NAME }}
          user: ${{ secrets.DB_USER }}
          password: ${{ secrets.DB_PASSWORD }}
      
      - name: Run Migrations
        run: flyway migrate
      
      - name: Verify Migrations
        run: flyway validate
```

---

## Production Checklist

- [ ] **Backup Database:** Always backup before migrations
- [ ] **Test in Staging:** Run migrations in staging environment first
- [ ] **Read-Only Mode:** Consider setting DB to read-only during migration
- [ ] **Rollback Plan:** Document rollback steps
- [ ] **Performance Impact:** Estimate migration time for large tables
- [ ] **Zero-Downtime:** For production, use Blue-Green deployment
- [ ] **Monitoring:** Watch for deadlocks, long queries, connection pools

### Backup Before Migration

```bash
# Full backup
pg_dump -h localhost -U kiki_admin -F c -b -v -f "kiki_backup_$(date +%Y%m%d_%H%M%S).dump" kiki_platform

# Schema-only backup
pg_dump -h localhost -U kiki_admin -s -f "kiki_schema_$(date +%Y%m%d).sql" kiki_platform
```

### Restore from Backup

```bash
# Restore full backup
pg_restore -h localhost -U kiki_admin -d kiki_platform -v kiki_backup_20260120_120000.dump

# Restore schema only
psql -h localhost -U kiki_admin -d kiki_platform -f kiki_schema_20260120.sql
```

---

## Troubleshooting

### Migration Failed Mid-Way

```sql
-- Check applied migrations
SELECT * FROM flyway_schema_history ORDER BY installed_rank DESC;

-- Repair broken migration
flyway repair

-- Force version
flyway baseline --baseline-version=3
```

### Lock Contention

```sql
-- Check active locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Kill blocking queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction' 
AND query_start < NOW() - INTERVAL '5 minutes';
```

### TimescaleDB Not Available

```sql
-- Check extension
SELECT * FROM pg_extension WHERE extname = 'timescaledb';

-- Recreate extension (if missing)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

---

## Next Steps

1. **Create Migration Script:** Add `scripts/migrate.sh` for automation
2. **Add Seed Data:** Create `db/seeds/` for test data
3. **Document Schema:** Generate ER diagrams
4. **Performance Tuning:** Add indexes based on query patterns
5. **Monitoring:** Set up slow query logs

**Recommended Tools:**

- [SchemaSpy](https://schemaspy.org/) - Generate database documentation
- [pgAdmin](https://www.pgadmin.org/) - Database management GUI
- [DataGrip](https://www.jetbrains.com/datagrip/) - IDE for databases
