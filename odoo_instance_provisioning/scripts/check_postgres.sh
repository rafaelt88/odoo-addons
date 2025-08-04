#!/bin/bash

# Script to check PostgreSQL connection and configuration
# Usage: ./check_postgres.sh

set -e

# Set locale to avoid perl warnings
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Configuration
ODOO_USER="${PGUSER:-odoo}"
ODOO_PASSWORD="${PGPASSWORD:-odoo}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

log "Checking PostgreSQL connection and configuration"
log "Host: $DB_HOST"
log "Port: $DB_PORT"
log "User: $ODOO_USER"

# Set environment variables for psql
export PGUSER="$ODOO_USER"
export PGPASSWORD="$ODOO_PASSWORD"
export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"

# Check if PostgreSQL client tools are available
if ! command -v psql >/dev/null 2>&1; then
    error_exit "psql command not found. Please install PostgreSQL client tools."
fi

if ! command -v createdb >/dev/null 2>&1; then
    error_exit "createdb command not found. Please install PostgreSQL client tools."
fi

# Test PostgreSQL connection
log "Testing PostgreSQL connection..."
if ! psql -d postgres -c "SELECT version();" >/dev/null 2>&1; then
    log "ERROR: Cannot connect to PostgreSQL server"
    log "Common solutions:"
    log "1. Check if PostgreSQL container is running: docker ps | grep postgres"
    log "2. Check if PostgreSQL is listening on the correct port: netstat -nl | grep $DB_PORT"
    log "3. Check connection parameters: host=$DB_HOST, port=$DB_PORT, user=$ODOO_USER"
    log "4. For Docker Compose: ensure 'db' service is running and accessible"
    log "5. Check Docker network connectivity between containers"
    exit 1
fi

log "✅ PostgreSQL connection successful"

# Check PostgreSQL version
PG_VERSION=$(psql -d postgres -t -c "SELECT version();" | head -1 | awk '{print $2}')
log "PostgreSQL version: $PG_VERSION"

# Check if user can create databases
log "Testing database creation permissions..."
TEST_DB="test_connection_$(date +%s)"
if createdb "$TEST_DB" >/dev/null 2>&1; then
    log "✅ Database creation permissions OK"
    # Clean up test database
    dropdb "$TEST_DB" >/dev/null 2>&1 || log "Warning: Could not clean up test database"
else
    log "❌ User $ODOO_USER cannot create databases"
    log "Please ensure the user has CREATEDB privileges:"
    log "  ALTER USER $ODOO_USER CREATEDB;"
    exit 1
fi

# Check required extensions
log "Checking required PostgreSQL extensions..."
EXTENSIONS=("uuid-ossp" "unaccent")
for ext in "${EXTENSIONS[@]}"; do
    if psql -d postgres -t -c "SELECT 1 FROM pg_available_extensions WHERE name='$ext';" | grep -q 1; then
        log "✅ Extension $ext is available"
    else
        log "⚠️  Extension $ext is not available (may cause issues)"
    fi
done

log "🎉 PostgreSQL configuration check completed successfully!"
log "System is ready for Odoo instance provisioning."
