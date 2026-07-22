#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
	echo "Usage: $0 <backup-file.sql.gz>"
	echo "       $0 <backup-file.sql>"
	exit 1
fi

BACKUP_FILE="$1"

if [[ "$BACKUP_FILE" == *.gz ]]; then
	gunzip -c "$BACKUP_FILE" | docker exec -i mbird_postgres psql -U mbird -d mbird_reports
else
	docker exec -i mbird_postgres psql -U mbird -d mbird_reports <"$BACKUP_FILE"
fi

echo "Restore completed from: $BACKUP_FILE"
