# Apply Database Migration
# Usage: .\apply_migration.ps1 -MigrationFile "004_add_edge_query_indexes.sql"

param(
    [Parameter(Mandatory=$true)]
    [string]$MigrationFile
)

# Load environment variables
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

$dbHost = $env:DB_HOST
$dbPort = $env:DB_PORT
$dbName = $env:DB_NAME
$dbUser = $env:DB_USER
$dbPassword = $env:DB_PASSWORD

if (-not $dbHost) {
    Write-Error "Database configuration not found in .env file"
    exit 1
}

$migrationPath = Join-Path "database\migrations" $MigrationFile

if (-not (Test-Path $migrationPath)) {
    Write-Error "Migration file not found: $migrationPath"
    exit 1
}

Write-Host "Applying migration: $MigrationFile" -ForegroundColor Cyan
Write-Host "Database: $dbName@${dbHost}:${dbPort}" -ForegroundColor Yellow

# Set PGPASSWORD environment variable
$env:PGPASSWORD = $dbPassword

try {
    # Execute migration using psql
    $output = & psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -f $migrationPath 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Migration applied successfully!" -ForegroundColor Green
        Write-Host $output

        # Verify indexes were created
        Write-Host "`nVerifying indexes..." -ForegroundColor Cyan
        $verifyQuery = @"
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'sim_network_edges' AND schemaname = 'dim'
ORDER BY indexname;
"@

        $indexOutput = echo $verifyQuery | & psql -h $dbHost -p $dbPort -U $dbUser -d $dbName 2>&1
        Write-Host $indexOutput

    } else {
        Write-Error "Migration failed with exit code $LASTEXITCODE"
        Write-Host $output -ForegroundColor Red
        exit 1
    }
} finally {
    # Clear password from environment
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
