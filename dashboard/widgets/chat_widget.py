"""
Chat Widget - Embedded Chat with WebSocket connection to RAG API
Flask Blueprint with REST API and real-time messaging
"""
from flask import Blueprint, jsonify, render_template, request
from flask_socketio import emit
from datetime import datetime
import requests
import json
import threading

# Create blueprint
chat_widget_bp = Blueprint('chat_widget', __name__, url_prefix='/widget/chat')

# Message history (in-memory, would use database in production)
message_history = []
_history_lock = threading.Lock()
MAX_HISTORY = 50

def get_rag_api_url(app_config):
    """Get RAG API URL from app config"""
    return getattr(app_config, 'RAG_API_URL', 'http://localhost:8765')

def send_to_rag_api(message, api_url):
    """Send message to RAG API and get response"""
    try:
        response = requests.post(
            f"{api_url}/api/chat",
            json={'message': message, 'timestamp': datetime.now().isoformat()},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return {'error': f'RAG API error: {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'error': f'Connection failed: {str(e)}'}

def add_message(role, content, metadata=None):
    """Add message to history (thread-safe)."""
    with _history_lock:
        message = {
            'id': len(message_history) + 1,
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        message_history.append(message)

        # Trim history if too long
        if len(message_history) > MAX_HISTORY:
            message_history.pop(0)

        return message

def get_recent_messages(limit=20):
    """Get recent message history (thread-safe)."""
    with _history_lock:
        return list(message_history[-limit:])

def clear_history():
    """Clear message history (thread-safe)."""
    with _history_lock:
        message_history.clear()
    return {'status': 'cleared'}

@chat_widget_bp.route('/')
def widget_view():
    """Render chat widget"""
    return render_template('widgets/chat_widget.html')

@chat_widget_bp.route('/api')
def api_chat():
    """REST API endpoint for chat - returns recent messages"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'messages': get_recent_messages(limit),
        'count': len(message_history)
    })

@chat_widget_bp.route('/api/send', methods=['POST'])
def api_send():
    """REST API endpoint to send a message"""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = data['message']
    api_url = data.get('api_url', 'http://localhost:8765')
    
    # Add user message to history
    add_message('user', user_message)
    
    # Send to RAG API
    response = send_to_rag_api(user_message, api_url)
    
    # Add assistant response to history
    if 'error' in response:
        add_message('assistant', f"Error: {response['error']}")
    else:
        assistant_message = response.get('response', response.get('answer', 'No response'))
        add_message('assistant', assistant_message, response.get('metadata', {}))
    
    return jsonify({
        'status': 'sent',
        'user_message': user_message,
        'response': response
    })

@chat_widget_bp.route('/api/history')
def api_history():
    """REST API endpoint for message history"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(get_recent_messages(limit))

@chat_widget_bp.route('/api/clear', methods=['POST'])
def api_clear():
    """REST API endpoint to clear chat history"""
    return jsonify(clear_history())

@chat_widget_bp.route('/api/rag-status')
def api_rag_status():
    """Check RAG API status"""
    api_url = request.args.get('api_url', 'http://localhost:8765')
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return jsonify({
            'status': 'online' if response.status_code == 200 else 'offline',
            'response_time': response.elapsed.total_seconds() * 1000
        })
    except requests.exceptions.RequestException:
        return jsonify({'status': 'offline', 'error': 'Connection failed'})

def register_socketio_events(socketio, app_config=None):
    """Register WebSocket events for chat"""
    api_url = getattr(app_config, 'RAG_API_URL', 'http://localhost:8765') if app_config else 'http://localhost:8765'
    
    @socketio.on('connect', namespace='/chat')
    def handle_connect():
        emit('connected', {
            'message': 'Connected to Chat widget',
            'rag_api': api_url
        })
        emit('history', get_recent_messages(20))
    
    @socketio.on('disconnect', namespace='/chat')
    def handle_disconnect():
        print('Client disconnected from Chat widget')
    
    @socketio.on('send_message', namespace='/chat')
    def handle_send_message(data):
        message = data.get('message')
        if not message:
            emit('error', {'message': 'No message provided'})
            return
        
        # Add user message
        user_msg = add_message('user', message)
        emit('new_message', user_msg, broadcast=True)
        
        # Send to RAG API
        response = send_to_rag_api(message, api_url)
        
        # Add and emit assistant response
        if 'error' in response:
            assistant_msg = add_message('assistant', f"Error: {response['error']}")
        else:
            assistant_content = response.get('response', response.get('answer', 'No response'))
            assistant_msg = add_message('assistant', assistant_content, response.get('metadata', {}))
        
        emit('new_message', assistant_msg, broadcast=True)
    
    @socketio.on('request_history', namespace='/chat')
    def handle_request_history(data):
        limit = data.get('limit', 20)
        emit('history', get_recent_messages(limit))
    
    @socketio.on('clear_history', namespace='/chat')
    def handle_clear_history():
        clear_history()
        emit('history_cleared', {'status': 'cleared'}, broadcast=True)

def broadcast_message(socketio, message):
    """Broadcast a new message to all connected clients"""
    socketio.emit('new_message', message, namespace='/chat')


# ── Plugin Registration ────────────────────────────────────────────────────────
from plugin_registry import WIDGET_REGISTRY, WidgetPlugin
WIDGET_REGISTRY.register(WidgetPlugin(
    name='chat',
    blueprint_bp=chat_widget_bp,
    version='1.0.0',
    author='PilotSuite',
    description='Eingebetteter Chat mit WebSocket-Anbindung ans RAG-API',
    socketio_register=register_socketio_events,
    broadcast_fn=broadcast_message,
))
