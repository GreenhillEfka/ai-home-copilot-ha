"""
System Status Widget - CPU, RAM, Disk, Uptime monitoring + Core/HA Health
Flask Blueprint with REST API and WebSocket live updates
"""
from flask import Blueprint, jsonify, render_template
from flask_socketio import emit
import psutil
import time
import threading
import json
import os
from collections import deque
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError

# Create blueprint
system_status_bp = Blueprint('system_status', __name__, url_prefix='/widget/system_status')

# Store boot time for uptime calculation
BOOT_TIME = psutil.boot_time()

# Metrics history for trend computation (last 60 samples ~ 30 min at 30s interval)
_HISTORY_SIZE = 60
_metrics_history = deque(maxlen=_HISTORY_SIZE)
_history_lock = threading.Lock()

def _compute_trends():
    """Compute min/max/avg trends from recent history."""
    with _history_lock:
        if not _metrics_history:
            return None
        samples = list(_metrics_history)

    cpu_vals = [s['cpu_pct'] for s in samples]
    mem_vals = [s['mem_pct'] for s in samples]
    n = len(samples)
    span_min = round(n * 0.5, 1)  # approximate minutes (30s interval)

    return {
        'sample_count': n,
        'span_minutes': span_min,
        'cpu': {
            'min': round(min(cpu_vals), 1),
            'max': round(max(cpu_vals), 1),
            'avg': round(sum(cpu_vals) / n, 1),
        },
        'memory': {
            'min': round(min(mem_vals), 1),
            'max': round(max(mem_vals), 1),
            'avg': round(sum(mem_vals) / n, 1),
        },
    }


# Config - can be overridden via environment
CORE_API_URL = os.environ.get('CORE_API_URL', 'http://localhost:8909')
CORE_AUTH_TOKEN = os.environ.get('COPILOT_AUTH_TOKEN', '')
_HA_VERSION_CACHE = None
_CORE_VERSION_CACHE = None
_CORE_HEALTH_CACHE = None
_VERSION_CACHE_TTL = 60  # seconds


def _fetch_ha_version():
    """Fetch HA version from the Home Assistant REST API."""
    global _HA_VERSION_CACHE
    now = time.time()
    if _HA_VERSION_CACHE and (_HA_VERSION_CACHE.get('_ts', 0) + _VERSION_CACHE_TTL) > now:
        return _HA_VERSION_CACHE
    try:
        # HA supervisor API
        with urlopen('http://supervisor/info', timeout=3) as resp:
            import json as _json
            data = _json.loads(resp.read())
            version = data.get('data', {}).get('homeassistant', {}).get('version', 'unknown')
            _HA_VERSION_CACHE = {'version': version, 'available': True, '_ts': now}
    except Exception:
        _HA_VERSION_CACHE = {'version': 'unavailable', 'available': False, '_ts': now}
    return _HA_VERSION_CACHE


def _fetch_core_version():
    """Fetch Styx Core version from the Core API health endpoint."""
    global _CORE_VERSION_CACHE, _CORE_HEALTH_CACHE
    now = time.time()
    if _CORE_VERSION_CACHE and (_CORE_VERSION_CACHE.get('_ts', 0) + _VERSION_CACHE_TTL) > now:
        return _CORE_VERSION_CACHE
    try:
        headers = {}
        if CORE_AUTH_TOKEN:
            headers['Authorization'] = f'Bearer {CORE_AUTH_TOKEN}'
        import urllib.request
        req = urllib.request.Request(f'{CORE_API_URL}/health', headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            version = data.get('version', data.get('core_version', 'unknown'))
            _CORE_VERSION_CACHE = {'version': version, 'available': True, '_ts': now}
            _CORE_HEALTH_CACHE = {'status': 'healthy', '_ts': now}
    except Exception:
        _CORE_VERSION_CACHE = {'version': 'unavailable', 'available': False, '_ts': now}
        _CORE_HEALTH_CACHE = {'status': 'unreachable', '_ts': now}
    return _CORE_VERSION_CACHE


def _fetch_core_health():
    """Fetch Core health status separately (used for real-time health widget)."""
    global _CORE_HEALTH_CACHE
    now = time.time()
    if _CORE_HEALTH_CACHE and (_CORE_HEALTH_CACHE.get('_ts', 0) + _VERSION_CACHE_TTL) > now:
        return _CORE_HEALTH_CACHE
    _fetch_core_version()  # side-effect: populates both caches
    return _CORE_HEALTH_CACHE or {'status': 'unknown', '_ts': now}


def get_system_metrics():
    """Collect current system metrics with trend data."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = time.time() - BOOT_TIME

    # Format uptime
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    # Record sample for trend computation
    with _history_lock:
        _metrics_history.append({
            'cpu_pct': cpu_percent,
            'mem_pct': memory.percent,
            'ts': time.time(),
        })

    result = {
        'cpu': {
            'percent': cpu_percent,
            'cores': psutil.cpu_count(logical=True),
            'physical_cores': psutil.cpu_count(logical=False)
        },
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'uptime': {
            'seconds': uptime_seconds,
            'formatted': f"{days}d {hours}h {minutes}m"
        },
        'versions': {
            'ha': _fetch_ha_version().get('version', 'unknown'),
            'ha_available': _fetch_ha_version().get('available', False),
            'core': _fetch_core_version().get('version', 'unknown'),
            'core_available': _fetch_core_version().get('available', False),
            'core_health': _fetch_core_health().get('status', 'unknown'),
        },
        'timestamp': datetime.now().isoformat()
    }

    # Add trend data if history is available
    trends = _compute_trends()
    if trends:
        result['trends'] = trends

    return result

@system_status_bp.route('/')
def widget_view():
    """Render system status widget"""
    return render_template('widgets/system_status.html')

@system_status_bp.route('/api')
def api_status():
    """REST API endpoint for system status"""
    return jsonify(get_system_metrics())

@system_status_bp.route('/api/cpu')
def api_cpu():
    """REST API endpoint for CPU metrics only"""
    metrics = get_system_metrics()
    return jsonify(metrics['cpu'])

@system_status_bp.route('/api/memory')
def api_memory():
    """REST API endpoint for memory metrics only"""
    metrics = get_system_metrics()
    return jsonify(metrics['memory'])

@system_status_bp.route('/api/disk')
def api_disk():
    """REST API endpoint for disk metrics only"""
    metrics = get_system_metrics()
    return jsonify(metrics['disk'])

@system_status_bp.route('/api/uptime')
def api_uptime():
    """REST API endpoint for uptime only"""
    metrics = get_system_metrics()
    return jsonify(metrics['uptime'])

@system_status_bp.route('/api/versions')
def api_versions():
    """REST API endpoint for HA/Core versions"""
    return jsonify({
        'ha': _fetch_ha_version(),
        'core': _fetch_core_version(),
        'core_health': _fetch_core_health(),
    })

def register_socketio_events(socketio):
    """Register WebSocket events for system status"""
    @socketio.on('connect', namespace='/system_status')
    def handle_connect():
        emit('connected', {'message': 'Connected to System Status widget'})
        emit('metrics', get_system_metrics())
    
    @socketio.on('disconnect', namespace='/system_status')
    def handle_disconnect():
        print('Client disconnected from System Status widget')
    
    @socketio.on('request_metrics', namespace='/system_status')
    def handle_request_metrics():
        emit('metrics', get_system_metrics())

def broadcast_updates(socketio):
    """Broadcast system metrics updates (call periodically)"""
    socketio.emit('metrics', get_system_metrics(), namespace='/system_status')


# ── Plugin Registration ────────────────────────────────────────────────────────
from plugin_registry import WIDGET_REGISTRY, WidgetPlugin
WIDGET_REGISTRY.register(WidgetPlugin(
    name='system_status',
    blueprint_bp=system_status_bp,
    version='1.0.0',
    author='PilotSuite',
    description='CPU, RAM, Disk, Uptime + Core/HA Health Status mit WebSocket Live-Updates',
    socketio_register=register_socketio_events,
    broadcast_fn=broadcast_updates,
))
