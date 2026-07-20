#!/bin/bash
set -e

API="http://localhost:8050"

echo "Getting JWT token..."
TOKEN=$(curl -s -X POST "$API/api/v1/auth/login" \
	-H "Content-Type: application/json" \
	-d '{"email":"admin@empresa.com","password":"admin123"}' |
	grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
	echo "ERROR: Failed to get token"
	exit 1
fi
echo "Token obtained: ${TOKEN:0:20}..."

for MONTH in 1 2 3 4 5 6; do
	echo ""
	echo "=== Sync month $MONTH/2026 ==="
	START=$(date +%s)
	RESULT=$(curl -s --max-time 600 -X POST "$API/api/v1/admin/sync/trigger" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $TOKEN" \
		-d "{\"full_sync\":false,\"sync_messages\":true,\"year\":2026,\"month\":$MONTH}")
	ELAPSED=$(($(date +%s) - START))
	echo "Result: $RESULT (${ELAPSED}s)"
done

echo ""
echo "=== Refreshing materialized view ==="
curl -s --max-time 60 -X POST "$API/api/v1/admin/sync/trigger" \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer $TOKEN" \
	-d '{"backfill_surveys":true}'
echo ""

echo ""
echo "=== ALL DONE ==="
