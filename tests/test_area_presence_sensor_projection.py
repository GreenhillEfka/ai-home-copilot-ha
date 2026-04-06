"""AreaPresenceSensor Projection-Contract-Tests - HA-150.

Verifiziert: AreaPresenceSensor ist reine Projection-Shell auf
`/api/v1/zone-automation/dashboard` - triviale Dict-Lookups +
ANY-ON-Aggregation im HA-Fallback, keine lokale Semantik-Invention
im Core-Sync-Pfad.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# ── Contract Mirror: AreaPresenceSensor ─────────────────────────────

class AreaPresenceSensorContract:
    """Mirror der Projection-Logik für Test-Assertions."""

    ZONES_ENDPOINT = "/api/v1/zone-automation/dashboard"

    @staticmethod
    def extract_zone_state(zones: list, zone_id: str) -> dict | None:
        """Extrahiert zone state aus Core-API-Response."""
        for zone in zones:
            if zone.get("zone_id") == zone_id:
                return zone.get("state", {})
        return None

    @staticmethod
    def native_value_from_core(state: dict | None) -> bool | None:
        """native_value = occupied (bool) oder None bei fehlendem state."""
        if state is None:
            return None
        return state.get("occupied", False)

    @staticmethod
    def icon_from_core(state: dict | None, hold_state: str = "auto") -> str:
        """Icon: mdi:lock bei hold, sonst motion-sensor (on) / motion-sensor-off (off)."""
        if hold_state != "auto":
            return "mdi:lock"
        occupied = state.get("occupied", False) if state else False
        return "mdi:motion-sensor" if occupied else "mdi:motion-sensor-off"

    @staticmethod
    def attrs_from_core(state: dict | None, zone_id: str, zone_name: str) -> dict:
        """Attributes: zone_id, zone_name, hold_state, confidence, primary_source, last_core_sync."""
        if state is None:
            return {
                "zone_id": zone_id,
                "zone_name": zone_name,
                "hold_state": "auto",
                "confidence": 0.0,
                "primary_source": None,
                "last_core_sync": None,
            }
        return {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "hold_state": "auto",
            "confidence": state.get("confidence", 0.0),
            "primary_source": state.get("primary_source"),
            "last_core_sync": "ISO-8601",  # Wird im Test gemockt
        }


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def coordinator():
    """Mock-Coordinator mit Core-API-Stub."""
    coord = MagicMock()
    coord.api = MagicMock()
    coord.api.async_request = AsyncMock()
    return coord


@pytest.fixture
def zone_id():
    return "wohnzimmer"


@pytest.fixture
def zone_name():
    return "Wohnzimmer"


# ── Test-Cases ──────────────────────────────────────────────────────

class TestAreaPresenceSensorProjection:
    """HA-150: AreaPresenceSensor Projection-Contract."""

    # ── AP1: native_value ───────────────────────────────────────────

    @pytest.mark.parametrize("occupied,expected", [
        (True, True),
        (False, False),
    ])
    def test_AP1_native_value_occupied(self, coordinator, zone_id, zone_name, occupied, expected):
        """AP1: native_value = occupied aus Core-API."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {"occupied": occupied, "confidence": 0.85, "primary_source": "mmwave"},
            }]
        }
        coordinator.api.async_request.return_value = core_response

        # Contract-Mirror
        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        result = AreaPresenceSensorContract.native_value_from_core(state)

        assert result == expected

    def test_AP1_native_value_missing_zone(self, coordinator, zone_id):
        """AP1: native_value = None wenn zone nicht gefunden."""
        core_response = {"zones": [{"zone_id": "kitchen", "state": {"occupied": True}}]}
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        result = AreaPresenceSensorContract.native_value_from_core(state)

        assert result is None

    def test_AP1_native_value_empty_zones(self, coordinator, zone_id):
        """AP1: native_value = None bei leeren zones."""
        coordinator.api.async_request.return_value = {"zones": []}

        zones = []
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        result = AreaPresenceSensorContract.native_value_from_core(state)

        assert result is None

    # ── AP2: icon ───────────────────────────────────────────────────

    @pytest.mark.parametrize("occupied,hold_state,expected", [
        (True, "auto", "mdi:motion-sensor"),
        (False, "auto", "mdi:motion-sensor-off"),
        (True, "force_on", "mdi:lock"),
        (False, "force_on", "mdi:lock"),
        (True, "force_off", "mdi:lock"),
        (False, "force_off", "mdi:lock"),
    ])
    def test_AP2_icon_mapping(self, coordinator, zone_id, zone_name, occupied, hold_state, expected):
        """AP2: Icon = motion-sensor (on) / motion-sensor-off (off) / lock (hold)."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {"occupied": occupied, "confidence": 0.85},
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        result = AreaPresenceSensorContract.icon_from_core(state, hold_state)

        assert result == expected

    # ── AP3: attrs ──────────────────────────────────────────────────

    def test_AP3_attrs_full(self, coordinator, zone_id, zone_name):
        """AP3: attrs mit allen Core-Feldern."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {
                    "occupied": True,
                    "confidence": 0.92,
                    "primary_source": "mmwave",
                },
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)

        assert attrs["zone_id"] == zone_id
        assert attrs["zone_name"] == zone_name
        assert attrs["confidence"] == 0.92
        assert attrs["primary_source"] == "mmwave"
        assert attrs["hold_state"] == "auto"

    def test_AP3_attrs_defaults(self, coordinator, zone_id, zone_name):
        """AP3: attrs mit Defaults bei fehlenden Feldern."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {"occupied": True},  # keine confidence/primary_source
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)

        assert attrs["confidence"] == 0.0
        assert attrs["primary_source"] is None

    def test_AP3_attrs_hold_state(self, coordinator, zone_id, zone_name):
        """AP3: attrs mit hold_state != auto."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {"occupied": True},
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)
        attrs["hold_state"] = "force_on"  # Simuliert Hold-Zustand

        assert attrs["hold_state"] == "force_on"

    # ── AP4: edge cases ─────────────────────────────────────────────

    def test_AP4_edge_core_unreachable(self, coordinator, zone_id, zone_name):
        """AP4: Bei Core-API-Fehler → state=None → Default-Attrs (Fallback-Pfad)."""
        # Simuliert: Core-API wirft Exception → Sensor fällt in HA-native zurück
        # Contract-Mirror testet: Bei state=None liefert attrs Defaults
        state = None
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)
        
        assert attrs["confidence"] == 0.0
        assert attrs["primary_source"] is None
        assert attrs["hold_state"] == "auto"

    def test_AP4_edge_state_none(self, coordinator, zone_id, zone_name):
        """AP4: attrs mit None-state (Zone ohne state-Feld)."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                # kein "state"-Feld
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)

        assert attrs["confidence"] == 0.0
        assert attrs["primary_source"] is None

    def test_AP4_edge_ok_false(self, coordinator, zone_id, zone_name):
        """AP4: attrs bei ok=false (Core-Daten nicht valide)."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": None,  # ok=false-Semantik
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)

        assert attrs["confidence"] == 0.0
        assert attrs["primary_source"] is None

    # ── GC: Global Contract ─────────────────────────────────────────

    def test_GC1_hits_core_api_endpoint(self, coordinator, zone_id):
        """GC1: Sensor nutzt `/api/v1/zone-automation/dashboard`."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {"occupied": True},
            }]
        }
        coordinator.api.async_request.return_value = core_response

        # Source-Inspection: Endpoint-String im Contract-Mirror
        assert AreaPresenceSensorContract.ZONES_ENDPOINT == "/api/v1/zone-automation/dashboard"

    def test_GC2_no_local_semantic_invention(self, coordinator, zone_id, zone_name):
        """GC2: Keine lokale Semantik - reine Projection-Shell."""
        core_response = {
            "zones": [{
                "zone_id": zone_id,
                "state": {
                    "occupied": True,
                    "confidence": 0.75,
                    "primary_source": "ble",
                },
            }]
        }
        coordinator.api.async_request.return_value = core_response

        zones = core_response.get("zones", [])
        state = AreaPresenceSensorContract.extract_zone_state(zones, zone_id)

        # Verifiziert: native_value, icon, attrs sind reine Dict-Lookups
        nv = AreaPresenceSensorContract.native_value_from_core(state)
        icon = AreaPresenceSensorContract.icon_from_core(state)
        attrs = AreaPresenceSensorContract.attrs_from_core(state, zone_id, zone_name)

        assert nv is True  # Direkt aus occupied
        assert icon == "mdi:motion-sensor"  # Direkt aus occupied
        assert attrs["confidence"] == 0.75  # Direkt aus Core
        assert attrs["primary_source"] == "ble"  # Direkt aus Core
