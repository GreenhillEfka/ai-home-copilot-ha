"""
System Status Widget - CPU, RAM, Disk, Uptime monitoring
Flask Blueprint with REST API and WebSocket live updates
"""
from flask import Blueprint, jsonify, render_template
from flask_socketio import emit
import psutil
import time
from datetime import datetime

# Create blueprint
system_status_bp = Blueprint('system_status', __name__, url_prefix='/widget/system_status')

# Store boot time for uptime calculation
BOOT_TIME = psutil.boot_time()

def get_system_metrics():
    """Collect current system metrics"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = time.time() - BOOT_TIME
    
    # Format uptime
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    return {
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
        'timestamp': datetime.now().isoformat()
    }

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
