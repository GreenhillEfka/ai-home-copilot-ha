"""Flask Integration Tests for Collective Intelligence (Federated Learning) API.

Tests the Flask blueprint endpoints for federated learning operations.
Requires Flask to be installed.
"""

import pytest
from unittest.mock import MagicMock, Mock

try:
    from flask import Flask
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

# Import federated learning components
try:
    from copilot_core.collective_intelligence.api import (
        federated_bp,
        init_federated_api,
        _get_service,
    )
    FEDERATED_AVAILABLE = True
except ImportError:
    FEDERATED_AVAILABLE = False
    federated_bp = None


@pytest.fixture
def mock_service():
    """Create a mock federated learning service."""
    service = MagicMock()
    
    # Mock status object
    status_mock = MagicMock()
    status_mock.to_dict.return_value = {
        'state': 'active',
        'nodes': 2,
        'rounds_completed': 5
    }
    service.get_status.return_value = status_mock
    
    # Mock round object
    round_mock = MagicMock()
    round_mock.round_id = 'round-test-123'
    round_mock.to_dict.return_value = {
        'round_id': 'round-test-123',
        'participants': 2,
        'metrics': {'accuracy': 0.95}
    }
    service.start_federated_round.return_value = 'round-test-123'
    
    # Mock aggregation result
    agg_mock = MagicMock()
    agg_mock.model_version = 'v1.0'
    agg_mock.participants = 2
    agg_mock.metrics = {'accuracy': 0.95}
    agg_mock.privacy_loss = 0.1
    service.execute_aggregation.return_value = agg_mock
    
    # Mock knowledge item
    knowledge_mock = MagicMock()
    knowledge_mock.knowledge_id = 'know-123'
    knowledge_mock.knowledge_hash = 'abc123hash'
    knowledge_mock.to_dict.return_value = {
        'knowledge_id': 'know-123',
        'knowledge_hash': 'abc123hash',
        'knowledge_type': 'pattern',
        'confidence': 0.95
    }
    service.extract_knowledge.return_value = knowledge_mock
    
    # Mock update object (for submit_local_update)
    update_mock = MagicMock()
    update_mock.update_id = 'update-test-456'
    update_mock.timestamp = '2024-01-01T00:00:00Z'
    service.submit_local_update.return_value = update_mock
    
    # Mock other methods
    service.register_node.return_value = True
    service.transfer_knowledge.return_value = True
    service.get_federated_round_history.return_value = [round_mock, round_mock]
    service.get_aggregated_models.return_value = {'v1.0': round_mock}
    # get_knowledge_base returns dict {id: knowledge_obj}, API converts to list
    knowledge_dict = {'know-123': knowledge_mock}
    service.get_knowledge_base.return_value = knowledge_dict
    service.get_statistics.return_value = {'total_rounds': 5, 'total_nodes': 2}
    service.save_state.return_value = True
    service.load_state.return_value = True
    
    return service


@pytest.fixture
def test_app(mock_service):
    """Create test Flask app with federated blueprint."""
    if not FLASK_AVAILABLE:
        pytest.skip("Flask not installed")
    if not FEDERATED_AVAILABLE:
        pytest.skip("Federated module not available")
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(federated_bp)
    
    # Initialize with mock service
    init_federated_api(mock_service)
    
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not installed")
@pytest.mark.skipif(not FEDERATED_AVAILABLE, reason="Federated module not available")
class TestFederatedFlaskIntegration:
    """Test Flask integration for federated learning API."""
    
    def test_get_status(self, client, mock_service):
        """Test getting federated learning status."""
        response = client.get('/api/v1/federated')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['state'] == 'active'
        assert data['nodes'] == 2
        mock_service.get_status.assert_called_once()
    
    def test_start_service(self, client, mock_service):
        """Test starting the federated service."""
        response = client.post('/api/v1/federated/start')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['message'] == 'Federated service started'
        mock_service.start.assert_called_once()
    
    def test_stop_service(self, client, mock_service):
        """Test stopping the federated service."""
        response = client.post('/api/v1/federated/stop')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['message'] == 'Federated service stopped'
        mock_service.stop.assert_called_once()
    
    def test_register_node(self, client, mock_service):
        """Test registering a new node."""
        response = client.post('/api/v1/federated/register', json={
            'node_id': 'home-node-1',
            'max_epsilon': 0.5
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['node_id'] == 'home-node-1'
        mock_service.register_node.assert_called_once_with('home-node-1', 0.5)
    
    def test_register_node_missing_id(self, client, mock_service):
        """Test registering node without node_id fails."""
        response = client.post('/api/v1/federated/register', json={
            'max_epsilon': 0.5
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'node_id required'
    
    def test_submit_update(self, client, mock_service):
        """Test submitting a model update."""
        response = client.post('/api/v1/federated/update', json={
            'node_id': 'home-node-1',
            'weights': {'layer1': [0.1, 0.2, 0.3]},
            'metrics': {'loss': 0.05}
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert 'update_id' in data
        mock_service.submit_local_update.assert_called_once()
    
    def test_submit_update_missing_fields(self, client, mock_service):
        """Test submitting update without required fields fails."""
        response = client.post('/api/v1/federated/update', json={
            'node_id': 'home-node-1'
            # Missing weights
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'node_id and weights required'
    
    def test_start_round(self, client, mock_service):
        """Test starting a federated learning round."""
        response = client.post('/api/v1/federated/round')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['round_id'] == 'round-test-123'
        mock_service.start_federated_round.assert_called_once()
    
    def test_execute_aggregation(self, client, mock_service):
        """Test executing aggregation for a round."""
        response = client.post('/api/v1/federated/aggregate', json={
            'round_id': 'round-test-123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['model_version'] == 'v1.0'
        assert data['participants'] == 2
        mock_service.execute_aggregation.assert_called_once_with('round-test-123')
    
    def test_execute_aggregation_missing_round_id(self, client, mock_service):
        """Test aggregation without round_id fails."""
        response = client.post('/api/v1/federated/aggregate', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'round_id required'
    
    def test_extract_knowledge(self, client, mock_service):
        """Test extracting knowledge from a node."""
        response = client.post('/api/v1/federated/knowledge', json={
            'node_id': 'home-node-1',
            'knowledge_type': 'pattern',
            'payload': {'data': [1, 2, 3]},
            'confidence': 0.9
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert 'knowledge_id' in data
        mock_service.extract_knowledge.assert_called_once()
    
    def test_extract_knowledge_missing_fields(self, client, mock_service):
        """Test knowledge extraction without required fields fails."""
        response = client.post('/api/v1/federated/knowledge', json={
            'node_id': 'home-node-1'
            # Missing knowledge_type and payload
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'node_id, knowledge_type, and payload required'
    
    def test_transfer_knowledge(self, client, mock_service):
        """Test transferring knowledge to another node."""
        response = client.post('/api/v1/federated/knowledge/know-123/transfer', json={
            'target_node_id': 'home-node-2'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['knowledge_id'] == 'know-123'
        assert data['target_node_id'] == 'home-node-2'
    
    def test_transfer_knowledge_missing_target(self, client, mock_service):
        """Test knowledge transfer without target_node_id fails."""
        response = client.post('/api/v1/federated/knowledge/know-123/transfer', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['error'] == 'target_node_id required'
    
    def test_get_round_history(self, client, mock_service):
        """Test getting round history."""
        response = client.get('/api/v1/federated/rounds')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 2
        assert 'rounds' in data
        mock_service.get_federated_round_history.assert_called_once()
    
    def test_get_aggregated_models(self, client, mock_service):
        """Test getting aggregated models."""
        response = client.get('/api/v1/federated/models')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert 'models' in data
        mock_service.get_aggregated_models.assert_called_once()
    
    def test_get_knowledge_base(self, client, mock_service):
        """Test getting knowledge base."""
        response = client.get('/api/v1/federated/knowledge-base')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['count'] == 1
        assert 'items' in data
        mock_service.get_knowledge_base.assert_called_once()
    
    def test_get_statistics(self, client, mock_service):
        """Test getting statistics."""
        response = client.get('/api/v1/federated/statistics')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_rounds'] == 5
        assert data['total_nodes'] == 2
        mock_service.get_statistics.assert_called_once()
    
    def test_save_state(self, client, mock_service):
        """Test saving state to file."""
        response = client.post('/api/v1/federated/save', json={
            'path': '/tmp/test_state.json'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['path'] == '/tmp/test_state.json'
        mock_service.save_state.assert_called_once_with('/tmp/test_state.json')
    
    def test_save_state_default_path(self, client, mock_service):
        """Test saving state with default path."""
        response = client.post('/api/v1/federated/save', json={})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['path'] == '/config/.copilot/federated_state.json'
    
    def test_load_state(self, client, mock_service):
        """Test loading state from file."""
        response = client.post('/api/v1/federated/load', json={
            'path': '/tmp/test_state.json'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['path'] == '/tmp/test_state.json'
        mock_service.load_state.assert_called_once_with('/tmp/test_state.json')
    
    def test_service_not_initialized(self):
        """Test endpoints when service is not initialized."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not installed")
        if not FEDERATED_AVAILABLE:
            pytest.skip("Federated module not available")
        
        # Create a fresh app without initializing the service
        init_federated_api(None)  # Clear any existing service
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(federated_bp)
        
        client = app.test_client()
        response = client.get('/api/v1/federated')
        
        assert response.status_code == 503
        data = response.get_json()
        assert data['error'] == 'Federated service not initialized'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
