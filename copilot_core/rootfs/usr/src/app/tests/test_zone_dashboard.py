"""Tests for Zone Dashboard API.

Test coverage:
- Dashboard endpoint (list, summary, detail)
- Mood endpoints (get, set)
- Quick action execution
- Entity counting and status calculation
- Error handling and edge cases

Author: Clawdya (via Codex)
Version: 1.0.0
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from flask import Flask


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret"
    yield app


@pytest.fixture
def mock_zones():
    """Mock zone data for testing."""
    return [
        {
            "zone_id": "zone:wohnzimmer",
            "name": "Wohnzimmer",
            "zone_type": "room",
            "entity_ids": [
                "light.wohnzimmer_1",
                "light.wohnzimmer_2",
                "sensor.temp_wohnzimmer",
                "binary_sensor.motion_wohnzimmer",
            ],
            "entities": {
                "lights": ["light.wohnzimmer_1", "light.wohnzimmer_2"],
                "motion": ["binary_sensor.motion_wohnzimmer"],
                "temperature": ["sensor.temp_wohnzimmer"],
            },
            "metadata": {"ha_area_id": "wohnzimmer"},
            "enabled": True,
        },
        {
            "zone_id": "zone:kuche",
            "name": "Küche",
            "zone_type": "room",
            "entity_ids": [
                "light.kuche",
                "switch.kaffeemaschine",
                "sensor.temp_kuche",
            ],
            "entities": {
                "lights": ["light.kuche"],
                "heating": ["switch.kaffeemaschine"],
            },
            "enabled": True,
        },
        {
            "zone_id": "zone:schlafzimmer",
            "name": "Schlafzimmer",
            "zone_type": "room",
            "entity_ids": ["light.schlafzimmer"],
            "entities": {"lights": ["light.schlafzimmer"]},
            "enabled": False,
        },
    ]


@pytest.fixture
def client(app, mock_zones):
    """Create test client with mocked zones."""
    from copilot_core.api.v1 import zone_dashboard
    
    # Reset mock data
    zone_dashboard._MOCK_MOOD_DATA.clear()
    zone_dashboard._MOCK_ENTITY_STATES.clear()
    
    with patch.object(zone_dashboard, '_get_habitus_zones', return_value=mock_zones):
        with patch.object(zone_dashboard, 'require_token', lambda f: f):
            app.register_blueprint(zone_dashboard.zone_dashboard_bp)
            with app.test_client() as test_client:
                yield test_client


class TestZoneDashboardAPI:
    """Test suite for Zone Dashboard API endpoints."""

    def test_get_dashboard_returns_all_zones(self, client, mock_zones):
        """Test GET /api/v1/zone/dashboard returns all zones."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert len(data["zones"]) == len(mock_zones)
        assert "generated_at" in data

    def test_get_dashboard_includes_mood_by_default(self, client):
        """Test dashboard includes mood data by default."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "mood" in zone
            assert "comfort" in zone["mood"]
            assert "joy" in zone["mood"]
            assert "frugality" in zone["mood"]

    def test_get_dashboard_includes_quick_actions(self, client):
        """Test dashboard includes quick actions by default."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "quick_actions" in zone
            assert isinstance(zone["quick_actions"], list)

    def test_get_dashboard_entity_counts(self, client, mock_zones):
        """Test entity counting per zone."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        wohnzimmer = next(z for z in data["zones"] if z["zone_id"] == "zone:wohnzimmer")
        assert wohnzimmer["entity_count"] == 4
        assert "entity_counts_by_domain" in wohnzimmer

    def test_get_dashboard_status_calculation(self, client):
        """Test zone status is calculated correctly."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "status" in zone
            assert zone["status"] in ["active", "idle", "disabled", "transitioning"]

    def test_get_dashboard_person_count(self, client):
        """Test person counting per zone."""
        response = client.get('/api/v1/zone/dashboard')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "person_count" in zone
            assert isinstance(zone["person_count"], int)

    def test_get_dashboard_summary(self, client, mock_zones):
        """Test GET /api/v1/zone/dashboard/summary."""
        response = client.get('/api/v1/zone/dashboard/summary')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert "summary" in data
        
        summary = data["summary"]
        assert summary["total_zones"] == len(mock_zones)
        assert "active_zones" in summary
        assert "idle_zones" in summary
        assert "total_entities" in summary
        assert "total_persons" in summary
        assert "zone_types" in summary

    def test_get_dashboard_summary_zone_types(self, client):
        """Test summary includes zone type breakdown."""
        response = client.get('/api/v1/zone/dashboard/summary')
        data = json.loads(response.data)
        
        zone_types = data["summary"]["zone_types"]
        assert "room" in zone_types
        assert zone_types["room"] == 3

    def test_get_mood_all_zones(self, client):
        """Test GET /api/v1/zone/dashboard/mood."""
        response = client.get('/api/v1/zone/dashboard/mood')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert "mood" in data
        assert len(data["mood"]) == 3

    def test_set_mood_for_zone(self, client):
        """Test PUT /api/v1/zone/dashboard/mood/<zone_id>."""
        mood_data = {
            "comfort": 0.9,
            "joy": 0.7,
            "frugality": 0.6,
        }
        
        response = client.put(
            '/api/v1/zone/dashboard/mood/zone:wohnzimmer',
            data=json.dumps(mood_data),
            content_type='application/json',
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert data["mood"]["comfort"] == 0.9
        assert data["mood"]["joy"] == 0.7
        assert data["mood"]["frugality"] == 0.6

    def test_set_mood_invalid_zone_id(self, client):
        """Test PUT mood with invalid zone_id format."""
        mood_data = {"comfort": 0.8}
        
        response = client.put(
            '/api/v1/zone/dashboard/mood/wohnzimmer',
            data=json.dumps(mood_data),
            content_type='application/json',
        )
        # Should auto-prefix with "zone:"
        assert response.status_code in [200, 404]

    def test_set_mood_empty_payload(self, client):
        """Test PUT mood with empty payload returns error."""
        response = client.put(
            '/api/v1/zone/dashboard/mood/zone:wohnzimmer',
            data=json.dumps({}),
            content_type='application/json',
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data["ok"] is False
        assert "error" in data

    def test_execute_quick_action(self, client):
        """Test POST /api/v1/zone/dashboard/quick-action."""
        action_payload = {
            "zone_id": "zone:wohnzimmer",
            "action_id": "zone:wohnzimmer_lights_on",
            "service": "light.turn_on",
            "target": {"entity_id": "light.wohnzimmer"},
        }
        
        response = client.post(
            '/api/v1/zone/dashboard/quick-action',
            data=json.dumps(action_payload),
            content_type='application/json',
        )
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert data["action_id"] == action_payload["action_id"]
        assert "executed_at" in data

    def test_execute_quick_action_missing_fields(self, client):
        """Test quick action with missing required fields."""
        response = client.post(
            '/api/v1/zone/dashboard/quick-action',
            data=json.dumps({"zone_id": "zone:wohnzimmer"}),
            content_type='application/json',
        )
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert data["ok"] is False
        assert "error" in data

    def test_get_zone_detail(self, client):
        """Test GET /api/v1/zone/dashboard/<zone_id>."""
        response = client.get('/api/v1/zone/dashboard/zone:wohnzimmer')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data["ok"] is True
        assert "zone" in data
        
        zone = data["zone"]
        assert zone["zone_id"] == "zone:wohnzimmer"
        assert zone["name"] == "Wohnzimmer"
        assert "mood" in zone
        assert "quick_actions" in zone
        assert "entity_ids" in zone

    def test_get_zone_detail_not_found(self, client):
        """Test GET zone detail for non-existent zone."""
        response = client.get('/api/v1/zone/dashboard/zone:nonexistent')
        data = json.loads(response.data)
        
        assert response.status_code == 404
        assert data["ok"] is False
        assert "error" in data

    def test_quick_actions_generated_for_lights(self, client):
        """Test quick actions include light controls for zones with lights."""
        response = client.get('/api/v1/zone/dashboard/zone:wohnzimmer')
        data = json.loads(response.data)
        
        actions = data["zone"]["quick_actions"]
        light_actions = [a for a in actions if "light" in a.get("service", "").lower()]
        
        assert len(light_actions) >= 2  # lights_on and lights_off

    def test_quick_actions_generated_for_climate(self, client):
        """Test quick actions include climate controls for zones with heating."""
        response = client.get('/api/v1/zone/dashboard/zone:kuche')
        data = json.loads(response.data)
        
        actions = data["zone"]["quick_actions"]
        climate_actions = [a for a in actions if "climate" in a.get("service", "").lower()]
        
        assert len(climate_actions) >= 1

    def test_dashboard_query_params_exclude_entities(self, client):
        """Test dashboard with include_entities=false."""
        response = client.get('/api/v1/zone/dashboard?include_entities=false')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "entity_ids" not in zone
            assert "entities" not in zone

    def test_dashboard_query_params_exclude_mood(self, client):
        """Test dashboard with include_mood=false."""
        response = client.get('/api/v1/zone/dashboard?include_mood=false')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "mood" not in zone

    def test_dashboard_query_params_exclude_actions(self, client):
        """Test dashboard with include_actions=false."""
        response = client.get('/api/v1/zone/dashboard?include_actions=false')
        data = json.loads(response.data)
        
        for zone in data["zones"]:
            assert "quick_actions" not in zone

    def test_zone_status_active_with_motion(self, client):
        """Test zone with motion entities is marked active."""
        response = client.get('/api/v1/zone/dashboard/zone:wohnzimmer')
        data = json.loads(response.data)
        
        # Wohnzimmer has motion entities
        assert data["zone"]["status"] == "active"

    def test_entity_count_by_domain(self, client):
        """Test entity counts are grouped by domain correctly."""
        response = client.get('/api/v1/zone/dashboard/zone:wohnzimmer')
        data = json.loads(response.data)
        
        counts = data["zone"]["entity_counts_by_domain"]
        assert "light" in counts
        assert "sensor" in counts
        assert "binary_sensor" in counts

    def test_mock_mood_persistence(self, client):
        """Test mock mood data persists across requests."""
        mood_data = {"comfort": 0.95, "joy": 0.85, "frugality": 0.75}
        
        # Set mood
        client.put(
            '/api/v1/zone/dashboard/mood/zone:kuche',
            data=json.dumps(mood_data),
            content_type='application/json',
        )
        
        # Get mood
        response = client.get('/api/v1/zone/dashboard/mood')
        data = json.loads(response.data)
        
        kuche_mood = data["mood"]["zone:kuche"]
        assert kuche_mood["comfort"] == 0.95
        assert kuche_mood["joy"] == 0.85
        assert kuche_mood["frugality"] == 0.75


class TestZoneDashboardEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_zone_list(self, app):
        """Test dashboard with no zones."""
        from copilot_core.api.v1 import zone_dashboard
        
        with patch.object(zone_dashboard, '_get_habitus_zones', return_value=[]):
            with patch.object(zone_dashboard, 'require_token', lambda f: f):
                app.register_blueprint(zone_dashboard.zone_dashboard_bp)
                with app.test_client() as client:
                    response = client.get('/api/v1/zone/dashboard')
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert data["ok"] is True
                    assert len(data["zones"]) == 0
                    assert data["count"] == 0

    def test_zone_without_entities(self, app):
        """Test zone with no entities."""
        from copilot_core.api.v1 import zone_dashboard
        
        empty_zone = [{
            "zone_id": "zone:empty",
            "name": "Empty Zone",
            "entity_ids": [],
            "entities": {},
        }]
        
        with patch.object(zone_dashboard, '_get_habitus_zones', return_value=empty_zone):
            with patch.object(zone_dashboard, 'require_token', lambda f: f):
                app.register_blueprint(zone_dashboard.zone_dashboard_bp)
                with app.test_client() as client:
                    response = client.get('/api/v1/zone/dashboard')
                    data = json.loads(response.data)
                    
                    zone = data["zones"][0]
                    assert zone["entity_count"] == 0
                    assert zone["person_count"] == 0
                    assert len(zone["quick_actions"]) > 0  # Still has toggle action

    def test_zone_without_metadata(self, app):
        """Test zone without metadata field."""
        from copilot_core.api.v1 import zone_dashboard
        
        zone_no_metadata = [{
            "zone_id": "zone:minimal",
            "name": "Minimal Zone",
            "entity_ids": ["light.test"],
        }]
        
        with patch.object(zone_dashboard, '_get_habitus_zones', return_value=zone_no_metadata):
            with patch.object(zone_dashboard, 'require_token', lambda f: f):
                app.register_blueprint(zone_dashboard.zone_dashboard_bp)
                with app.test_client() as client:
                    response = client.get('/api/v1/zone/dashboard')
                    data = json.loads(response.data)
                    
                    assert response.status_code == 200
                    assert len(data["zones"]) == 1

    def test_mood_default_values(self, app, mock_zones):
        """Test default mood values for zones without explicit mood."""
        from copilot_core.api.v1 import zone_dashboard
        
        with patch.object(zone_dashboard, '_get_habitus_zones', return_value=mock_zones):
            with patch.object(zone_dashboard, 'require_token', lambda f: f):
                app.register_blueprint(zone_dashboard.zone_dashboard_bp)
                with app.test_client() as client:
                    response = client.get('/api/v1/zone/dashboard/mood')
                    data = json.loads(response.data)
                    
                    for zone_id, mood in data["mood"].items():
                        assert 0 <= mood["comfort"] <= 1
                        assert 0 <= mood["joy"] <= 1
                        assert 0 <= mood["frugality"] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
