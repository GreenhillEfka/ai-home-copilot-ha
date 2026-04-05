"""Fixtures for PilotSuite tests."""

import pytest
from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return enable_custom_integrations


@pytest.fixture
def mock_api_response():
    """Mock API response for sensors."""
    return {
        "sensors": [
            {
                "unique_id": "pilotsuite_module_presence",
                "name": "Presence",
                "state": "active",
                "attributes": {"module_id": "presence"},
                "icon": "mdi:motion-sensor"
            },
            {
                "unique_id": "pilotsuite_zone_living",
                "name": "Living Room",
                "state": "active",
                "attributes": {"zone_id": "living", "module_count": 3},
                "icon": "mdi:home"
            }
        ]
    }