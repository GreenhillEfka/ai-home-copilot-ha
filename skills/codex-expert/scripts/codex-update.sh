#!/bin/bash
# Codex CLI Update Script
set -e

echo "🟢 Codex CLI Update Check"
echo "========================="
echo ""

CURRENT=$(codex --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
LATEST=$(npm show @openai/codex version 2>/dev/null || echo "unknown")

echo "Current: $CURRENT"
echo "Latest:  $LATEST"
echo ""

if [ "$CURRENT" = "$LATEST" ]; then
    echo "✅ Already up to date!"
    exit 0
fi

echo "Updating Codex CLI..."
npm install -g @openai/codex@latest

NEW=$(codex --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "error")
echo ""
echo "✅ Updated to: $NEW"