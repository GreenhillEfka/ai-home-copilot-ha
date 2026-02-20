#!/bin/bash
# Autopilot Runner - Startet alle 5 Minuten via systemd timer oder cron
# Oder manuell: ./autopilot.sh

WORKSPACE="/config/.openclaw/workspace"
STATE_FILE="$WORKSPACE/.openclaw/autopilot/state.json"
TASKS_FILE="$WORKSPACE/.openclaw/autopilot/tasks.md"
LOG_FILE="$WORKSPACE/.openclaw/autopilot/autopilot.log"

log() {
    echo "[$(date -Iseconds)] $1" >> "$LOG_FILE"
    echo "$1"
}

check_task_running() {
    # Prüfe ob ein Sub-Agent noch läuft
    if pgrep -f "autopilot-task" > /dev/null; then
        return 0
    fi
    return 1
}

start_next_task() {
    local next_task=$(jq -r '.next_task // empty' "$STATE_FILE" 2>/dev/null)
    
    if [ -z "$next_task" ] || [ "$next_task" = "null" ]; then
        log "No pending tasks"
        return 1
    fi
    
    log "Starting task: $next_task"
    
    # Update state
    jq --arg task "$next_task" --arg ts "$(date -Iseconds)" \
       '.current_task = $task | .task_status = "running" | .last_run = $ts' \
       "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    
    # Task wird von OpenClaw Heartbeat ausgeführt
    return 0
}

main() {
    log "=== Autopilot Check ==="
    
    if [ ! -f "$STATE_FILE" ]; then
        log "State file not found, initializing..."
        echo '{"last_run": null, "current_task": null, "task_status": null, "next_task": "interactive_brain_graph_panel"}' > "$STATE_FILE"
    fi
    
    local task_status=$(jq -r '.task_status // "idle"' "$STATE_FILE")
    local current_task=$(jq -r '.current_task // "none"' "$STATE_FILE")
    
    log "Status: $task_status, Task: $current_task"
    
    case "$task_status" in
        "running")
            log "Task still running, waiting..."
            ;;
        "waiting_approval")
            log "Task waiting for approval - user notification needed"
            ;;
        "completed")
            log "Task completed, ready for next"
            ;;
        "failed")
            log "Task failed, needs investigation"
            ;;
        *)
            start_next_task
            ;;
    esac
    
    # Update last check
    jq --arg ts "$(date -Iseconds)" '.last_check = $ts' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
}

main "$@"