#!/bin/bash
set -e

echo "PilotAgent HA Add-on starting..."

# Wait for Home Assistant supervisor
until curl -sf http://supervisor/info 2>/dev/null | grep -q '"supervisor"'; do
    echo "Waiting for Supervisor..."
    sleep 5
done

echo "Supervisor detected."

# Get HA token from Supervisor
HA_TOKEN="$(printenv SUPERVISOR_TOKEN)"

# Config from add-on options
AGENT_ID="$(cat /data/options.json | jq -r '.agent_id // "ha_agent")"
GATEWAY_URL="$(cat /data/options.json | jq -r '.gateway_url // ""')"

# Write HA token to file for agent
echo "$HA_TOKEN" > /shared/ha_token

echo "Starting OpenClaw agent as user: $(whoami)"

# Run openclaw agent if available, else sleep for debugging
if command -v openclaw &>/dev/null; then
    exec openclaw agent start \
        --agent-id "$AGENT_ID" \
        --ha-url "http://supervisor/core/api" \
        --ha-token "$HA_TOKEN" \
        ${GATEWAY_URL:+--gateway-url "$GATEWAY_URL"}
else
    echo "OpenClaw CLI not found. Keeping container alive for debugging."
    # Keep container running
    sleep infinity
fi
