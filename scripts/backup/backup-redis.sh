#!/bin/bash

# Redis Backup Script
set -e

BACKUP_DIR=${BACKUP_DIR:-"./backups/redis"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="redis_backup_${TIMESTAMP}.rdb"

echo "Starting Redis backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Trigger Redis background save
echo "Triggering Redis BGSAVE..."
docker-compose exec -T redis redis-cli BGSAVE

# Wait for background save to complete
echo "Waiting for backup to complete..."
while [ "$(docker-compose exec -T redis redis-cli LASTSAVE)" = "$(docker-compose exec -T redis redis-cli LASTSAVE)" ]; do
    sleep 1
done

# Copy RDB file from container
echo "Copying RDB file..."
docker-compose exec -T redis cat /data/dump.rdb > "$BACKUP_DIR/$BACKUP_FILE"

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
find "$BACKUP_DIR" -name "redis_backup_*.rdb" -mtime +$RETENTION_DAYS -delete

# List current backups
echo "Current backups:"
ls -lh "$BACKUP_DIR"/redis_backup_*.rdb 2>/dev/null || echo "No backups found"

echo "Redis backup completed successfully!"