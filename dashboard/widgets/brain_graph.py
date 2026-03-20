"""
Brain Graph Widget - D3.js Knowledge Graph Visualization
Flask Blueprint with REST API and interactive nodes
"""
from flask import Blueprint, jsonify, render_template, request
from flask_socketio import emit
import random
from datetime import datetime

# Create blueprint
brain_graph_bp = Blueprint('brain_graph', __name__, url_prefix='/widget/brain_graph')

# Sample knowledge graph data (would be replaced with real data from RAG/Knowledge base)
DEFAULT_NODES = [
    {'id': 'core', 'label': 'Styx Core', 'group': 'core', 'size': 30},
    {'id': 'rag', 'label': 'RAG API', 'group': 'api', 'size': 20},
    {'id': 'dashboard', 'label': 'Dashboard', 'group': 'ui', 'size': 20},
    {'id': 'agents', 'label': 'Agents', 'group': 'services', 'size': 25},
    {'id': 'memory', 'label': 'Memory', 'group': 'services', 'size': 18},
    {'id': 'scheduler', 'label': 'Scheduler', 'group': 'services', 'size': 18},
    {'id': 'websocket', 'label': 'WebSocket', 'group': 'api', 'size': 15},
    {'id': 'config', 'label': 'Config', 'group': 'core', 'size': 15},
]

DEFAULT_EDGES = [
    {'from': 'core', 'to': 'rag', 'label': 'uses'},
    {'from': 'core', 'to': 'dashboard', 'label': 'serves'},
    {'from': 'core', 'to': 'agents', 'label': 'manages'},
    {'from': 'core', 'to': 'memory', 'label': 'stores'},
    {'from': 'core', 'to': 'scheduler', 'label': 'triggers'},
    {'from': 'dashboard', 'to': 'websocket', 'label': 'connects'},
    {'from': 'dashboard', 'to': 'rag', 'label': 'queries'},
    {'from': 'agents', 'to': 'memory', 'label': 'reads'},
    {'from': 'scheduler', 'to': 'agents', 'label': 'activates'},
    {'from': 'config', 'to': 'core', 'label': 'configures'},
]

def get_graph_data():
    """Get current graph data"""
    return {
        'nodes': DEFAULT_NODES,
        'edges': DEFAULT_EDGES,
        'timestamp': datetime.now().isoformat()
    }

def get_node_details(node_id):
    """Get detailed information about a specific node"""
    node = next((n for n in DEFAULT_NODES if n['id'] == node_id), None)
    if not node:
        return {'error': 'Node not found'}, 404
    
    # Simulate detailed node info
    details = {
        'core': {'description': 'Main orchestrator', 'status': 'active', 'connections': 5},
        'rag': {'description': 'Retrieval-Augmented Generation API', 'status': 'active', 'connections': 2},
        'dashboard': {'description': 'Web dashboard interface', 'status': 'active', 'connections': 2},
        'agents': {'description': 'Agent management system', 'status': 'active', 'connections': 3},
        'memory': {'description': 'Vector memory store', 'status': 'active', 'connections': 2},
        'scheduler': {'description': 'Task scheduler', 'status': 'active', 'connections': 2},
        'websocket': {'description': 'Real-time communication', 'status': 'active', 'connections': 1},
        'config': {'description': 'Configuration manager', 'status': 'active', 'connections': 1},
    }
    
    return {
        **node,
        **details.get(node_id, {})
    }

@brain_graph_bp.route('/')
def widget_view():
    """Render brain graph widget"""
    return render_template('widgets/brain_graph.html')

@brain_graph_bp.route('/api')
def api_graph():
    """REST API endpoint for full graph data"""
    return jsonify(get_graph_data())

@brain_graph_bp.route('/api/nodes')
def api_nodes():
    """REST API endpoint for nodes only"""
    return jsonify({'nodes': DEFAULT_NODES})

@brain_graph_bp.route('/api/edges')
def api_edges():
    """REST API endpoint for edges only"""
    return jsonify({'edges': DEFAULT_EDGES})

@brain_graph_bp.route('/api/node/<node_id>')
def api_node_detail(node_id):
    """REST API endpoint for specific node details"""
    result = get_node_details(node_id)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@brain_graph_bp.route('/api/layout')
def api_layout():
    """Get graph layout configuration"""
    return jsonify({
        'width': 800,
        'height': 600,
        'charge': -300,
        'linkDistance': 150,
        'centerGravity': 0.1,
        'groups': {
            'core': {'color': '#FF6B6B', 'label': 'Core'},
            'api': {'color': '#4ECDC4', 'label': 'API'},
            'ui': {'color': '#45B7D1', 'label': 'UI'},
            'services': {'color': '#FFA07A', 'label': 'Services'}
        }
    })

def register_socketio_events(socketio):
    """Register WebSocket events for brain graph"""
    @socketio.on('connect', namespace='/brain_graph')
    def handle_connect():
        emit('connected', {'message': 'Connected to Brain Graph widget'})
        emit('graph_data', get_graph_data())
    
    @socketio.on('disconnect', namespace='/brain_graph')
    def handle_disconnect():
        print('Client disconnected from Brain Graph widget')
    
    @socketio.on('request_graph', namespace='/brain_graph')
    def handle_request_graph():
        emit('graph_data', get_graph_data())
    
    @socketio.on('node_click', namespace='/brain_graph')
    def handle_node_click(data):
        node_id = data.get('node_id')
        if node_id:
            details = get_node_details(node_id)
            emit('node_details', details)

def broadcast_updates(socketio, event_type='layout_update'):
    """Broadcast graph updates (call when graph changes)"""
    socketio.emit('graph_updated', {
        'type': event_type,
        'data': get_graph_data()
    }, namespace='/brain_graph')


# ── Plugin Registration ────────────────────────────────────────────────────────
from plugin_registry import WIDGET_REGISTRY, WidgetPlugin
WIDGET_REGISTRY.register(WidgetPlugin(
    name='brain_graph',
    blueprint_bp=brain_graph_bp,
    socketio_register=register_socketio_events,
))
