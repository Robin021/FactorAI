#!/bin/bash

# Redis Restore Script
set -e

BACKUP_FILE=${1}
BACKUP_DIR=${BACKUP_DIR:-"./backups/redis"}

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/redis_backup_*.rdb 2>/dev/null || echo "No backups found"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_DIR/$BACKUP_FILE"
    exit 1
fi

echo "Starting Redis restore from: $BACKUP_FILE"

# Confirm restore operation
echo "⚠️  WARNING: This will replace all data in the Redis database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled"
    exit 0
fi

# Stop Redis service
echo "Stopping Redis service..."
docker-compose stop redis

# Copy backup file to Redis data volume
echo "Copying backup file to Redis container..."
docker run --rm -v tradingagents_redis_data:/data -v "$BACKUP_DIR":/backup alpine \
    cp "/backup/$BACKUP_FILE" /data/dump.rdb

# Start Redis service
echo "Starting Redis service..."
docker-compose start redis

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
sleep 5

# Verify restore
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis restore completed successfully!"
else
    echo "❌ Redis restore failed"
    exit 1
fi