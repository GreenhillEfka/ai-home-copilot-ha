#!/bin/bash
# Activity Logger - logs to both Telegram and React Board

# Get parameters
TYPE="${1:-update}"
TITLE="$2"
DESCRIPTION="$3"
BADGE="${4:-📋}"

# React Board API
REACT_BOARD_API="http://localhost:3001/api/activity"

# Log to React Board
curl -s -X POST "$REACT_BOARD_API" \
    -H "Content-Type: application/json" \
    -d "{\"type\": \"$TYPE\", \"title\": \"$TITLE\", \"description\": \"$DESCRIPTION\", \"badge\": \"$BADGE\"}" \
    > /dev/null 2>&1 &

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Activity logged: $TITLE"

# Exit immediately (curl runs in background)
exit 0
