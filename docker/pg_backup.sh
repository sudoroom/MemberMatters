#!/bin/bash -e -o pipefail

# Setup
BACKUP_BASE=/opt/member-matters/postgres/backups
DATA_DIR=/opt/member-matters/postgres/data
WAL_DIR=/opt/member-matters/postgres/wal_archive
CONTAINER=docker-mm-postgres-1
DB=membermatters
USER=membermatters
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FOLDER=$BACKUP_BASE/$TIMESTAMP

mkdir -p $BACKUP_FOLDER

echo "🧠 Backing up base DB..."
docker exec -t $CONTAINER pg_basebackup -U $USER -D - -Ft -X fetch -z > "$BACKUP_FOLDER/base.tar.gz"

echo "🔁 Backing up WAL files..."
cp -r $WAL_DIR "$BACKUP_FOLDER/wal_archive"

echo "🗑 Deleting backups older than 7 days..."
find $BACKUP_BASE -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
