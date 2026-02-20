#!/bin/bash
# Complete sync script for React Board + Context + GitHub

set -e

WORKSPACE="/config/.openclaw/workspace"
REACT_BOARD="/config/.openclaw/canvas/ReactBoard"
API="http://localhost:3001/api"

echo "=== 1. Syncing Context Files ==="
for file in MEMORY.md AGENTS.md SOUL.md USER.md TOOLS.md HEARTBEAT.md IDENTITY.md BOOTSTRAP.md; do
    if [ -f "$WORKSPACE/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file fehlt"
    fi
done

echo ""
echo "=== 2. Logging alle fehlenden Activities ==="

# Log die fehlenden Activities seit 17:16
curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "sync", "title": "🔄 Context Sync", "description": "Context Files synchronisiert", "badge": "📋"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "project", "title": "📊 PROJECT_AGENT.md erstellt", "description": "AI Home CoPilot + Core Add-on Agents definiert", "badge": "🤖"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "docs", "title": "📖 RELEASE_PROCESS.md erstellt", "description": "Secure Release Process dokumentiert", "badge": "📋"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "docs", "title": "📖 GITHUB_CLAUDE_INTEGRATION.md", "description": "GitHub + Claude CLI Integration dokumentiert", "badge": "🔗"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "fix", "title": "🔧 Port 3001 repariert", "description": "React Board auf Port 3001 wiederhergestellt", "badge": "🔧"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "fix", "title": "🔧 Nginx Proxy korrigiert", "description": "Port 48099 → 3001", "badge": "🌐"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "config", "title": "☁️ CLOUD ONLY Policy", "description": "Nur ollamam2/ Modelle ab jetzt", "badge": "☁️"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "task", "title": "🧠 Habitus Zones v2 Phase 1", "description": "habitus_zones_store_v2.py + entities erstellt", "badge": "🏗️"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "task", "title": "🧠 Habitus Zones v2 Phase 2", "description": "Brain Graph Integration + API Endpoints", "badge": "🔗"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "task", "title": "📦 Habitus Dashboard Cards", "description": "Dashboard Cards für HA UI", "badge": "📊"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "task", "title": "🌉 Graph Candidates Bridge", "description": "Brain Graph v2 + Candidates Store", "badge": "🌉"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "fix", "title": "🔧 Telegram API konfiguriert", "description": "Message Tool funktioniert jetzt", "badge": "📱"}'

curl -s -X POST "$API/activity" -H "Content-Type: application/json" \
  -d '{"type": "sync", "title": "🔄 Scripts erstellt", "description": "claude_orchestrate.sh + sync_workspace.sh", "badge": "📜"}'

echo ""
echo "=== 3. Verifizierung ==="
ACTIVITIES=$(curl -s "$API/activity" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d))")
echo "Activities: $ACTIVITIES"

echo ""
echo "=== 4. GitHub Status ==="
cd "$WORKSPACE/ai_home_copilot_hacs_repo" && git status --short | head -5
