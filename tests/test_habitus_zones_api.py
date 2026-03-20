"""Tests for habitat zones API endpoints."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api
from custom_components.copilot_ha.habitus_zones_api import (
    ws_get_habitus_zones, ws_match_habitus_zone, ws_get_habitus_zone_suggestions,
    async_register_habitus_zone_api
)


class TestHabitusZonesAPI:
    """Tests for habitat zones API endpoints."""
    
    @pytest.fixture
    def hass(self):
        """Fixture for Home Assistant instance."""
        return Mock(spec=HomeAssistant)
    
    @pytest.fixture
    def connection(self):
        """Fixture for WebSocket connection."""
        conn = Mock(spec=websocket_api.ActiveConnection)
        conn.context.user.id = "test_user"
        return conn
    
    @pytest.fixture
    def message(self):
        """Fixture for WebSocket message."""
        return {"id": 1, "type": "pilotsuite/habitus/zones"}
    
    async def test_ws_get_habitus_zones_success(self, hass, connection, message):
        """Test successful retrieval of habitat zones."""
        # Mock the async_get_zones_v2 function
        with patch("custom_components.copilot_ha.habitus_zones_api.async_get_zones_v2") as mock_get_zones:
            mock_get_zones.return_value = [
                {"zone_type": "living", "name": "Living Room"},
                {"zone_type": "kitchen", "name": "Kitchen"}
            ]
            
            await ws_get_habitus_zones(hass, connection, message)
            
            # Verify the function was called
            mock_get_zones.assert_called_once_with(hass, "test_user")
            
            # Verify the response
            connection.send_result.assert_called_once_with(1, {
                "zones": [
                    {"zone_type": "living", "name": "Living Room"},
                    {"zone_type": "kitchen", "name": "Kitchen"}
                ]
            })
    
    async def test_ws_get_habitus_zones_error(self, hass, connection, message):
        """Test error handling in habitat zones retrieval."""
        # Mock the async_get_zones_v2 function to raise an exception
        with patch("custom_components.copilot_ha.habitus_zones_api.async_get_zones_v2") as mock_get_zones:
            mock_get_zones.side_effect = Exception("Test error")
            
            await ws_get_habitus_zones(hass, connection, message)
            
            # Verify the error response
            connection.send_error.assert_called_once_with(1, "get_failed", "Test error")
    
    async def test_ws_match_habitus_zone_success_exact(self, hass, connection):
        """Test successful exact matching of habitat zone."""
        message = {"id": 1, "type": "pilotsuite/habitus/match_zone", "input_text": "Wohnbereich"}
        
        # Mock the zone matcher functions
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", True):
            with patch("custom_components.copilot_ha.habitus_zones_api.create_zone_matcher") as mock_create:
                mock_matcher = Mock()
                mock_matcher.match_zone_by_name.return_value = Mock(value="living")
                mock_matcher.get_zone_info.return_value = Mock(
                    name_de="Wohnbereich",
                    name_en="Living Area"
                )
                mock_create.return_value = mock_matcher
                
                await ws_match_habitus_zone(hass, connection, message)
                
                # Verify the response
                connection.send_result.assert_called_once()
    
    async def test_ws_match_habitus_zone_success_fuzzy(self, hass, connection):
        """Test successful fuzzy matching of habitat zone."""
        message = {
            "id": 1, 
            "type": "pilotsuite/habitus/match_zone", 
            "input_text": "Wohnzimmer",
            "fuzzy_threshold": 0.6
        }
        
        # Mock the zone matcher functions
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", True):
            with patch("custom_components.copilot_ha.habitus_zones_api.create_zone_matcher") as mock_create:
                mock_matcher = Mock()
                mock_matcher.match_zone_by_name.return_value = None
                mock_matcher.match_zone_by_keyword.return_value = None
                mock_matcher.fuzzy_match_zone.return_value = (Mock(value="living"), 0.8)
                mock_matcher.get_zone_info.return_value = Mock(
                    name_de="Wohnbereich",
                    name_en="Living Area"
                )
                mock_create.return_value = mock_matcher
                
                await ws_match_habitus_zone(hass, connection, message)
                
                # Verify the response
                connection.send_result.assert_called_once()
    
    async def test_ws_match_habitus_zone_no_match(self, hass, connection):
        """Test when no habitat zone matches."""
        message = {"id": 1, "type": "pilotsuite/habitus/match_zone", "input_text": "NonExistentZone"}
        
        # Mock the zone matcher functions
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", True):
            with patch("custom_components.copilot_ha.habitus_zones_api.create_zone_matcher") as mock_create:
                mock_matcher = Mock()
                mock_matcher.match_zone_by_name.return_value = None
                mock_matcher.match_zone_by_keyword.return_value = None
                mock_matcher.fuzzy_match_zone.return_value = None
                mock_create.return_value = mock_matcher
                
                await ws_match_habitus_zone(hass, connection, message)
                
                # Verify the response
                connection.send_result.assert_called_once_with(1, {"matched_zone": None})
    
    async def test_ws_match_habitus_zone_not_available(self, hass, connection, message):
        """Test when zone matcher is not available."""
        message = {"id": 1, "type": "pilotsuite/habitus/match_zone", "input_text": "Wohnbereich"}
        
        # Mock that zone matcher is not available
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", False):
            await ws_match_habitus_zone(hass, connection, message)
            
            # Verify the error response
            connection.send_error.assert_called_once_with(1, "not_supported", "Zone matcher not available")
    
    async def test_ws_get_habitus_zone_suggestions_success(self, hass, connection):
        """Test successful retrieval of habitat zone suggestions."""
        message = {
            "id": 1, 
            "type": "pilotsuite/habitus/get_suggestions", 
            "input_text": "Wohn",
            "max_results": 5
        }
        
        # Mock the zone matcher functions
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", True):
            with patch("custom_components.copilot_ha.habitus_zones_api.get_zone_suggestions") as mock_get_suggestions:
                with patch("custom_components.copilot_ha.habitus_zones_api.create_zone_matcher") as mock_create:
                    mock_get_suggestions.return_value = [
                        (Mock(value="living"), 0.9),
                        (Mock(value="bedroom"), 0.7)
                    ]
                    
                    mock_matcher = Mock()
                    mock_matcher.get_zone_info.return_value = Mock(
                        name_de="Wohnbereich",
                        name_en="Living Area"
                    )
                    mock_create.return_value = mock_matcher
                    
                    await ws_get_habitus_zone_suggestions(hass, connection, message)
                    
                    # Verify the response
                    connection.send_result.assert_called_once()
    
    async def test_ws_get_habitus_zone_suggestions_not_available(self, hass, connection):
        """Test when zone matcher is not available for suggestions."""
        message = {
            "id": 1, 
            "type": "pilotsuite/habitus/get_suggestions", 
            "input_text": "Wohn",
            "max_results": 5
        }
        
        # Mock that zone matcher is not available
        with patch("custom_components.copilot_ha.habitus_zones_api.HAS_ZONE_MATCHER", False):
            await ws_get_habitus_zone_suggestions(hass, connection, message)
            
            # Verify the error response
            connection.send_error.assert_called_once_with(1, "not_supported", "Zone matcher not available")
    
    def test_async_register_habitus_zone_api(self, hass):
        """Test registering habitat zone API endpoints."""
        with patch("custom_components.copilot_ha.habitus_zones_api.websocket_api.async_register_command") as mock_register:
            async_register_habitus_zone_api(hass)
            
            # Verify that all four API endpoints were registered
            assert mock_register.call_count == 4


if __name__ == "__main__":
    pytest.main([__file__])