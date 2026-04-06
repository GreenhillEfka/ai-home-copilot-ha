#!/bin/bash
# PilotSuite Worker Management Script

set -e

# Configuration
PILOTSUITE_DIR="/config/clawd"
DATA_DIR="/config/pilotsuite"
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
LOG_DIR="${DATA_DIR}/logs"
PID_DIR="${DATA_DIR}/pids"

# Create directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_redis() {
    if ! command -v redis-cli &> /dev/null; then
        log_error "Redis CLI not found. Please install Redis."
        exit 1
    fi
    
    if ! redis-cli ping &> /dev/null; then
        log_error "Redis is not running. Please start Redis first."
        exit 1
    fi
    
    log_info "Redis is running"
}

start_worker() {
    local concurrency=${1:-4}
    local queues=${2:-celery,backups,reports,energy}
    local loglevel=${3:-info}
    
    log_info "Starting PilotSuite Celery Worker..."
    log_info "Concurrency: $concurrency"
    log_info "Queues: $queues"
    log_info "Log Level: $loglevel"
    
    cd "$PILOTSUITE_DIR"
    
    celery -A copilot_core.celery_app worker \
        --loglevel "$loglevel" \
        --concurrency "$concurrency" \
        --queues "$queues" \
        --pidfile "$PID_DIR/celery.pid" \
        --logfile "$LOG_DIR/celery.log" \
        --detach
    
    log_info "Worker started (PID: $(cat $PID_DIR/celery.pid))"
}

start_beat() {
    log_info "Starting Celery Beat..."
    
    cd "$PILOTSUITE_DIR"
    
    celery -A copilot_core.celery_app beat \
        --loglevel info \
        --pidfile "$PID_DIR/beat.pid" \
        --logfile "$LOG_DIR/beat.log" \
        --detach
    
    log_info "Beat started (PID: $(cat $PID_DIR/beat.pid))"
}

start_flower() {
    log_info "Starting Flower (Celery Monitor)..."
    
    cd "$PILOTSUITE_DIR"
    
    celery -A copilot_core.celery_app flower \
        --port=5555 \
        --pidfile "$PID_DIR/flower.pid" \
        --logfile "$LOG_DIR/flower.log" \
        --detach
    
    log_info "Flower started (PID: $(cat $PID_DIR/flower.pid))"
    log_info "Open http://localhost:5555 to monitor workers"
}

stop_worker() {
    log_info "Stopping Celery Worker..."
    
    if [ -f "$PID_DIR/celery.pid" ]; then
        kill $(cat "$PID_DIR/celery.pid") 2>/dev/null || true
        rm -f "$PID_DIR/celery.pid"
        log_info "Worker stopped"
    else
        log_warn "Worker PID file not found"
    fi
}

stop_beat() {
    log_info "Stopping Celery Beat..."
    
    if [ -f "$PID_DIR/beat.pid" ]; then
        kill $(cat "$PID_DIR/beat.pid") 2>/dev/null || true
        rm -f "$PID_DIR/beat.pid"
        log_info "Beat stopped"
    else
        log_warn "Beat PID file not found"
    fi
}

stop_flower() {
    log_info "Stopping Flower..."
    
    if [ -f "$PID_DIR/flower.pid" ]; then
        kill $(cat "$PID_DIR/flower.pid") 2>/dev/null || true
        rm -f "$PID_DIR/flower.pid"
        log_info "Flower stopped"
    else
        log_warn "Flower PID file not found"
    fi
}

stop_all() {
    log_info "Stopping all PilotSuite workers..."
    stop_worker
    stop_beat
    stop_flower
    log_info "All workers stopped"
}

status() {
    echo "=== PilotSuite Worker Status ==="
    echo ""
    
    # Redis
    if redis-cli ping &> /dev/null; then
        echo -e "Redis: ${GREEN}Running${NC}"
    else
        echo -e "Redis: ${RED}Not Running${NC}"
    fi
    
    # Worker
    if [ -f "$PID_DIR/celery.pid" ] && kill -0 $(cat "$PID_DIR/celery.pid") 2>/dev/null; then
        echo -e "Worker: ${GREEN}Running (PID: $(cat $PID_DIR/celery.pid))${NC}"
    else
        echo -e "Worker: ${RED}Not Running${NC}"
    fi
    
    # Beat
    if [ -f "$PID_DIR/beat.pid" ] && kill -0 $(cat "$PID_DIR/beat.pid") 2>/dev/null; then
        echo -e "Beat: ${GREEN}Running (PID: $(cat $PID_DIR/beat.pid))${NC}"
    else
        echo -e "Beat: ${RED}Not Running${NC}"
    fi
    
    # Flower
    if [ -f "$PID_DIR/flower.pid" ] && kill -0 $(cat "$PID_DIR/flower.pid") 2>/dev/null; then
        echo -e "Flower: ${GREEN}Running (PID: $(cat $PID_DIR/flower.pid))${NC}"
    else
        echo -e "Flower: ${RED}Not Running${NC}"
    fi
    
    echo ""
    echo "=== Recent Logs ==="
    tail -20 "$LOG_DIR/celery.log" 2>/dev/null || echo "No logs found"
}

restart_all() {
    log_info "Restarting all workers..."
    stop_all
    sleep 2
    start_worker
    start_beat
    log_info "All workers restarted"
}

# Main
case "${1:-status}" in
    start)
        check_redis
        start_worker "${2:-4}" "${3:-celery,backups,reports,energy}" "${4:-info}"
        ;;
    start-beat)
        start_beat
        ;;
    start-flower)
        start_flower
        ;;
    start-all)
        check_redis
        start_worker "${2:-4}"
        start_beat
        if [ "${3:-}" = "--flower" ]; then
            start_flower
        fi
        ;;
    stop)
        stop_worker
        ;;
    stop-beat)
        stop_beat
        ;;
    stop-flower)
        stop_flower
        ;;
    stop-all)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|start-beat|start-flower|start-all|stop|stop-beat|stop-flower|stop-all|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start [concurrency] [queues] [loglevel]  - Start Celery worker"
        echo "  start-beat                                - Start Celery Beat scheduler"
        echo "  start-flower                              - Start Flower monitor"
        echo "  start-all [concurrency] [--flower]        - Start worker + beat (+ optional flower)"
        echo "  stop                                      - Stop Celery worker"
        echo "  stop-beat                                 - Stop Celery Beat"
        echo "  stop-flower                               - Stop Flower"
        echo "  stop-all                                  - Stop all workers"
        echo "  restart                                   - Restart all workers"
        echo "  status                                    - Show status"
        exit 1
        ;;
esac
