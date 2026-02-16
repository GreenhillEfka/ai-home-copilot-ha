#!/bin/bash
# AI Home CoPilot Release System
# Handles version bumps, commits, and releases for HA Integration and Core Add-on

set -e

WORKSPACE="/config/.openclaw/workspace"
HA_REPO="$WORKSPACE/ai_home_copilot_hacs_repo"
CORE_REPO="$WORKSPACE/ha-copilot-repo"

echo "========================================"
echo "AI Home CoPilot Release System"
echo "========================================"
echo ""

# Check if we're in the workspace
if [ ! -d "$HA_REPO" ] || [ ! -d "$CORE_REPO" ]; then
    echo "❌ Error: Repos not found!"
    echo "  HA Repo: $HA_REPO"
    echo "  Core Repo: $CORE_REPO"
    exit 1
fi

# Parse command
COMMAND="${1:-}"

case "$COMMAND" in
    status)
        echo "Repo Status:"
        echo "------------"
        cd "$HA_REPO" && echo "HA Integration: v$(grep '"version"' custom_components/ai_home_copilot/manifest.json | head -1 | sed 's/.*: "\([^"]*\)".*/\1/') - $(git rev-parse --short HEAD) - $(git diff --quiet && echo 'clean' || echo 'modified')"
        cd "$CORE_REPO" && echo "Core Add-on: v$(grep '"version"' addons/copilot_core/config.json | head -1 | sed 's/.*: "\([^"]*\)".*/\1/') - $(git rev-parse --short HEAD) - $(git diff --quiet && echo 'clean' || echo 'modified')"
        ;;
    sync)
        echo "Syncing workspaces..."
        cd "$HA_REPO" && git pull origin main
        cd "$CORE_REPO" && git pull origin main
        ;;
    commit)
        echo "Committing changes..."
        cd "$HA_REPO" && git add -A && git commit -m "$2" && git push origin main
        cd "$CORE_REPO" && git add -A && git commit -m "$2" && git push origin main
        ;;
    push)
        echo "Pushing changes..."
        cd "$HA_REPO" && git push origin main
        cd "$CORE_REPO" && git push origin main
        ;;
    release)
        VERSION="${2:-}"
        if [ -z "$VERSION" ]; then
            echo "❌ Error: Version required for release"
            exit 1
        fi
        
        echo "Releasing v$VERSION..."
        
        # Update HA Integration
        cd "$HA_REPO"
        sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/ai_home_copilot/manifest.json
        
        # Update Core Add-on
        cd "$CORE_REPO"
        sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" addons/copilot_core/config.json
        
        # Commit and push
        git add -A
        git commit -m "chore(release): v$VERSION - $3"
        git push origin main
        
        echo "✅ Release v$VERSION pushed!"
        ;;
    dashboard)
        echo "Updating React Board dashboard..."
        cd "$WORKSPACE" && git add -A && git commit -m "chore: update dashboard" && git push origin main
        ;;
    full)
        echo "Full release workflow..."
        ./scripts/sync_workspace.sh
        echo "Run 'git status' to review changes before committing"
        ;;
    *)
        echo "AI Home CoPilot Release System"
        echo ""
        echo "Usage: $0 <command> [args...]"
        echo ""
        echo "Commands:"
        echo "  status          Show current repo versions and status"
        echo "  sync            Pull latest changes from remote"
        echo "  commit <msg>    Stage and commit changes"
        echo "  push            Push changes to remote"
        echo "  release <v>     Full release with version bump"
        echo "  dashboard       Sync React Board dashboard"
        echo "  full            Full sync and review workflow"
        ;;
esac

echo ""
echo "========================================"
