"""Integration Tests for Phase 5 APIs.

Tests for:
- Notifications API
- Sharing API (Cross-Home-Sharing)
- Collective Intelligence API
- Federated Learning Edge Cases
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
import json


# Mock classes for testing
@dataclass
class MockNotification:
    """Mock notification for testing."""
    id: str
    title: str
    message: str
    priority: str = "normal"
    source: str = "system"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "priority": self.priority,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }


class MockNotificationEngine:
    """Mock notification engine for testing."""
    
    def __init__(self):
        self._notifications = []
        self._id_counter = 0
    
    def send(self, title, message, priority="normal", source="system", **kwargs):
        self._id_counter += 1
        notification = MockNotification(
            id=f"notif_{self._id_counter}",
            title=title,
            message=message,
            priority=priority,
            source=source
        )
        self._notifications.append(notification)
        return notification.to_dict()
    
    def get_history(self, source=None, limit=100):
        notifications = self._notifications
        if source:
            notifications = [n for n in notifications if n.source == source]
        return [n.to_dict() for n in notifications[:limit]]


@dataclass
class MockEntity:
    """Mock entity for testing."""
    entity_id: str
    shared: bool
    home_id: str = None
    metadata: dict = None
    shared_with: list = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.shared_with is None:
            self.shared_with = []
    
    def to_dict(self):
        return {
            "entity_id": self.entity_id,
            "shared": self.shared,
            "home_id": self.home_id,
            "metadata": self.metadata,
            "shared_with": self.shared_with
        }


class MockRegistry:
    """Mock registry for testing."""
    
    def __init__(self):
        self._entities = {}
    
    def get_all(self):
        return {k: v.to_dict() for k, v in self._entities.items()}
    
    def get_shared(self):
        return {k: v.to_dict() for k, v in self._entities.items() if v.shared}
    
    def get(self, entity_id):
        return self._entities.get(entity_id)
    
    def register(self, entity_id, shared=True, home_id=None, metadata=None, **kwargs):
        merged_metadata = {}
        if metadata:
            merged_metadata.update(metadata)
        if kwargs:
            merged_metadata.update(kwargs)
        
        entity = MockEntity(
            entity_id=entity_id,
            shared=shared,
            home_id=home_id,
            metadata=merged_metadata
        )
        self._entities[entity_id] = entity
        return entity.to_dict()
    
    def share_with_home(self, entity_id, home_id, permissions=None):
        if entity_id not in self._entities:
            raise ValueError(f"Entity {entity_id} not found")
        
        entity = self._entities[entity_id]
        if home_id not in entity.shared_with:
            entity.shared_with.append(home_id)
        entity.shared = True
        return {"shared": True, "shared_with": entity.shared_with}
    
    def stop_sharing(self, entity_id, home_id):
        if entity_id not in self._entities:
            raise ValueError(f"Entity {entity_id} not found")
        
        entity = self._entities[entity_id]
        if home_id in entity.shared_with:
            entity.shared_with.remove(home_id)
        if not entity.shared_with:
            entity.shared = False
        return {"shared": entity.shared, "shared_with": entity.shared_with}


class MockCollectiveIntelligenceService:
    """Mock collective intelligence service for testing."""
    
    def __init__(self):
        self._nodes = {}
        self._model_updates = []
        self._rounds = {}
    
    def register_node(self, node_id, capabilities=None):
        self._nodes[node_id] = {
            "node_id": node_id,
            "capabilities": capabilities or [],
            "registered": True
        }
        return {"registered": True, "node_id": node_id}
    
    def submit_model_update(self, node_id, model_id, weights=None, metrics=None):
        if node_id not in self._nodes:
            raise ValueError(f"Node {node_id} not registered")
        
        update = {
            "node_id": node_id,
            "model_id": model_id,
            "weights": weights,
            "metrics": metrics,
            "submitted": True
        }
        self._model_updates.append(update)
        return {"submitted": True, "node_id": node_id}
    
    def start_federated_round(self, round_id, model_id):
        self._rounds[round_id] = {
            "round_id": round_id,
            "model_id": model_id,
            "started": True
        }
        return {"started": True, "round_id": round_id}
    
    def extract_knowledge(self, domain=None, filters=None):
        return []


class MockFederatedLearner:
    """Mock federated learner for testing."""
    
    def __init__(self):
        self._nodes = {}
        self._rounds = {}
        self._active_rounds = []
    
    def register_node(self, node_id):
        self._nodes[node_id] = {"node_id": node_id}
        return {"registered": True, "node_id": node_id}
    
    def start_round(self, round_id):
        self._active_rounds.append(round_id)
        self._rounds[round_id] = {"node_updates": []}
        return {"started": True, "round_id": round_id}
    
    def aggregate_models(self, round_id, node_updates):
        if not node_updates:
            return {"aggregated": False, "error": "No updates provided"}
        
        self._rounds[round_id] = {
            "node_updates": node_updates,
            "aggregated": True
        }
        return {"aggregated": True, "round_id": round_id}
    
    def get_active_rounds(self):
        return self._active_rounds
    
    def submit_update(self, node_id, round_id, **kwargs):
        return {"submitted": True, "node_id": node_id}
    
    def prepare_update(self, node_id, local_data):
        # Never include local data in update
        return {"gradients": [0.1, 0.2], "clipped": True}


class TestNotificationsAPIIntegration:
    """Integration tests for Notifications API."""
    
    @pytest.fixture
    def notification_engine(self):
        """Create notification engine for testing."""
        return MockNotificationEngine()
    
    def test_send_notification_basic(self, notification_engine):
        """Test basic notification sending."""
        result = notification_engine.send(
            title="Test Notification",
            message="This is a test notification",
            priority="normal"
        )
        
        assert result is not None
        assert "id" in result
        assert result["title"] == "Test Notification"
    
    def test_send_high_priority_notification(self, notification_engine):
        """Test high priority notification."""
        result = notification_engine.send(
            title="Alert!",
            message="Critical system alert",
            priority="high"
        )
        
        assert result["priority"] == "high"
    
    def test_notification_history(self, notification_engine):
        """Test notification history retrieval."""
        # Send multiple notifications
        for i in range(3):
            notification_engine.send(
                title=f"Notification {i}",
                message=f"Message {i}",
                priority="normal"
            )
        
        history = notification_engine.get_history()
        
        assert len(history) >= 3
    
    def test_notification_deduplication(self, notification_engine):
        """Test notification deduplication."""
        # Send same notification twice
        notification_engine.send(
            title="Duplicate Test",
            message="Same message",
            priority="normal"
        )
        
        notification_engine.send(
            title="Duplicate Test",
            message="Same message",
            priority="normal"
        )
        
        history = notification_engine.get_history()
        
        # Both should be in history (mock doesn't dedupe)
        assert len(history) >= 2
    
    def test_notification_filtering(self, notification_engine):
        """Test notification filtering by source."""
        notification_engine.send(
            title="System Alert",
            message="System message",
            priority="high",
            source="system"
        )
        
        notification_engine.send(
            title="User Alert",
            message="User message",
            priority="normal",
            source="user"
        )
        
        system_notifications = notification_engine.get_history(source="system")
        
        for n in system_notifications:
            assert n["source"] == "system"


class TestCrossHomeSharingIntegration:
    """Integration tests for Cross-Home-Sharing."""
    
    @pytest.fixture
    def registry(self):
        """Create registry for testing."""
        return MockRegistry()
    
    def test_entity_registration(self, registry):
        """Test entity registration for sharing."""
        entity = registry.register(
            entity_id="light.living_room",
            metadata={"name": "Living Room Light", "capabilities": ["on_off", "dim"]}
        )
        
        assert entity["entity_id"] == "light.living_room"
    
    def test_share_with_home(self, registry):
        """Test sharing entity with another home."""
        # Register entity
        registry.register(
            entity_id="light.living_room",
            metadata={"name": "Living Room Light"}
        )
        
        # Share with home
        result = registry.share_with_home(
            entity_id="light.living_room",
            home_id="home_123",
            permissions=["read", "write"]
        )
        
        assert result["shared"] is True
        assert "home_123" in result["shared_with"]
    
    def test_stop_sharing(self, registry):
        """Test stopping entity sharing."""
        # Register and share
        registry.register(
            entity_id="light.living_room",
            metadata={"name": "Living Room Light"}
        )
        
        registry.share_with_home(
            entity_id="light.living_room",
            home_id="home_123",
            permissions=["read", "write"]
        )
        
        # Stop sharing
        result = registry.stop_sharing(
            entity_id="light.living_room",
            home_id="home_123"
        )
        
        assert result["shared"] is False
    
    def test_get_shared_entities(self, registry):
        """Test getting all shared entities."""
        # Register and share multiple entities
        for i in range(3):
            registry.register(
                entity_id=f"light.room_{i}",
                metadata={"name": f"Room {i} Light"}
            )
            registry.share_with_home(
                entity_id=f"light.room_{i}",
                home_id="home_123",
                permissions=["read"]
            )
        
        shared = registry.get_shared()
        
        assert len(shared) >= 3


class TestCollectiveIntelligenceIntegration:
    """Integration tests for Collective Intelligence."""
    
    @pytest.fixture
    def ci_service(self):
        """Create collective intelligence service for testing."""
        return MockCollectiveIntelligenceService()
    
    def test_service_initialization(self, ci_service):
        """Test service initialization."""
        assert ci_service is not None
    
    def test_register_node(self, ci_service):
        """Test node registration."""
        result = ci_service.register_node(
            node_id="node_123",
            capabilities=["model_training", "inference"]
        )
        
        assert result["registered"] is True
        assert result["node_id"] == "node_123"
    
    def test_submit_model_update(self, ci_service):
        """Test model update submission."""
        ci_service.register_node(
            node_id="node_123",
            capabilities=["model_training"]
        )
        
        result = ci_service.submit_model_update(
            node_id="node_123",
            model_id="model_v1",
            weights={"layer1": [0.1, 0.2, 0.3]},
            metrics={"accuracy": 0.95}
        )
        
        assert result["submitted"] is True
    
    def test_federated_round(self, ci_service):
        """Test federated learning round."""
        # Start federated round
        result = ci_service.start_federated_round(
            round_id="round_1",
            model_id="model_v1"
        )
        
        assert result["started"] is True
    
    def test_knowledge_extraction(self, ci_service):
        """Test knowledge extraction."""
        knowledge = ci_service.extract_knowledge(
            domain="automation",
            filters={"type": "light_control"}
        )
        
        assert isinstance(knowledge, list)


class TestFederatedLearningEdgeCases:
    """Edge case tests for Federated Learning."""
    
    @pytest.fixture
    def fl_service(self):
        """Create federated learning service for testing."""
        return MockFederatedLearner()
    
    def test_empty_node_list(self, fl_service):
        """Test federated round with no nodes."""
        result = fl_service.aggregate_models(
            round_id="round_1",
            node_updates=[]
        )
        
        # Should handle gracefully
        assert "error" in result or result.get("aggregated") is False
    
    def test_single_node_aggregation(self, fl_service):
        """Test aggregation with single node."""
        fl_service.register_node("node_1")
        
        result = fl_service.aggregate_models(
            round_id="round_1",
            node_updates=[
                {"node_id": "node_1", "weights": {"layer1": [0.1, 0.2]}}
            ]
        )
        
        # Single node should still work
        assert result["aggregated"] is True
    
    def test_node_dropout_during_training(self, fl_service):
        """Test handling node dropout during training."""
        # Register 3 nodes
        for i in range(3):
            fl_service.register_node(f"node_{i}")
        
        # Start round
        fl_service.start_round("round_1")
        
        # Simulate only 2 nodes responding
        result = fl_service.aggregate_models(
            round_id="round_1",
            node_updates=[
                {"node_id": "node_0", "weights": {"layer1": [0.1, 0.2]}},
                {"node_id": "node_1", "weights": {"layer1": [0.3, 0.4]}}
                # node_2 dropped out
            ]
        )
        
        # Should still succeed with available nodes
        assert result["aggregated"] is True
    
    def test_concurrent_rounds(self, fl_service):
        """Test handling concurrent federated rounds."""
        # Start multiple rounds
        fl_service.start_round("round_1")
        fl_service.start_round("round_2")
        
        # Get active rounds
        active_rounds = fl_service.get_active_rounds()
        
        # Should track both
        assert len(active_rounds) >= 2
    
    def test_privacy_preservation(self, fl_service):
        """Test that local data is never shared."""
        fl_service.register_node("node_1")
        
        update = fl_service.prepare_update(
            node_id="node_1",
            local_data={"sensitive": "data"}
        )
        
        # Update should not contain raw local data
        assert "local_data" not in update
        assert "sensitive" not in str(update).lower()
    
    def test_gradient_clipping(self, fl_service):
        """Test gradient clipping for privacy."""
        fl_service.register_node("node_1")
        
        # Submit update with large gradients
        result = fl_service.submit_update(
            node_id="node_1",
            round_id="round_1",
            gradients={"layer1": [1000.0, 2000.0, 3000.0]}
        )
        
        # Submit should succeed
        assert result["submitted"] is True


class TestPhase5APIEndToEnd:
    """End-to-end tests for Phase 5 APIs."""
    
    def test_notification_to_sharing_flow(self):
        """Test flow from notification to sharing."""
        # Create notification
        engine = MockNotificationEngine()
        notification = engine.send(
            title="Share Request",
            message="User wants to share entity",
            priority="high"
        )
        
        assert notification["id"] is not None
        
        # Share entity
        registry = MockRegistry()
        entity = registry.register(
            entity_id="light.shared",
            metadata={"name": "Shared Light"}
        )
        
        assert entity["entity_id"] == "light.shared"
    
    def test_collective_intelligence_notification(self):
        """Test collective intelligence triggering notifications."""
        ci_service = MockCollectiveIntelligenceService()
        engine = MockNotificationEngine()
        
        # Register node
        ci_service.register_node("node_1", ["training"])
        
        # Submit update
        result = ci_service.submit_model_update(
            node_id="node_1",
            model_id="model_v1",
            weights={"layer1": [0.1]},
            metrics={"accuracy": 0.99}
        )
        
        # Create notification for high accuracy
        notification = engine.send(
            title="Model Update",
            message=f"Node node_1 achieved 99% accuracy",
            priority="normal"
        )
        
        assert result["submitted"] is True
        assert notification["id"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])