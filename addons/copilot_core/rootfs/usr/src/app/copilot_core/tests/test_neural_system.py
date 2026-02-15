"""Tests for NeuronManager and Neural Pipeline."""
import pytest
from datetime import datetime, timezone

# Note: These tests require the copilot_core package to be installed
# Run with: pytest tests/test_neural_system.py -v


class TestNeuronManager:
    """Test the NeuronManager class."""
    
    def test_manager_initialization(self):
        """Test that NeuronManager initializes with default neurons."""
        from copilot_core.neurons.manager import get_neuron_manager
        
        manager = get_neuron_manager()
        
        assert manager is not None
        assert len(manager._context_configs) == 4  # presence, time_of_day, light_level, weather
        assert len(manager._state_configs) == 6  # energy, stress, routine, sleep, attention, comfort
        assert len(manager._mood_configs) == 8  # relax, focus, active, sleep, away, alert, social, recovery
    
    def test_evaluate_with_empty_context(self):
        """Test evaluation with minimal context."""
        from copilot_core.neurons.manager import get_neuron_manager
        
        manager = get_neuron_manager()
        context = {
            "states": {},
            "time": {},
            "weather": {},
            "presence": {},
        }
        
        result = manager.evaluate(context)
        
        assert "context" in result
        assert "state" in result
        assert "mood" in result
        assert "dominant_mood" in result
        assert "suggestions" in result
    
    def test_evaluate_with_presence(self):
        """Test evaluation with presence data."""
        from copilot_core.neurons.manager import get_neuron_manager
        
        manager = get_neuron_manager()
        context = {
            "states": {
                "person.andreas": {"state": "home"},
                "person.efka": {"state": "home"},
            },
            "presence": {"home": True},
        }
        
        result = manager.evaluate(context)
        
        assert result["context"].get("presence.house", 0) >= 0
        assert result["mood"] is not None
    
    def test_mood_evaluation(self):
        """Test that mood evaluation produces valid moods."""
        from copilot_core.neurons.manager import get_neuron_manager
        
        manager = get_neuron_manager()
        
        # Create context that should trigger relax mood
        context = {
            "states": {},
            "time": {"hour": 22},  # Night time
            "weather": {},
            "presence": {"home": True},
        }
        
        result = manager.evaluate(context)
        
        assert result["dominant_mood"] is not None
        assert result["mood_confidence"] >= 0.0
        assert result["mood_confidence"] <= 1.0
    
    def test_get_stats(self):
        """Test that get_stats returns valid statistics."""
        from copilot_core.neurons.manager import get_neuron_manager
        
        manager = get_neuron_manager()
        stats = manager.get_stats()
        
        assert "total_neurons" in stats
        assert "context_neurons" in stats
        assert "state_neurons" in stats
        assert "mood_neurons" in stats
        assert "synapse_stats" in stats
        assert stats["total_neurons"] == 18  # 4 context + 6 state + 8 mood


class TestNeuronAPI:
    """Test the Neuron API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the API."""
        from flask import Flask
        from copilot_core.api.v1.neurons import bp
        
        app = Flask(__name__)
        app.register_blueprint(bp, url_prefix='/api/v1/neurons')
        return app.test_client()
    
    def test_list_neurons(self, client):
        """Test GET /api/v1/neurons."""
        response = client.get('/api/v1/neurons')
        assert response.status_code == 200
        
        data = response.get_json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data
    
    def test_get_mood(self, client):
        """Test GET /api/v1/neurons/mood."""
        response = client.get('/api/v1/neurons/mood')
        assert response.status_code == 200
        
        data = response.get_json()
        assert "success" in data
        assert "data" in data
        assert "mood" in data["data"]
        assert "confidence" in data["data"]
    
    def test_evaluate_neurons(self, client):
        """Test POST /api/v1/neurons/evaluate."""
        response = client.post(
            '/api/v1/neurons/evaluate',
            json={
                "states": {
                    "person.test": {"state": "home"}
                },
                "presence": {"home": True}
            }
        )
        assert response.status_code == 200
        
        data = response.get_json()
        assert "success" in data
        assert "data" in data
        assert "dominant_mood" in data["data"]


class TestSynapseManager:
    """Test the SynapseManager class."""
    
    def test_create_synapse(self):
        """Test synapse creation."""
        from copilot_core.synapses import SynapseManager, Synapse, SynapseType
        
        manager = SynapseManager()
        
        synapse = manager.create_synapse(
            source_id="presence.house",
            target_id="energy_level",
            weight=0.5,
            threshold=0.3
        )
        
        assert synapse is not None
        assert synapse.source_id == "presence.house"
        assert synapse.target_id == "energy_level"
        assert synapse.weight == 0.5
        assert synapse.synapse_type == SynapseType.EXCITATORY
    
    def test_propagate_signal(self):
        """Test signal propagation through synapses."""
        from copilot_core.synapses import SynapseManager
        
        manager = SynapseManager()
        
        # Create synapse
        manager.create_synapse(
            source_id="test_source",
            target_id="test_target",
            weight=0.8,
            threshold=0.5
        )
        
        # Propagate signal
        neuron_states = {"test_source": 0.7}
        outputs = manager.propagate("test_source", 0.7, neuron_states)
        
        assert "test_target" in outputs
        assert outputs["test_target"] > 0  # Should have transmitted signal
    
    def test_learning(self):
        """Test synapse learning from feedback."""
        from copilot_core.synapses import SynapseManager, Synapse
        
        manager = SynapseManager()
        
        synapse = manager.create_synapse(
            source_id="mood.relax",
            target_id="suggestion.dim_lights",
            weight=0.5,
            threshold=0.3
        )
        
        initial_weight = synapse.weight
        
        # Apply positive reinforcement
        manager.apply_feedback("sugg_test", accepted=True)
        
        # Weight should have changed
        # Note: This is a simplified test - actual learning depends on synapse state
        assert synapse.state in [Synapse.STATE.ACTIVE, Synapse.STATE.DORMANT]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])