#!/bin/bash

# Script to drop Odoo instance database
# Usage: ./drop_database.sh <db_name>

set -e  # Exit on any error

# Set locale to avoid perl warnings
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Parse arguments
DB_NAME="$1"

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

# Function to run postgres commands
run_postgres_cmd() {
    local cmd="$1"
    
    # Try different methods to run postgres commands
    if command -v sudo >/dev/null 2>&1 && id postgres >/dev/null 2>&1; then
        # Traditional sudo approach
        sudo -u postgres $cmd
    elif [ "$USER" = "postgres" ] || [ "$USER" = "root" ]; then
        # Already running as postgres or root
        $cmd
    elif command -v su >/dev/null 2>&1 && id postgres >/dev/null 2>&1; then
        # Use su instead of sudo
        su - postgres -c "$cmd"
    else
        # Direct execution (for containerized environments)
        $cmd
    fi
}

# Function to run psql commands
run_psql_cmd() {
    local database="$1"
    local sql_cmd="$2"
    
    # Set environment variables for psql
    export PGUSER="$ODOO_USER"
    export PGPASSWORD="$ODOO_PASSWORD"
    export PGHOST="$DB_HOST"
    export PGPORT="$DB_PORT"
    
    if [ -n "$database" ]; then
        echo "$sql_cmd" | psql -d "$database"
    else
        echo "$sql_cmd" | psql
    fi
}

# Validate arguments
if [ -z "$DB_NAME" ]; then
    error_exit "Usage: $0 <db_name>"
fi

# Check if database exists
if ! run_psql_cmd "" "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1; then
    log "WARNING: Database '$DB_NAME' does not exist"
    exit 0
fi

log "Starting database removal for: $DB_NAME"

# Terminate active connections
log "Terminating active connections to database: $DB_NAME"
run_psql_cmd "" "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();
" || log "WARNING: Failed to terminate some connections"

# Drop database
log "Dropping database: $DB_NAME"
run_postgres_cmd "dropdb '$DB_NAME'" || error_exit "Failed to drop database"

# Remove filestore directory
FILESTORE_PATH="/opt/odoo/data/filestore/$DB_NAME"
if [ -d "$FILESTORE_PATH" ]; then
    log "Removing filestore directory: $FILESTORE_PATH"
    rm -rf "$FILESTORE_PATH" || error_exit "Failed to remove filestore directory"
else
    log "Filestore directory not found: $FILESTORE_PATH"
fi

# Remove sessions directory
SESSIONS_PATH="/opt/odoo/data/sessions/$DB_NAME"
if [ -d "$SESSIONS_PATH" ]; then
    log "Removing sessions directory: $SESSIONS_PATH"
    rm -rf "$SESSIONS_PATH" || error_exit "Failed to remove sessions directory"
else
    log "Sessions directory not found: $SESSIONS_PATH"
fi

log "Database '$DB_NAME' and associated files removed successfully"
