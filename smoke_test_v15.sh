#!/bin/bash
# PilotSuite v15 E2E Smoke Test
echo "=== PilotSuite v15 E2E Smoke Test ==="
VERSION=$(curl -s http://localhost:8909/health | python3 -c "import json,sys; print(json.load(sys.stdin).get(\"version\",\"?\"))" 2>/dev/null)
echo "Core version: $VERSION"
SYNC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8909/api/v1/zone-automation/sync-definitions -H "Content-Type: application/json" -d "{\"source\":\"ha\",\"zones\":[]}")
echo "/sync-definitions status: $SYNC_STATUS"
ZONES=$(curl -s http://localhost:8909/api/v1/zone-automation/zones | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get(\"zones\",[])) if isinstance(d,dict) else \"?\")" 2>/dev/null)
echo "Zones in Core: $ZONES"
MODULES=$(curl -s http://localhost:8909/api/v1/modules/dashboard | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get(\"modules\",{})))" 2>/dev/null)
echo "Active modules: $MODULES"
echo ""
if [[ "$VERSION" == "15.0.1" ]] && [[ "$SYNC_STATUS" == "200" ]]; then
  echo "ALL CHECKS PASS"
else
  echo "ISSUES DETECTED"
fi
