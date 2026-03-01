"""HomeAssistant Integration Tests (v12.8.0).

Integration tests for HA API, WebSocket updates, and end-to-end flows.
Uses mock HA server - no real HA instance required.
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, List, Any, Optional
import asyncio
import json
import time
from dataclasses import dataclass


# ── Mock HomeAssistant API ───────────────────────────────────────────────

@dataclass
class HAEntity:
    """HomeAssistant entity representation."""
    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: str
    last_updated: str


@dataclass
class HAArea:
    """HomeAssistant area representation."""
    area_id: str
    name: str
    floor_id: Optional[str] = None


class MockHomeAssistantAPI:
    """Mock HomeAssistant REST API for testing."""

    def __init__(self, base_url: str = "http://localhost:8123", token: str = "test_token"):
        self.base_url = base_url
        self.token = token
        self._entities: Dict[str, HAEntity] = {}
        self._areas: Dict[str, HAArea] = {}
        self._zones: Dict[str, Dict[str, Any]] = {}
        self._authenticated = False

    def authenticate(self, token: str) -> bool:
        """Authenticate with HA API."""
        if token == "test_token":
            self._authenticated = True
            return True
        return False

    def get_states(self) -> List[HAEntity]:
        """Get all entity states."""
        if not self._authenticated:
            raise Exception("Unauthorized")
        return list(self._entities.values())

    def get_entity_state(self, entity_id: str) -> Optional[HAEntity]:
        """Get specific entity state."""
        if not self._authenticated:
            raise Exception("Unauthorized")
        return self._entities.get(entity_id)

    def set_entity_state(self, entity_id: str, state: str, attributes: Dict = None) -> bool:
        """Set entity state."""
        if not self._authenticated:
            raise Exception("Unauthorized")

        if entity_id in self._entities:
            entity = self._entities[entity_id]
            self._entities[entity_id] = HAEntity(
                entity_id=entity_id,
                state=state,
                attributes=attributes or entity.attributes,
                last_changed=time.time(),
                last_updated=time.time(),
            )
            return True
        return False

    def get_areas(self) -> List[HAArea]:
        """Get all areas."""
        if not self._authenticated:
            raise Exception("Unauthorized")
        return list(self._areas.values())

    def get_area_entities(self, area_id: str) -> List[HAEntity]:
        """Get all entities in an area."""
        if not self._authenticated:
            raise Exception("Unauthorized")
        return [
            e for e in self._entities.values()
            if e.attributes.get("area_id") == area_id
        ]

    def load_test_data(self):
        """Load test data for integration tests."""
        # Load areas
        self._areas = {
            "wohnzimmer": HAArea("wohnzimmer", "Wohnzimmer", "floor_1"),
            "bad": HAArea("bad", "Bad", "floor_1"),
            "toilette": HAArea("toilette", "Toilette", "floor_1"),
            "kueche": HAArea("kueche", "Küche", "floor_1"),
            "schlafzimmer": HAArea("schlafzimmer", "Schlafzimmer", "floor_2"),
        }

        # Load entities
        self._entities = {
            "sensor.wohnzimmer_temperature": HAEntity(
                entity_id="sensor.wohnzimmer_temperature",
                state="22.5",
                attributes={
                    "friendly_name": "Wohnzimmer Temperatur",
                    "unit_of_measurement": "°C",
                    "device_class": "temperature",
                    "area_id": "wohnzimmer",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "sensor.wohnzimmer_humidity": HAEntity(
                entity_id="sensor.wohnzimmer_humidity",
                state="55.0",
                attributes={
                    "friendly_name": "Wohnzimmer Luftfeuchtigkeit",
                    "unit_of_measurement": "%",
                    "device_class": "humidity",
                    "area_id": "wohnzimmer",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "light.wohnzimmer_haupt": HAEntity(
                entity_id="light.wohnzimmer_haupt",
                state="on",
                attributes={
                    "friendly_name": "Wohnzimmer Hauptlicht",
                    "area_id": "wohnzimmer",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "binary_sensor.wohnzimmer_motion": HAEntity(
                entity_id="binary_sensor.wohnzimmer_motion",
                state="on",
                attributes={
                    "friendly_name": "Wohnzimmer Bewegung",
                    "device_class": "motion",
                    "area_id": "wohnzimmer",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "sensor.bad_temperature": HAEntity(
                entity_id="sensor.bad_temperature",
                state="24.0",
                attributes={
                    "friendly_name": "Bad Temperatur",
                    "unit_of_measurement": "°C",
                    "device_class": "temperature",
                    "area_id": "bad",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "sensor.bad_humidity": HAEntity(
                entity_id="sensor.bad_humidity",
                state="65.0",
                attributes={
                    "friendly_name": "Bad Luftfeuchtigkeit",
                    "area_id": "bad",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "light.bad_decke": HAEntity(
                entity_id="light.bad_decke",
                state="off",
                attributes={
                    "friendly_name": "Bad Deckenlicht",
                    "area_id": "bad",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "binary_sensor.bad_motion": HAEntity(
                entity_id="binary_sensor.bad_motion",
                state="off",
                attributes={
                    "friendly_name": "Bad Bewegung",
                    "device_class": "motion",
                    "area_id": "bad",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "light.toilette_licht": HAEntity(
                entity_id="light.toilette_licht",
                state="off",
                attributes={
                    "friendly_name": "Toilette Licht",
                    "area_id": "toilette",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
            "binary_sensor.toilette_motion": HAEntity(
                entity_id="binary_sensor.toilette_motion",
                state="off",
                attributes={
                    "friendly_name": "Toilette Bewegung",
                    "device_class": "motion",
                    "area_id": "toilette",
                },
                last_changed=time.time(),
                last_updated=time.time(),
            ),
        }


# ── Mock WebSocket Connection ───────────────────────────────────────────

class MockWebSocketConnection:
    """Mock WebSocket connection for HA WebSocket API."""

    def __init__(self):
        self.connected = False
        self.messages_sent = []
        self.messages_received = []
        self.event_listeners: Dict[str, List] = {}
        self._id_counter = 0

    async def connect(self, url: str, token: str) -> bool:
        """Connect to WebSocket."""
        if token == "test_token":
            self.connected = True
            self.messages_received.append({
                "type": "auth_ok",
                "ha_version": "2024.1.0"
            })
            return True
        return False

    async def disconnect(self):
        """Disconnect from WebSocket."""
        self.connected = False

    async def send(self, message: Dict[str, Any]):
        """Send message to server."""
        if not self.connected:
            raise Exception("Not connected")
        self.messages_sent.append(message)

    async def receive(self) -> Dict[str, Any]:
        """Receive message from server."""
        if not self.connected:
            raise Exception("Not connected")
        if self.messages_received:
            return self.messages_received.pop(0)
        return {}

    def on(self, event_type: str, callback):
        """Register event listener."""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to listeners (simulating server push)."""
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                callback(data)

    def get_next_id(self) -> int:
        """Get next message ID."""
        self._id_counter += 1
        return self._id_counter


# ── Integration Service ─────────────────────────────────────────────────

class HAIntegrationService:
    """Service for HA integration (discovery, sync, WebSocket)."""

    def __init__(self, api: MockHomeAssistantAPI, ws: MockWebSocketConnection):
        self.api = api
        self.ws = ws
        self._rooms: Dict[str, Dict[str, Any]] = {}
        self._zones: Dict[str, Dict[str, Any]] = {}
        self._entity_cache: Dict[str, Any] = {}
        self._connected = False

    async def connect(self) -> bool:
        """Connect to HA (REST + WebSocket)."""
        # Authenticate REST API
        if not self.api.authenticate("test_token"):
            return False

        # Connect WebSocket
        connected = await self.ws.connect(
            "ws://localhost:8123/api/websocket",
            "test_token"
        )
        if connected:
            self._connected = True

        return connected

    async def disconnect(self):
        """Disconnect from HA."""
        await self.ws.disconnect()
        self._connected = False

    async def discover_entities(self) -> Dict[str, Any]:
        """Discover all entities from HA."""
        if not self._connected:
            return {"error": "not_connected"}

        entities = self.api.get_states()

        # Cache entities
        for entity in entities:
            self._entity_cache[entity.entity_id] = {
                "state": entity.state,
                "attributes": entity.attributes,
            }

        return {
            "total_entities": len(entities),
            "by_domain": self._group_by_domain(entities),
        }

    async def discover_areas(self) -> Dict[str, Any]:
        """Discover all areas from HA."""
        if not self._connected:
            return {"error": "not_connected"}

        areas = self.api.get_areas()

        for area in areas:
            self._rooms[area.area_id] = {
                "room_id": area.area_id,
                "name": area.name,
                "floor": area.floor_id,
                "entities": [],
                "zone": None,
            }

        return {
            "total_areas": len(areas),
            "areas": [a.area_id for a in areas],
        }

    def _group_by_domain(self, entities: List[HAEntity]) -> Dict[str, int]:
        """Group entities by domain."""
        domains = {}
        for entity in entities:
            domain = entity.entity_id.split(".")[0]
            domains[domain] = domains.get(domain, 0) + 1
        return domains

    async def sync_entity_state(self, entity_id: str) -> bool:
        """Sync single entity state from HA."""
        entity = self.api.get_entity_state(entity_id)
        if entity:
            self._entity_cache[entity_id] = {
                "state": entity.state,
                "attributes": entity.attributes,
            }
            return True
        return False

    async def update_entity_state(self, entity_id: str, state: str) -> bool:
        """Update entity state in HA."""
        return self.api.set_entity_state(entity_id, state)

    def get_cached_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get cached entity state."""
        return self._entity_cache.get(entity_id)

    async def subscribe_to_events(self, event_type: str = None):
        """Subscribe to HA events via WebSocket."""
        msg_id = self.ws.get_next_id()
        message = {
            "id": msg_id,
            "type": "subscribe_events",
        }
        if event_type:
            message["event_type"] = event_type

        await self.ws.send(message)


# ── Zone Matching Integration ───────────────────────────────────────────

class ZoneMatchingIntegration:
    """Integration layer for zone matching with HA discovery."""

    ZONE_TEMPLATES = {
        "wohnbereich": ["wohnzimmer", "esszimmer", "living_room"],
        "badbereich": ["bad", "badezimmer", "toilette", "gaeste_wc"],
        "schlafbereich": ["schlafzimmer", "kinderzimmer", "guest_room"],
        "kuechenbereich": ["küche", "kueche", "kitchen"],
        "eingangsbereich": ["flur", "diele", "eingang", "hallway"],
        "aussenbereich": ["garten", "terrasse", "balkon", "garage"],
        "buero": ["büro", "buero", "arbeitszimmer", "office"],
        "essbereich": ["esszimmer", "dining_room"],
        "hobbybereich": ["keller", "hobbyraum", "gaming_room"],
        "waschbereich": ["waschraum", "hauswirtschaftsraum", "laundry"],
    }

    def __init__(self, integration_service: HAIntegrationService):
        self.service = integration_service
        self._room_zone_map: Dict[str, str] = {}

    async def auto_discover_and_match(self) -> Dict[str, Any]:
        """Auto-discover rooms and match to zones."""
        # Discover areas
        areas_result = await self.service.discover_areas()
        if "error" in areas_result:
            return areas_result

        # Discover entities
        entities_result = await self.service.discover_entities()
        if "error" in entities_result:
            return entities_result

        # Match rooms to zones
        matched = {}
        for room_id in self.service._rooms:
            zone_id = self._match_room_to_zone(room_id)
            if zone_id:
                self._room_zone_map[room_id] = zone_id
                self.service._rooms[room_id]["zone"] = zone_id
                matched[room_id] = zone_id

        return {
            "rooms_discovered": len(self.service._rooms),
            "entities_discovered": entities_result["total_entities"],
            "zones_matched": len(matched),
            "matches": matched,
        }

    def _match_room_to_zone(self, room_id: str) -> Optional[str]:
        """Match room to zone."""
        room_id_lower = room_id.lower()

        for zone_id, aliases in self.ZONE_TEMPLATES.items():
            if room_id_lower in aliases:
                return zone_id

        return None

    def get_zone_rooms(self, zone_id: str) -> List[str]:
        """Get rooms in zone."""
        return [
            room_id for room_id, zone in self._room_zone_map.items()
            if zone == zone_id
        ]

    def get_zone_entities(self, zone_id: str) -> List[str]:
        """Get all entities in zone."""
        room_ids = self.get_zone_rooms(zone_id)
        entities = []

        for room_id in room_ids:
            room_entities = [
                e.entity_id for e in self.service.api.get_states()
                if e.attributes.get("area_id") == room_id
            ]
            entities.extend(room_entities)

        return entities


# ── Tests ─────────────────────────────────────────────────────────────────

@pytest.fixture
def ha_api():
    """Create mock HA API with test data."""
    api = MockHomeAssistantAPI()
    api.load_test_data()
    return api


@pytest.fixture
def ws_connection():
    """Create mock WebSocket connection."""
    return MockWebSocketConnection()


@pytest_asyncio.fixture
async def integration_service(ha_api, ws_connection):
    """Create integration service with connected HA."""
    service = HAIntegrationService(ha_api, ws_connection)
    await service.connect()
    return service


class TestHAConnection:
    """Tests for HA connection and authentication."""

    @pytest.mark.asyncio
    async def test_connect_success(self, ha_api, ws_connection):
        """Test successful connection to HA."""
        service = HAIntegrationService(ha_api, ws_connection)
        connected = await service.connect()

        assert connected is True
        assert service._connected is True

    @pytest.mark.asyncio
    async def test_connect_invalid_token(self, ha_api, ws_connection):
        """Test connection with invalid token."""
        service = HAIntegrationService(ha_api, ws_connection)
        ha_api.authenticate = lambda t: t == "invalid_token"

        connected = await service.connect()
        assert connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, integration_service):
        """Test disconnection from HA."""
        assert integration_service._connected is True

        await integration_service.disconnect()
        assert integration_service._connected is False


class TestHADiscovery:
    """Tests for HA entity and area discovery."""

    @pytest.mark.asyncio
    async def test_discover_entities(self, integration_service):
        """Test entity discovery."""
        result = await integration_service.discover_entities()

        assert "error" not in result
        assert result["total_entities"] == 10
        assert "sensor" in result["by_domain"]
        assert "light" in result["by_domain"]
        assert "binary_sensor" in result["by_domain"]

    @pytest.mark.asyncio
    async def test_discover_areas(self, integration_service):
        """Test area discovery."""
        result = await integration_service.discover_areas()

        assert "error" not in result
        assert result["total_areas"] == 5
        assert "wohnzimmer" in result["areas"]
        assert "bad" in result["areas"]

    @pytest.mark.asyncio
    async def test_discover_without_connection(self, ha_api, ws_connection):
        """Test discovery fails without connection."""
        service = HAIntegrationService(ha_api, ws_connection)
        # Don't connect

        result = await service.discover_entities()
        assert result["error"] == "not_connected"

    @pytest.mark.asyncio
    async def test_entity_count_by_domain(self, integration_service):
        """Test entity grouping by domain."""
        result = await integration_service.discover_entities()

        assert result["by_domain"]["sensor"] == 4
        assert result["by_domain"]["light"] == 3
        assert result["by_domain"]["binary_sensor"] == 3


class TestEntitySync:
    """Tests for entity state synchronization."""

    @pytest.mark.asyncio
    async def test_sync_entity_state(self, integration_service):
        """Test syncing single entity state."""
        result = await integration_service.sync_entity_state("sensor.wohnzimmer_temperature")

        assert result is True
        cached = integration_service.get_cached_state("sensor.wohnzimmer_temperature")
        assert cached is not None
        assert cached["state"] == "22.5"

    @pytest.mark.asyncio
    async def test_update_entity_state(self, integration_service):
        """Test updating entity state."""
        result = await integration_service.update_entity_state(
            "light.wohnzimmer_haupt", "off"
        )

        assert result is True

        # Verify update
        entity = integration_service.api.get_entity_state("light.wohnzimmer_haupt")
        assert entity.state == "off"

    @pytest.mark.asyncio
    async def test_sync_nonexistent_entity(self, integration_service):
        """Test syncing nonexistent entity."""
        result = await integration_service.sync_entity_state("sensor.nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_cached_state(self, integration_service):
        """Test getting cached entity state."""
        await integration_service.sync_entity_state("sensor.bad_temperature")

        cached = integration_service.get_cached_state("sensor.bad_temperature")
        assert cached["state"] == "24.0"
        assert cached["attributes"]["area_id"] == "bad"


class TestZoneMatchingIntegration:
    """Tests for zone matching integration with HA discovery."""

    @pytest_asyncio.fixture
    async def zone_matcher(self, integration_service):
        """Create zone matching integration."""
        return ZoneMatchingIntegration(integration_service)

    @pytest.mark.asyncio
    async def test_auto_discover_and_match(self, zone_matcher):
        """Test auto-discovery and zone matching."""
        result = await zone_matcher.auto_discover_and_match()

        assert "error" not in result
        assert result["rooms_discovered"] == 5
        assert result["entities_discovered"] == 10
        assert result["zones_matched"] >= 4  # At least 4 rooms should match

    @pytest.mark.asyncio
    async def test_room_zone_mapping(self, zone_matcher):
        """Test room-to-zone mapping."""
        await zone_matcher.auto_discover_and_match()

        assert zone_matcher._room_zone_map.get("wohnzimmer") == "wohnbereich"
        assert zone_matcher._room_zone_map.get("bad") == "badbereich"
        assert zone_matcher._room_zone_map.get("toilette") == "badbereich"
        assert zone_matcher._room_zone_map.get("kueche") == "kuechenbereich"

    @pytest.mark.asyncio
    async def test_get_zone_rooms(self, zone_matcher):
        """Test getting rooms in zone."""
        await zone_matcher.auto_discover_and_match()

        rooms = zone_matcher.get_zone_rooms("badbereich")
        assert "bad" in rooms
        assert "toilette" in rooms

    @pytest.mark.asyncio
    async def test_get_zone_entities(self, zone_matcher):
        """Test getting entities in zone."""
        await zone_matcher.auto_discover_and_match()

        entities = zone_matcher.get_zone_entities("wohnbereich")
        assert len(entities) >= 4  # At least 4 entities in wohnzimmer

    @pytest.mark.asyncio
    async def test_all_10_zones_available(self, zone_matcher):
        """Test that all 10 Habitus zones are available for matching."""
        templates = zone_matcher.ZONE_TEMPLATES
        assert len(templates) == 10

        expected_zones = {
            "wohnbereich", "badbereich", "schlafbereich",
            "kuechenbereich", "eingangsbereich", "aussenbereich",
            "buero", "essbereich", "hobbybereich", "waschbereich"
        }
        assert set(templates.keys()) == expected_zones


class TestWebSocketEvents:
    """Tests for WebSocket event subscriptions."""

    @pytest.mark.asyncio
    async def test_subscribe_to_events(self, integration_service):
        """Test subscribing to HA events."""
        await integration_service.subscribe_to_events("state_changed")

        # Verify message was sent
        assert len(integration_service.ws.messages_sent) >= 1
        msg = integration_service.ws.messages_sent[-1]
        assert msg["type"] == "subscribe_events"
        assert msg["event_type"] == "state_changed"

    @pytest.mark.asyncio
    async def test_event_listener_registration(self, integration_service):
        """Test event listener registration."""
        callback_called = []

        def callback(data):
            callback_called.append(data)

        integration_service.ws.on("state_changed", callback)

        # Emit event
        integration_service.ws.emit_event("state_changed", {
            "entity_id": "light.test",
            "new_state": {"state": "on"}
        })

        assert len(callback_called) == 1
        assert callback_called[0]["entity_id"] == "light.test"


class TestIntegrationFlow:
    """End-to-end integration flow tests."""

    @pytest.mark.asyncio
    async def test_full_integration_flow(self, ha_api, ws_connection):
        """Test complete integration flow: connect → discover → match → sync."""
        # Step 1: Connect
        service = HAIntegrationService(ha_api, ws_connection)
        connected = await service.connect()
        assert connected is True

        # Step 2: Discover entities
        entities = await service.discover_entities()
        assert entities["total_entities"] == 10

        # Step 3: Discover areas
        areas = await service.discover_areas()
        assert areas["total_areas"] == 5

        # Step 4: Zone matching
        matcher = ZoneMatchingIntegration(service)
        matches = await matcher.auto_discover_and_match()
        assert matches["zones_matched"] >= 4

        # Step 5: Sync specific entity
        synced = await service.sync_entity_state("sensor.wohnzimmer_temperature")
        assert synced is True

        # Step 6: Get zone entities
        wohnbereich_entities = matcher.get_zone_entities("wohnbereich")
        assert len(wohnbereich_entities) >= 4

    @pytest.mark.asyncio
    async def test_entity_state_update_flow(self, integration_service):
        """Test entity state update flow."""
        # Initial state
        initial = integration_service.get_cached_state("light.wohnzimmer_haupt")
        assert initial is None

        # Sync initial state
        await integration_service.sync_entity_state("light.wohnzimmer_haupt")
        initial = integration_service.get_cached_state("light.wohnzimmer_haupt")
        assert initial["state"] == "on"

        # Update state
        await integration_service.update_entity_state("light.wohnzimmer_haupt", "off")

        # Sync again
        await integration_service.sync_entity_state("light.wohnzimmer_haupt")
        updated = integration_service.get_cached_state("light.wohnzimmer_haupt")
        assert updated["state"] == "off"

    @pytest.mark.asyncio
    async def test_badbereich_zone_flow(self, integration_service):
        """Test complete flow for badbereich zone."""
        matcher = ZoneMatchingIntegration(integration_service)
        await matcher.auto_discover_and_match()

        # Get badbereich rooms
        rooms = matcher.get_zone_rooms("badbereich")
        assert "bad" in rooms
        assert "toilette" in rooms

        # Get badbereich entities
        entities = matcher.get_zone_entities("badbereich")
        assert len(entities) >= 5  # At least 5 entities in bad + toilette

        # Verify temperature entities
        temp_entities = [e for e in entities if "temperature" in e]
        assert len(temp_entities) >= 1


class TestErrorHandling:
    """Tests for error handling in integration."""

    @pytest.mark.asyncio
    async def test_unauthenticated_api_call(self, ha_api, ws_connection):
        """Test API call without authentication."""
        service = HAIntegrationService(ha_api, ws_connection)
        # Don't authenticate

        with pytest.raises(Exception) as exc_info:
            service.api.get_states()

        assert "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_not_connected(self, integration_service):
        """Test WebSocket operation when not connected."""
        await integration_service.disconnect()

        with pytest.raises(Exception) as exc_info:
            await integration_service.ws.send({"type": "test"})

        assert "Not connected" in str(exc_info.value)


# ── Performance Tests ────────────────────────────────────────────────────

class TestIntegrationPerformance:
    """Performance tests for HA integration."""

    @pytest.mark.asyncio
    async def test_discovery_performance(self, integration_service):
        """Test discovery completes in reasonable time."""
        start = time.time()

        await integration_service.discover_entities()
        await integration_service.discover_areas()

        elapsed = time.time() - start
        assert elapsed < 1.0  # Should complete in < 1 second

    @pytest.mark.asyncio
    async def test_entity_sync_performance(self, integration_service):
        """Test syncing multiple entities is fast."""
        entities = integration_service.api.get_states()

        start = time.time()
        for entity in entities:
            await integration_service.sync_entity_state(entity.entity_id)
        elapsed = time.time() - start

        assert elapsed < 2.0  # Should sync 10 entities in < 2 seconds
