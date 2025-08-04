#!/bin/bash

# Script to backup Odoo instance
# Usage: ./backup_instance.sh <db_name> [backup_dir]

set -e  # Exit on any error

# Set locale to avoid perl warnings
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Parse arguments
DB_NAME="$1"
BACKUP_DIR="${2:-/opt/odoo/backups}"

# Configuration
ODOO_USER="${PGUSER:-odoo}"
ODOO_PASSWORD="${PGPASSWORD:-odoo}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
FILESTORE_BACKUP="$BACKUP_DIR/${DB_NAME}_filestore_${TIMESTAMP}.tar.gz"

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
    error_exit "Usage: $0 <db_name> [backup_dir]"
fi

# Check if database exists
if ! run_psql_cmd "" "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" | grep -q 1; then
    error_exit "Database '$DB_NAME' does not exist"
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"

log "Starting backup for database: $DB_NAME"

# Backup database
log "Creating database backup: $BACKUP_FILE"
# Set environment variables for pg_dump
export PGUSER="$ODOO_USER"
export PGPASSWORD="$ODOO_PASSWORD"
export PGHOST="$DB_HOST"
export PGPORT="$DB_PORT"

pg_dump \
    --dbname="$DB_NAME" \
    --file="$BACKUP_FILE" \
    --verbose \
    --format=custom \
    --compress=9 || error_exit "Failed to backup database"

# Backup filestore
FILESTORE_PATH="/opt/odoo/data/filestore/$DB_NAME"
if [ -d "$FILESTORE_PATH" ]; then
    log "Creating filestore backup: $FILESTORE_BACKUP"
    tar -czf "$FILESTORE_BACKUP" -C "/opt/odoo/data/filestore" "$DB_NAME" || error_exit "Failed to backup filestore"
else
    log "Filestore directory not found, skipping filestore backup"
fi

# Verify backup files
if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Database backup file not created"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Database backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

if [ -f "$FILESTORE_BACKUP" ]; then
    FILESTORE_SIZE=$(du -h "$FILESTORE_BACKUP" | cut -f1)
    log "Filestore backup completed: $FILESTORE_BACKUP ($FILESTORE_SIZE)"
fi

# Create backup info file
INFO_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.info"
cat > "$INFO_FILE" << EOF
Database Name: $DB_NAME
Backup Date: $(date '+%Y-%m-%d %H:%M:%S')
Database Backup: $BACKUP_FILE
Database Size: $BACKUP_SIZE
Filestore Backup: ${FILESTORE_BACKUP:-"Not available"}
Filestore Size: ${FILESTORE_SIZE:-"Not available"}
Host: $(hostname)
Odoo Version: $(python3 /opt/odoo/odoo-bin --version 2>/dev/null | head -n1 || echo "Unknown")
EOF

log "Backup info saved: $INFO_FILE"

# Cleanup old backups (keep last 7 days)
log "Cleaning up old backups (keeping last 7 days)"
find "$BACKUP_DIR" -name "${DB_NAME}_*.sql" -mtime +7 -delete || true
find "$BACKUP_DIR" -name "${DB_NAME}_filestore_*.tar.gz" -mtime +7 -delete || true
find "$BACKUP_DIR" -name "${DB_NAME}_*.info" -mtime +7 -delete || true

log "Backup process completed successfully for database: $DB_NAME"
