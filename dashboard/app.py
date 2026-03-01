"""
PilotSuite Styx Dashboard - Flask Application
Main dashboard server running on port 8766
"""
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from config import config
import os
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['default'])

# Initialize SocketIO for live updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Import widget blueprints
from widgets.system_status import system_status_bp, register_socketio_events as register_system_status_events, broadcast_updates as broadcast_system_status
from widgets.brain_graph import brain_graph_bp, register_socketio_events as register_brain_graph_events
from widgets.chat_widget import chat_widget_bp, register_socketio_events as register_chat_events
from widgets.sensor_overview import sensor_overview_bp, register_socketio_events as register_sensor_events, broadcast_updates as broadcast_sensor_status

# Register widget blueprints
app.register_blueprint(system_status_bp)
app.register_blueprint(brain_graph_bp)
app.register_blueprint(chat_widget_bp)
app.register_blueprint(sensor_overview_bp)

# Register widget Socket.IO events
register_system_status_events(socketio)
register_brain_graph_events(socketio)
register_chat_events(socketio, app.config)
register_sensor_events(socketio)

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get dashboard status"""
    return jsonify({
        'status': 'running',
        'version': '12.4.0',
        'port': app.config['PORT'],
        'rag_api': app.config['RAG_API_URL'],
        'widgets': ['system_status', 'brain_graph', 'chat', 'sensor_overview']
    })

@app.route('/api/overview')
def get_overview():
    """Get overview data"""
    return jsonify({
        'system_status': 'online',
        'active_services': 3,
        'pending_tasks': 0
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'message': 'Connected to PilotSuite Styx Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_update')
def handle_request_update(data):
    """Handle update requests from clients"""
    emit('update', {
        'type': 'status',
        'data': {'status': 'updated'}
    })

def broadcast_loop():
    """Background thread to broadcast live updates to widgets"""
    while True:
        time.sleep(5)  # Update every 5 seconds
        try:
            broadcast_system_status(socketio)
            broadcast_sensor_status(socketio)
        except Exception as e:
            print(f"Broadcast error: {e}")

def start_dashboard():
    """Start the dashboard server"""
    print(f"Starting PilotSuite Styx Dashboard on port {app.config['PORT']}")
    
    # Start background broadcast thread
    broadcast_thread = threading.Thread(target=broadcast_loop, daemon=True)
    broadcast_thread.start()
    print("Live update broadcast started")
    
    socketio.run(
        app,
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG_MODE']
    )

if __name__ == '__main__':
    start_dashboard()
