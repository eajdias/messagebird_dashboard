#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

docker exec mbird_postgres pg_dump -U mbird -d mbird_reports \
	--no-owner --no-acl |
	gzip >"$BACKUP_DIR/mbird_reports_$TIMESTAMP.sql.gz"

echo "Backup saved: $BACKUP_DIR/mbird_reports_$TIMESTAMP.sql.gz"
