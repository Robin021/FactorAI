#!/bin/bash

# MongoDB Backup Script
set -e

BACKUP_DIR=${BACKUP_DIR:-"./backups/mongodb"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mongodb_backup_${TIMESTAMP}.tar.gz"

echo "Starting MongoDB backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create temporary directory for backup
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Perform MongoDB dump
echo "Creating MongoDB dump..."
docker-compose exec -T mongodb mongodump --out "$TEMP_DIR/dump" --gzip

# Create compressed archive
echo "Creating compressed archive..."
tar -czf "$BACKUP_DIR/$BACKUP_FILE" -C "$TEMP_DIR" dump

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created successfully: $BACKUP_FILE ($BACKUP_SIZE)"
else
    echo "❌ Backup failed"
    exit 1
fi

# Clean up old backups
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "mongodb_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/mongodb_backup_*.tar.gz 2>/dev/null || echo "No backups found"

echo "MongoDB backup completed successfully!"