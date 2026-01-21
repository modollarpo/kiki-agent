# Database Migration Script for KIKI Platform (PowerShell)
# Usage: .\migrate.ps1 [up|down|status|validate|backup]

param(
    [Parameter(Position=0)]
    [ValidateSet('up','status','validate','backup')]
    [string]$Command = 'up'
)

# Configuration
$DB_HOST = $env:DB_HOST ?? "localhost"
$DB_PORT = $env:DB_PORT ?? "5432"
$DB_NAME = $env:DB_NAME ?? "kiki_platform"
$DB_USER = $env:DB_USER ?? "kiki_admin"
$DB_PASSWORD = $env:DB_PASSWORD ?? ""

$MIGRATIONS_DIR = "db/migrations"
$MIGRATION_TABLE = "schema_migrations"

# Set environment for psql
$env:PGPASSWORD = $DB_PASSWORD

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-DatabaseConnection {
    Write-Info "Checking database connection..."
    
    $result = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "✓ Database connection successful"
        return $true
    } else {
        Write-Error "✗ Cannot connect to database"
        Write-Error $result
        return $false
    }
}

function Initialize-Migrations {
    Write-Info "Initializing migration tracking..."
    
    $sql = @"
CREATE TABLE IF NOT EXISTS $MIGRATION_TABLE (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64),
    execution_time_ms INT
);
"@
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c $sql | Out-Null
    Write-Info "✓ Migration tracking initialized"
}

function Invoke-Migration {
    param([string]$FilePath)
    
    $version = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
    Write-Info "Applying migration: $version"
    
    # Check if already applied
    $checkSql = "SELECT COUNT(*) FROM $MIGRATION_TABLE WHERE version='$version';"
    $applied = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c $checkSql
    
    if ([int]$applied.Trim() -gt 0) {
        Write-Warn "Migration $version already applied, skipping"
        return
    }
    
    # Execute migration with timing
    $startTime = Get-Date
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $FilePath
    $endTime = Get-Date
    $executionTime = ($endTime - $startTime).TotalMilliseconds
    
    # Calculate checksum
    $checksum = (Get-FileHash -Path $FilePath -Algorithm MD5).Hash
    
    # Record migration
    $recordSql = @"
INSERT INTO $MIGRATION_TABLE (version, name, checksum, execution_time_ms) 
VALUES ('$version', '$([System.IO.Path]::GetFileName($FilePath))', '$checksum', $([int]$executionTime));
"@
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c $recordSql | Out-Null
    Write-Info "✓ Migration $version applied ($([int]$executionTime)ms)"
}

function Invoke-MigrateUp {
    Write-Info "Running migrations..."
    
    $files = Get-ChildItem -Path $MIGRATIONS_DIR -Filter "*.sql" | Sort-Object Name
    
    foreach ($file in $files) {
        Invoke-Migration -FilePath $file.FullName
    }
    
    Write-Info "✓ All migrations completed"
}

function Show-MigrationStatus {
    Write-Info "Migration status:"
    Write-Host ""
    
    $sql = @"
SELECT 
    version,
    name,
    applied_at,
    execution_time_ms || 'ms' AS execution_time
FROM $MIGRATION_TABLE
ORDER BY id;
"@
    
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c $sql
    
    Write-Host ""
    $total = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM $MIGRATION_TABLE;"
    Write-Info "Total migrations applied: $($total.Trim())"
}

function Test-Migrations {
    Write-Info "Validating migrations..."
    
    $errors = 0
    $files = Get-ChildItem -Path $MIGRATIONS_DIR -Filter "*.sql" | Sort-Object Name
    
    foreach ($file in $files) {
        $version = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $currentChecksum = (Get-FileHash -Path $file.FullName -Algorithm MD5).Hash
        
        $storedChecksum = psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT checksum FROM $MIGRATION_TABLE WHERE version='$version';"
        $storedChecksum = $storedChecksum.Trim()
        
        if ($storedChecksum -and $currentChecksum -ne $storedChecksum) {
            Write-Error "✗ Checksum mismatch for $version"
            $errors++
        } elseif ($storedChecksum) {
            Write-Info "✓ $version validated"
        }
    }
    
    if ($errors -eq 0) {
        Write-Info "✓ All migrations validated successfully"
        return $true
    } else {
        Write-Error "✗ Validation failed with $errors errors"
        return $false
    }
}

function Backup-Database {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backups/kiki_backup_$timestamp.dump"
    
    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }
    
    Write-Info "Creating backup: $backupFile"
    
    pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -F c -b -v -f $backupFile $DB_NAME
    
    if ($LASTEXITCODE -eq 0) {
        Write-Info "✓ Backup created successfully"
        return $backupFile
    } else {
        Write-Error "✗ Backup failed"
        return $null
    }
}

# Main execution
switch ($Command) {
    'up' {
        if (Test-DatabaseConnection) {
            Initialize-Migrations
            Invoke-MigrateUp
        } else {
            exit 1
        }
    }
    'status' {
        if (Test-DatabaseConnection) {
            Initialize-Migrations
            Show-MigrationStatus
        } else {
            exit 1
        }
    }
    'validate' {
        if (Test-DatabaseConnection) {
            Initialize-Migrations
            if (-not (Test-Migrations)) {
                exit 1
            }
        } else {
            exit 1
        }
    }
    'backup' {
        if (Test-DatabaseConnection) {
            $backupPath = Backup-Database
            if (-not $backupPath) {
                exit 1
            }
        } else {
            exit 1
        }
    }
}
