#!/bin/bash
BACKUP_DIR="/backups/vt-view-tester"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR/$DATE

# Backup database
cp data/vt_database.db $BACKUP_DIR/$DATE/

# Backup accounts
cp -r data/accounts $BACKUP_DIR/$DATE/

# Backup proxies
cp -r data/proxies $BACKUP_DIR/$DATE/

# Backup configuration
cp config.py $BACKUP_DIR/$DATE/

# Compress backup
tar -czf $BACKUP_DIR/vt_backup_$DATE.tar.gz -C $BACKUP_DIR/$DATE .

# Remove uncompressed backup
rm -rf $BACKUP_DIR/$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: vt_backup_$DATE.tar.gz"