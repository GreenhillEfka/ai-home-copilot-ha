#!/bin/bash
# Claude CLI Orchestration Script for AI Home CoPilot
# Manages GitHub sync, code review, and project oversight

set -e

REPO_HA="/config/.openclaw/workspace/ai_home_copilot_hacs_repo"
REPO_CORE="/config/.openclaw/workspace/ha-copilot-repo"
PROJECTS="/config/.openclaw/workspace/projects"
CONTEXT="/config/.openclaw/workspace"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==========================================
# 1. GitHub Sync
# ==========================================
sync_github() {
    log_info "Syncing with GitHub..."
    
    for repo in "$REPO_HA" "$REPO_CORE"; do
        cd "$repo"
        echo "--- Syncing $(basename $repo) ---"
        git fetch origin 2>/dev/null || log_warn "Could not fetch $repo"
        git status --short || true
    done
    
    log_success "GitHub sync complete"
}

# ==========================================
# 2. Pull Latest Changes
# ==========================================
pull_changes() {
    log_info "Pulling latest changes..."
    
    for repo in "$REPO_HA" "$REPO_CORE"; do
        cd "$repo"
        branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        log_info "Pulling $repo (branch: $branch)"
        git pull origin "$branch" 2>/dev/null || log_warn "Could not pull $repo"
    done
    
    log_success "Pull complete"
}

# ==========================================
# 3. Git Status Summary
# ==========================================
git_summary() {
    echo ""
    echo "========================================"
    echo "Git Status Summary"
    echo "========================================"
    
    for repo in "$REPO_HA" "$REPO_CORE"; do
        cd "$repo"
        echo ""
        echo "--- $(basename $repo) ---"
        branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        echo "Branch: $branch"
        git status --short 2>/dev/null || true
        git log --oneline -3 2>/dev/null || true
    done
    
    echo ""
    echo "========================================"
}

# ==========================================
# 4. Run Claude Code Review
# ==========================================
review_code() {
    log_info "Running Claude Code Review..."
    
    cd "$REPO_HA"
    claude -p "Review the latest changes in this HA Integration repo. Check for:
1. Code quality issues
2. Security concerns  
3. Architecture consistency
4. Test coverage
5. Documentation completeness

Report your findings concisely." 2>/dev/null || log_warn "Claude review failed for HA Integration"
    
    cd "$REPO_CORE"
    claude -p "Review the latest changes in this Core Add-on repo. Check for:
1. Code quality issues
2. Security concerns
3. Architecture consistency
4. Test coverage
5. Documentation completeness

Report your findings concisely." 2>/dev/null || log_warn "Claude review failed for Core Add-on"
    
    log_success "Code review complete"
}

# ==========================================
# 5. Update Project INDEX
# ==========================================
update_index() {
    log_info "Updating project INDEX files..."
    
    # AI Home CoPilot INDEX
    cat > "$PROJECTS/ai_home_copilot/INDEX.md" << 'EOF'
# AI Home CoPilot - INDEX.md

## Last Updated
$(date '+%Y-%m-%d %H:%M')

## Project Status

| Metric | Value |
|--------|-------|
| Branch | development |
| Version | v0.7.0 |
| Modules | 22 total |
| Done | 12 (55%) |

## Active Tasks

| Task | Status | Priority | Assignee |
|------|--------|----------|-----------|
| Habitus Zones v2 | in-progress | high | Project Agent |
| Habitus Dashboard Cards | in-progress | medium | Project Agent |
| Brain Graph v2 | in-progress | high | Task Worker |

## Completed Today

- [x] Habitus Miner Bug Fixes
- [x] Candidates Store Merge
- [x] Architecture Fixes
- [x] v0.7.0 Release

## Next Steps

1. Habitus Zones v2 Implementation
2. Dashboard Cards Integration
3. Brain Graph v2 Testing
4. v0.7.1 Release Prep

## Dependencies

- Core Add-on v0.4.x
- Brain Graph v2
- Neurons Architecture

## Notes

See PROJECT_AGENT.md for detailed task breakdown.
EOF
    
    log_success "INDEX files updated"
}

# ==========================================
# 6. Sync with React Board
# ==========================================
sync_react_board() {
    log_info "Syncing with React Board..."
    
    # Push updates to API
    curl -s http://localhost:3001/api/projects 2>/dev/null || log_warn "React Board API not available"
    
    log_success "React Board sync initiated"
}

# ==========================================
# 7. Full Orchestration
# ==========================================
orchestrate() {
    echo ""
    echo "========================================"
    echo "Claude CLI Orchestration"
    echo "========================================"
    
    log_info "Starting full orchestration..."
    
    sync_github
    pull_changes
    git_summary
    update_index
    sync_react_board
    
    echo ""
    log_success "Orchestration complete!"
    echo ""
    echo "Next steps:"
    echo "  - Run 'claude orchestrate review' for code review"
    echo "  - Run 'claude orchestrate sync' for GitHub sync"
    echo "  - Run 'claude orchestrate full' for everything"
    echo ""
}

# ==========================================
# Main
# ==========================================
case "${1:-orchestrate}" in
    sync)
        sync_github
        pull_changes
        git_summary
        ;;
    review)
        review_code
        ;;
    index)
        update_index
        ;;
    board)
        sync_react_board
        ;;
    full)
        orchestrate
        ;;
    *)
        orchestrate
        ;;
esac
