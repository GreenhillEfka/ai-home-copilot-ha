#!/bin/bash
# sync-ha-core-versions.sh
# Synchronizes version between pilotsuite-styx-ha and pilotsuite-styx-core repos
# Used in release pipeline to ensure both repos have matching versions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

HA_REPO="$WORKSPACE_DIR/pilotsuite-styx-ha"
CORE_REPO="$WORKSPACE_DIR/pilotsuite-styx-core"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if both repos exist
if [ ! -d "$HA_REPO" ]; then
    log_error "HA repo not found: $HA_REPO"
    exit 1
fi

if [ ! -d "$CORE_REPO" ]; then
    log_error "Core repo not found: $CORE_REPO"
    exit 1
fi

# Get current versions
HA_VERSION=$(cat "$HA_REPO/VERSION" 2>/dev/null || echo "unknown")
CORE_VERSION=$(cat "$CORE_REPO/VERSION" 2>/dev/null || echo "unknown")

log_info "Current versions:"
log_info "  HA Core: $HA_VERSION"
log_info "  Styx Core: $CORE_VERSION"

# Check if versions match
if [ "$HA_VERSION" = "$CORE_VERSION" ]; then
    log_info "✓ Versions are already in sync: $HA_VERSION"
    exit 0
fi

# Determine which version to use (prefer newer/HA version)
if [ "$HA_VERSION" != "unknown" ] && [ "$CORE_VERSION" != "unknown" ]; then
    TARGET_VERSION="$HA_VERSION"
    log_warn "Version mismatch detected. Using HA version: $TARGET_VERSION"
elif [ "$HA_VERSION" != "unknown" ]; then
    TARGET_VERSION="$HA_VERSION"
    log_warn "Core version unknown. Using HA version: $TARGET_VERSION"
elif [ "$CORE_VERSION" != "unknown" ]; then
    TARGET_VERSION="$CORE_VERSION"
    log_warn "HA version unknown. Using Core version: $TARGET_VERSION"
else
    log_error "Both versions unknown. Cannot sync."
    exit 1
fi

# Sync Core to match HA
log_info "Updating Core VERSION file to $TARGET_VERSION..."
echo "$TARGET_VERSION" > "$CORE_REPO/VERSION"

# Update Core manifest.json if it exists
if [ -f "$CORE_REPO/copilot_core/manifest.json" ]; then
    log_info "Updating Core manifest.json version..."
    # Use sed for JSON version update (cross-platform compatible)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$TARGET_VERSION\"/" "$CORE_REPO/copilot_core/manifest.json"
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$TARGET_VERSION\"/" "$CORE_REPO/copilot_core/manifest.json"
    fi
fi

# Update HA manifest.json if it exists
if [ -f "$HA_REPO/custom_components/copilot_ha/manifest.json" ]; then
    log_info "Updating HA manifest.json version..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/\"version\": \"[^\"]*\"/\"version\": \"$TARGET_VERSION\"/" "$HA_REPO/custom_components/copilot_ha/manifest.json"
    else
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$TARGET_VERSION\"/" "$HA_REPO/custom_components/copilot_ha/manifest.json"
    fi
fi

log_info "✓ Version sync complete: $TARGET_VERSION"
log_info ""
log_info "Next steps:"
log_info "  1. Review changes: git diff"
log_info "  2. Commit: git add VERSION manifest.json && git commit -m 'fix: sync versions to $TARGET_VERSION'"
log_info "  3. Push to both repos"

exit 0
