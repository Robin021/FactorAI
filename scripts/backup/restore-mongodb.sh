#!/bin/bash

# MongoDB Restore Script
set -e

BACKUP_FILE=${1}
BACKUP_DIR=${BACKUP_DIR:-"./backups/mongodb"}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/mongodb_backup_*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

echo "Starting MongoDB restore from: $BACKUP_FILE"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_DIR/$BACKUP_FILE" -C "$TEMP_DIR"

# Confirm restore operation
echo "⚠️  WARNING: This will replace all data in the MongoDB database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop application services to prevent data corruption
echo "Stopping application services..."
docker-compose stop backend frontend

# Perform restore
echo "Restoring MongoDB data..."
docker-compose exec -T mongodb mongorestore --drop --gzip "$TEMP_DIR/dump"

# Start application services
echo "Starting application services..."
docker-compose start backend frontend

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Verify restore
if docker-compose exec -T mongodb mongo --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo "✅ MongoDB restore completed successfully!"
else
    echo "❌ MongoDB restore failed - database may be corrupted"
    exit 1
fi