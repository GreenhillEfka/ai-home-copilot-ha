#!/bin/bash
# Gemini CLI Update Script
# Updates to latest stable version and reports status

set -e

echo "♊ Gemini CLI Update Check"
echo "=========================="
echo ""

# Current version
CURRENT=$(gemini --version 2>/dev/null || echo "not installed")
echo "Current version: $CURRENT"

# Latest available
LATEST=$(npm show @google/gemini-cli version 2>/dev/null || echo "unknown")
echo "Latest available: $LATEST"
echo ""

# Check if update needed
if [ "$CURRENT" = "$LATEST" ]; then
    echo "✅ Already up to date!"
    exit 0
fi

# Ask for confirmation (non-interactive mode skips)
if [ -z "$GEMINI_AUTO_UPDATE" ] && [ -t 0 ]; then
    read -p "Update to latest? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Update cancelled."
        exit 0
    fi
fi

# Perform update
echo "Updating Gemini CLI..."
npm install -g @google/gemini-cli@latest

# Verify
NEW_VERSION=$(gemini --version 2>/dev/null || echo "error")
echo ""
echo "✅ Update complete: $NEW_VERSION"
echo ""

# Show release info
echo "Release channels:"
echo "  stable:  npm install -g @google/gemini-cli@latest"
echo "  preview: npm install -g @google/gemini-cli@preview"
echo "  nightly: npm install -g @google/gemini-cli@nightly"