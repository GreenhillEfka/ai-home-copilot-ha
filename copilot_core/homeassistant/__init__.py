"""HomeAssistant Integration Package.

Provides async client, auto-discovery, and entity mapping for HomeAssistant.

Usage:
    from copilot_core.homeassistant import HomeAssistantClient, AutoDiscovery, EntityMapper
    
    # Auto-discovery
    discovery = AutoDiscovery()
    instances = await discovery.discover()
    
    # Connect
    client = await discovery.connect(
        base_url="http://homeassistant.local:8123",
        access_token="your-token"
    )
    
    # Get data
    areas = await client.get_areas()
    states = await client.get_states()
    
    # Map entities
    mapper = EntityMapper()
    mapper.update_area_registry(areas)
    mappings = mapper.map_entities(states)
"""

from .client import (
    HomeAssistantClient,
    HAConnectionConfig,
    HAConnectionStatus,
)
from .auto_discovery import (
    AutoDiscovery,
    DiscoveredInstance,
)
from .entity_mapper import (
    EntityMapper,
    EntityMapping,
    WidgetType,
    SensorDeviceClass,
)
from .api import (
    ha_discovery_bp,
    init_ha_discovery_api,
)

__all__ = [
    # Client
    "HomeAssistantClient",
    "HAConnectionConfig",
    "HAConnectionStatus",
    
    # Auto-discovery
    "AutoDiscovery",
    "DiscoveredInstance",
    
    # Entity mapping
    "EntityMapper",
    "EntityMapping",
    "WidgetType",
    "SensorDeviceClass",
    
    # API
    "ha_discovery_bp",
    "init_ha_discovery_api",
]
