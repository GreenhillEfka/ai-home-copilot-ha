#!/bin/bash
# React Board Auto-Start Script

cd /config/.openclaw/canvas/ReactBoard

# Prüfe ob bereits läuft
if pgrep -f "node app.js" > /dev/null; then
    echo "React Board already running"
    exit 0
fi

# Starte React Board
PORT=3001 nohup node app.js > /tmp/reactboard.log 2>&1 &

echo "React Board started on port 3001"