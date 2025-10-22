@echo off
REM Simple migration script for Windows
REM Usage: Set your database credentials below, then run this script

REM === CONFIGURE THESE VALUES ===
set DB_HOST=10.149.235.123
set DB_PORT=5432
set DB_NAME=sdzg
set DB_USER=your_username
set PGPASSWORD=your_password

REM === DO NOT MODIFY BELOW ===
echo Applying database migration...
echo Database: %DB_NAME%@%DB_HOST%:%DB_PORT%
echo.

psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f database\migrations\004_add_edge_query_indexes.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Migration applied successfully!
    echo.
    echo Verifying indexes...
    psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -c "SELECT indexname FROM pg_indexes WHERE tablename = 'sim_network_edges' AND schemaname = 'dim' ORDER BY indexname;"
) else (
    echo.
    echo [ERROR] Migration failed!
    exit /b 1
)

REM Clear password from environment
set PGPASSWORD=

pause
