#!/usr/bin/env bash
# Database Migration Script for KIKI Platform
# Usage: ./migrate.sh [up|down|status|validate]

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-kiki_platform}"
DB_USER="${DB_USER:-kiki_admin}"
DB_PASSWORD="${DB_PASSWORD:-}"

MIGRATIONS_DIR="db/migrations"
MIGRATION_TABLE="schema_migrations"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check PostgreSQL connection
check_connection() {
    log_info "Checking database connection..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        log_info "✓ Database connection successful"
        return 0
    else
        log_error "✗ Cannot connect to database"
        return 1
    fi
}

# Create migration tracking table
init_migrations() {
    log_info "Initializing migration tracking..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
CREATE TABLE IF NOT EXISTS $MIGRATION_TABLE (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time_ms INT
);
EOF
    log_info "✓ Migration tracking initialized"
}

# Apply migration
apply_migration() {
    local file=$1
    local version=$(basename "$file" .sql)
    
    log_info "Applying migration: $version"
    
    # Check if already applied
    local applied=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $MIGRATION_TABLE WHERE version='$version';")
    
    if [ "$applied" -gt 0 ]; then
        log_warn "Migration $version already applied, skipping"
        return 0
    fi
    
    # Execute migration with timing
    local start_time=$(date +%s%3N)
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$file"
    local end_time=$(date +%s%3N)
    local execution_time=$((end_time - start_time))
    
    # Calculate checksum
    local checksum=$(md5sum "$file" | awk '{print $1}')
    
    # Record migration
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
        "INSERT INTO $MIGRATION_TABLE (version, name, checksum, execution_time_ms) VALUES ('$version', '$(basename $file)', '$checksum', $execution_time);"
    
    log_info "✓ Migration $version applied (${execution_time}ms)"
}

# Migrate up (apply all pending migrations)
migrate_up() {
    log_info "Running migrations..."
    
    for file in $(ls -1 $MIGRATIONS_DIR/*.sql | sort); do
        apply_migration "$file"
    done
    
    log_info "✓ All migrations completed"
}

# Show migration status
show_status() {
    log_info "Migration status:"
    echo ""
    
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
SELECT 
    version,
    name,
    applied_at,
    execution_time_ms || 'ms' AS execution_time
FROM $MIGRATION_TABLE
ORDER BY id;
EOF
    
    echo ""
    local total=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM $MIGRATION_TABLE;")
    log_info "Total migrations applied: $total"
}

# Validate migrations (check checksums)
validate_migrations() {
    log_info "Validating migrations..."
    
    local errors=0
    for file in $(ls -1 $MIGRATIONS_DIR/*.sql | sort); do
        local version=$(basename "$file" .sql)
        local current_checksum=$(md5sum "$file" | awk '{print $1}')
        
        local stored_checksum=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
            "SELECT checksum FROM $MIGRATION_TABLE WHERE version='$version';" | tr -d ' ')
        
        if [ -n "$stored_checksum" ] && [ "$current_checksum" != "$stored_checksum" ]; then
            log_error "✗ Checksum mismatch for $version"
            errors=$((errors + 1))
        elif [ -n "$stored_checksum" ]; then
            log_info "✓ $version validated"
        fi
    done
    
    if [ $errors -eq 0 ]; then
        log_info "✓ All migrations validated successfully"
        return 0
    else
        log_error "✗ Validation failed with $errors errors"
        return 1
    fi
}

# Backup database
backup_database() {
    local backup_file="backups/kiki_backup_$(date +%Y%m%d_%H%M%S).dump"
    mkdir -p backups
    
    log_info "Creating backup: $backup_file"
    PGPASSWORD=$DB_PASSWORD pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -F c -b -v -f "$backup_file" "$DB_NAME"
    
    if [ $? -eq 0 ]; then
        log_info "✓ Backup created successfully"
        echo "$backup_file"
    else
        log_error "✗ Backup failed"
        return 1
    fi
}

# Main
main() {
    local command=${1:-up}
    
    case $command in
        up)
            check_connection || exit 1
            init_migrations
            migrate_up
            ;;
        status)
            check_connection || exit 1
            init_migrations
            show_status
            ;;
        validate)
            check_connection || exit 1
            init_migrations
            validate_migrations
            ;;
        backup)
            check_connection || exit 1
            backup_database
            ;;
        *)
            echo "Usage: $0 {up|status|validate|backup}"
            echo ""
            echo "Commands:"
            echo "  up        - Apply all pending migrations"
            echo "  status    - Show migration history"
            echo "  validate  - Validate migration checksums"
            echo "  backup    - Create database backup"
            exit 1
            ;;
    esac
}

main "$@"
