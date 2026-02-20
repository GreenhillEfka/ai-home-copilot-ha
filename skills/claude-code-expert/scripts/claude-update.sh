#!/bin/bash
# Claude Code CLI Update Script
set -e

echo "🟣 Claude Code CLI Update Check"
echo "================================"
echo ""

# Attempt to get current version
CURRENT=$(claude --version 2>/dev/null | sed -n 's/.*version \([0-9.]*\).*/\1/p')
if [ -z "$CURRENT" ]; then
    # If --version doesn't work, try to get info from another command or assume latest
    echo "Could not determine current version directly. Assuming manual check needed."
    CURRENT="unknown"
fi
echo "Current version: $CURRENT"
echo ""

# Check for latest version - this part is tricky as there's no direct 'check-update' command
# We'll simulate a check by telling the user how to update manually.
echo "To update Claude Code CLI, typically you would use:"
echo "   'claude install stable' or 'claude install latest'"
echo "Please refer to Anthropic's official documentation for the definitive update procedure."
echo ""
echo "Recommendation: Regularly check Anthropic's official channels for updates."