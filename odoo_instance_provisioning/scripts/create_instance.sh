#!/bin/bash

# Script to create new Odoo instance
# Usage: ./create_instance.sh <db_name> <admin_email> <admin_password> <company_name>

set -e  # Exit on any error

# Set locale to avoid perl warnings
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Parse arguments
DB_NAME="$1"
ADMIN_EMAIL="$2"
ADMIN_PASSWORD="$3"
COMPANY_NAME="$4"

# Configuration - use environment variables from Odoo
ODOO_USER="${PGUSER:-odoo}"
ODOO_PASSWORD="${PGPASSWORD:-odoo}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"

# Detect if we're in a containerized environment
if [ -f "/usr/bin/odoo" ]; then
    ODOO_PATH="/usr/bin"
    ODOO_BIN="odoo"
    ADDONS_PATH="${ADDONS_PATH:-/mnt/extra-addons}"
elif [ -f "/opt/odoo/odoo-bin" ]; then
    ODOO_PATH="/opt/odoo"
    ODOO_BIN="odoo-bin"
    ADDONS_PATH="${ADDONS_PATH:-/opt/odoo/addons}"
elif command -v odoo >/dev/null 2>&1; then
    ODOO_PATH=$(dirname $(which odoo))
    ODOO_BIN="odoo"
    ADDONS_PATH="${ADDONS_PATH:-/mnt/extra-addons}"
else
    # Default fallback
    ODOO_PATH="${ODOO_PATH:-/opt/odoo}"
    ODOO_BIN="odoo-bin"
    ADDONS_PATH="${ADDONS_PATH:-/opt/odoo/addons}"
fi

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
    
    # In containerized environments, try direct execution first
    if [ -n "$PGHOST" ] && [ "$PGHOST" != "localhost" ]; then
        # Running in containerized environment, use psql with environment variables
        export PGUSER="$ODOO_USER"
        export PGPASSWORD="$ODOO_PASSWORD"
        export PGHOST="$DB_HOST"
        export PGPORT="$DB_PORT"
        $cmd
    elif command -v sudo >/dev/null 2>&1 && id postgres >/dev/null 2>&1; then
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
        # Default to postgres database for administrative operations
        echo "$sql_cmd" | psql -d postgres
    fi
}

# Function to check PostgreSQL connection
check_postgres_connection() {
    log "Checking PostgreSQL connection to $DB_HOST:$DB_PORT"
    
    # Set environment variables for connection
    export PGUSER="$ODOO_USER"
    export PGPASSWORD="$ODOO_PASSWORD"
    export PGHOST="$DB_HOST"
    export PGPORT="$DB_PORT"
    
    # Try to connect to PostgreSQL
    if ! psql -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        error_exit "Cannot connect to PostgreSQL server at $DB_HOST:$DB_PORT. Please check if PostgreSQL container is running and accessible."
    fi
    
    log "PostgreSQL connection successful"
}

# Validate arguments
if [ -z "$DB_NAME" ] || [ -z "$ADMIN_EMAIL" ] || [ -z "$ADMIN_PASSWORD" ] || [ -z "$COMPANY_NAME" ]; then
    error_exit "Usage: $0 <db_name> <admin_email> <admin_password> <company_name>"
fi

log "Starting instance creation for database: $DB_NAME"
log "Database host: $DB_HOST:$DB_PORT"
log "Database user: $ODOO_USER"

# Check PostgreSQL connection first
check_postgres_connection

# Check if database already exists
log "Checking if database exists"
if run_psql_cmd "" "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null | grep -q 1; then
    log "WARNING: Database '$DB_NAME' already exists - using existing database"
    log "Instance database setup completed (database already exists)"
    exit 0
fi

# Create PostgreSQL database
log "Creating PostgreSQL database: $DB_NAME"
if [ -n "$PGHOST" ] && [ "$PGHOST" != "localhost" ]; then
    # In containerized environment, use SQL to create database
    log "Using SQL CREATE DATABASE command for containerized environment"
    run_psql_cmd "" "CREATE DATABASE \"$DB_NAME\";" || error_exit "Failed to create database"
else
    # Traditional createdb command
    log "Using createdb command for local environment"
    run_postgres_cmd "createdb '$DB_NAME'" || error_exit "Failed to create database"
fi

# Verify database was created
log "Verifying database creation"
if run_psql_cmd "" "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null | grep -q 1; then
    log "✅ Database '$DB_NAME' successfully created and verified"
else
    error_exit "Database '$DB_NAME' was not created properly"
fi

# Grant privileges to Odoo user
log "Granting privileges to Odoo user"
run_psql_cmd "" "GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO $ODOO_USER;" || error_exit "Failed to grant privileges"

# Initialize Odoo database
log "Initializing Odoo database"
log "Using Odoo binary: $ODOO_PATH/$ODOO_BIN"
log "Using addons path: $ADDONS_PATH"

# Check if Odoo binary exists
if [ ! -f "$ODOO_PATH/$ODOO_BIN" ] && ! command -v "$ODOO_BIN" >/dev/null 2>&1; then
    log "WARNING: Odoo binary not found at $ODOO_PATH/$ODOO_BIN and not in PATH"
    log "Skipping Odoo initialization - database created but not initialized"
    log "Manual initialization will be required through Odoo interface"
else
    # Use python3 with full path or direct command
    if [ -f "$ODOO_PATH/$ODOO_BIN" ]; then
        python3 "$ODOO_PATH/$ODOO_BIN" \
            -d "$DB_NAME" \
            --db_host="$DB_HOST" \
            --db_port="$DB_PORT" \
            --db_user="$ODOO_USER" \
            --db_password="$ODOO_PASSWORD" \
            --init=base \
            --stop-after-init \
            --no-http \
            --addons-path="$ADDONS_PATH" || error_exit "Failed to initialize Odoo database"
    else
        # Use odoo command directly (containerized environment)
        "$ODOO_BIN" \
            -d "$DB_NAME" \
            --db_host="$DB_HOST" \
            --db_port="$DB_PORT" \
            --db_user="$ODOO_USER" \
            --db_password="$ODOO_PASSWORD" \
            --init=base \
            --stop-after-init \
            --no-http \
            --addons-path="$ADDONS_PATH" || error_exit "Failed to initialize Odoo database"
    fi
    
    log "Database '$DB_NAME' created and initialized successfully"
    
    # Update admin user
    log "Updating admin user configuration"
    run_psql_cmd "$DB_NAME" "
        UPDATE res_users 
        SET login = '$ADMIN_EMAIL', 
            email = '$ADMIN_EMAIL', 
            password = crypt('$ADMIN_PASSWORD', gen_salt('bf')) 
        WHERE id = 2;
    " || error_exit "Failed to update admin user"

    # Update company name
    log "Updating company information"
    run_psql_cmd "$DB_NAME" "
        UPDATE res_company 
        SET name = '$COMPANY_NAME' 
        WHERE id = 1;
    " || error_exit "Failed to update company name"

    log "Instance creation completed successfully for database: $DB_NAME"
    log "Admin credentials: $ADMIN_EMAIL / $ADMIN_PASSWORD"
fi

log "Database setup completed for: $DB_NAME"
