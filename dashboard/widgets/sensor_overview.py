"""
Sensor Overview Widget - Live sensor data monitoring
Flask Blueprint with REST API and WebSocket live updates
"""
from flask import Blueprint, jsonify, render_template, request
from flask_socketio import emit
from datetime import datetime
import random

# Create blueprint
sensor_overview_bp = Blueprint('sensor_overview', __name__, url_prefix='/widget/sensor_overview')

# Simulated sensor data (would connect to real sensors/Home Assistant in production)
SENSOR_CONFIG = {
    'temperature': {
        'living_room': {'name': 'Living Room', 'unit': '°C', 'min': 18, 'max': 26},
        'bedroom': {'name': 'Bedroom', 'unit': '°C', 'min': 16, 'max': 24},
        'kitchen': {'name': 'Kitchen', 'unit': '°C', 'min': 18, 'max': 28},
        'bathroom': {'name': 'Bathroom', 'unit': '°C', 'min': 20, 'max': 28},
        'outdoor': {'name': 'Outdoor', 'unit': '°C', 'min': -10, 'max': 40},
    },
    'humidity': {
        'living_room': {'name': 'Living Room', 'unit': '%', 'min': 30, 'max': 70},
        'bedroom': {'name': 'Bedroom', 'unit': '%', 'min': 30, 'max': 65},
        'bathroom': {'name': 'Bathroom', 'unit': '%', 'min': 40, 'max': 80},
        'outdoor': {'name': 'Outdoor', 'unit': '%', 'min': 20, 'max': 100},
    },
    'air_quality': {
        'living_room': {'name': 'Living Room', 'unit': 'AQI', 'min': 0, 'max': 500},
        'bedroom': {'name': 'Bedroom', 'unit': 'AQI', 'min': 0, 'max': 500},
        'outdoor': {'name': 'Outdoor', 'unit': 'AQI', 'min': 0, 'max': 500},
    },
    'motion': {
        'entrance': {'name': 'Entrance', 'unit': 'boolean', 'min': 0, 'max': 1},
        'hallway': {'name': 'Hallway', 'unit': 'boolean', 'min': 0, 'max': 1},
        'living_room': {'name': 'Living Room', 'unit': 'boolean', 'min': 0, 'max': 1},
    },
    'light': {
        'living_room': {'name': 'Living Room', 'unit': 'lux', 'min': 0, 'max': 1000},
        'bedroom': {'name': 'Bedroom', 'unit': 'lux', 'min': 0, 'max': 500},
        'outdoor': {'name': 'Outdoor', 'unit': 'lux', 'min': 0, 'max': 10000},
    }
}

def generate_sensor_value(sensor_type, location):
    """Generate realistic sensor value"""
    config = SENSOR_CONFIG.get(sensor_type, {}).get(location, {})
    if not config:
        return None
    
    min_val = config.get('min', 0)
    max_val = config.get('max', 100)
    
    if sensor_type == 'motion':
        return random.choice([0, 0, 0, 1, 1])  # More likely to be 0
    
    # Add some randomness with bias toward middle range
    range_val = max_val - min_val
    value = min_val + (range_val * (0.3 + random.random() * 0.4))
    return round(value, 1)

def get_all_sensors():
    """Get current readings from all sensors"""
    sensors = {}
    timestamp = datetime.now().isoformat()
    
    for sensor_type, locations in SENSOR_CONFIG.items():
        sensors[sensor_type] = {}
        for location, config in locations.items():
            value = generate_sensor_value(sensor_type, location)
            sensors[sensor_type][location] = {
                'name': config['name'],
                'value': value,
                'unit': config['unit'],
                'min': config['min'],
                'max': config['max'],
                'status': get_sensor_status(sensor_type, value, config)
            }
    
    return {
        'sensors': sensors,
        'timestamp': timestamp,
        'count': sum(len(locations) for locations in sensors.values())
    }

def get_sensor_status(sensor_type, value, config):
    """Determine sensor status based on value"""
    if value is None:
        return 'unknown'
    
    min_val = config.get('min', 0)
    max_val = config.get('max', 100)
    range_val = max_val - min_val
    
    if sensor_type == 'motion':
        return 'active' if value > 0 else 'idle'
    
    if sensor_type == 'temperature':
        if value < 18:
            return 'cold'
        elif value > 26:
            return 'hot'
        return 'comfortable'
    
    if sensor_type == 'humidity':
        if value < 30:
            return 'dry'
        elif value > 70:
            return 'humid'
        return 'optimal'
    
    if sensor_type == 'air_quality':
        if value < 50:
            return 'good'
        elif value < 100:
            return 'moderate'
        elif value < 150:
            return 'unhealthy_sensitive'
        return 'unhealthy'
    
    # Default status
    if value < min_val + range_val * 0.2:
        return 'low'
    elif value > max_val - range_val * 0.2:
        return 'high'
    return 'normal'

def get_sensor_history(sensor_type, location, points=10):
    """Generate simulated sensor history"""
    config = SENSOR_CONFIG.get(sensor_type, {}).get(location, {})
    if not config:
        return []
    
    history = []
    now = datetime.now()
    min_val = config.get('min', 0)
    max_val = config.get('max', 100)
    range_val = max_val - min_val
    
    for i in range(points):
        timestamp = now.replace(second=now.second - i)
        value = min_val + (range_val * (0.3 + random.random() * 0.4))
        history.append({
            'timestamp': timestamp.isoformat(),
            'value': round(value, 1)
        })
    
    return list(reversed(history))

@sensor_overview_bp.route('/')
def widget_view():
    """Render sensor overview widget"""
    return render_template('widgets/sensor_overview.html')

@sensor_overview_bp.route('/api')
def api_sensors():
    """REST API endpoint for all sensor data"""
    return jsonify(get_all_sensors())

@sensor_overview_bp.route('/api/<sensor_type>')
def api_sensor_type(sensor_type):
    """REST API endpoint for specific sensor type"""
    if sensor_type not in SENSOR_CONFIG:
        return jsonify({'error': 'Sensor type not found'}), 404
    
    sensors = {}
    for location, config in SENSOR_CONFIG[sensor_type].items():
        value = generate_sensor_value(sensor_type, location)
        sensors[location] = {
            'name': config['name'],
            'value': value,
            'unit': config['unit'],
            'status': get_sensor_status(sensor_type, value, config)
        }
    
    return jsonify({
        'type': sensor_type,
        'sensors': sensors,
        'timestamp': datetime.now().isoformat()
    })

@sensor_overview_bp.route('/api/<sensor_type>/<location>')
def api_sensor_detail(sensor_type, location):
    """REST API endpoint for specific sensor"""
    config = SENSOR_CONFIG.get(sensor_type, {}).get(location)
    if not config:
        return jsonify({'error': 'Sensor not found'}), 404
    
    value = generate_sensor_value(sensor_type, location)
    history = get_sensor_history(sensor_type, location)
    
    return jsonify({
        'type': sensor_type,
        'location': location,
        'name': config['name'],
        'value': value,
        'unit': config['unit'],
        'min': config['min'],
        'max': config['max'],
        'status': get_sensor_status(sensor_type, value, config),
        'history': history,
        'timestamp': datetime.now().isoformat()
    })

@sensor_overview_bp.route('/api/config')
def api_config():
    """REST API endpoint for sensor configuration"""
    return jsonify({
        'sensor_types': list(SENSOR_CONFIG.keys()),
        'sensors': SENSOR_CONFIG
    })

def register_socketio_events(socketio):
    """Register WebSocket events for sensor overview"""
    @socketio.on('connect', namespace='/sensor_overview')
    def handle_connect():
        emit('connected', {'message': 'Connected to Sensor Overview widget'})
        emit('sensor_data', get_all_sensors())
    
    @socketio.on('disconnect', namespace='/sensor_overview')
    def handle_disconnect():
        print('Client disconnected from Sensor Overview widget')
    
    @socketio.on('request_sensors', namespace='/sensor_overview')
    def handle_request_sensors():
        emit('sensor_data', get_all_sensors())
    
    @socketio.on('subscribe_sensor', namespace='/sensor_overview')
    def handle_subscribe(data):
        sensor_type = data.get('type')
        location = data.get('location')
        if sensor_type and location:
            emit('subscribed', {
                'type': sensor_type,
                'location': location,
                'message': f'Subscribed to {sensor_type}/{location}'
            })

def broadcast_updates(socketio):
    """Broadcast sensor updates (call periodically)"""
    socketio.emit('sensor_data', get_all_sensors(), namespace='/sensor_overview')


# ── Plugin Registration ────────────────────────────────────────────────────────
from plugin_registry import WIDGET_REGISTRY, WidgetPlugin
WIDGET_REGISTRY.register(WidgetPlugin(
    name='sensor_overview',
    blueprint_bp=sensor_overview_bp,
    socketio_register=register_socketio_events,
    broadcast_fn=broadcast_updates,
))
