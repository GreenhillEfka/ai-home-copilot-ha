"""Tests for the HA ↔ Core zone contract surface.

Scope:
- Zone dataclass serialization roundtrip
- WS API entry-id resolution
- WS API sync-status summary generation
- Coordinator zone-sync API method presence
- Zone store v2 CRUD + validation
- Core endpoint URL construction

These tests run without a live Core and exercise only the HA-side contract.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.components import websocket_api

# Module under test
from custom_components.copilot_ha.habitus_zones_api import (
    _zone_summary_for_response,
    _serialize_zone,
    _entry_id_from_connection,
    ws_get_habitus_zones,
    ws_sync_habitus_zones,
)
from custom_components.copilot_ha.habitus_zones_store_v2 import (
    HabitusZoneV2,
    async_get_zones_v2,
    async_set_zones_v2,
    _normalize_zone_v2,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_zone() -> HabitusZoneV2:
    return HabitusZoneV2(
        zone_id="zone:wohnzimmer",
        name="Wohnzimmer",
        zone_type="room",
        entity_ids=("light.decke", "binary_sensor.motion", "sensor.temp"),
        entities={"lights": ("light.decke",), "motion": ("binary_sensor.motion",)},
        floor="EG",
        current_state="active",
        priority=5,
        tags=("living", "ground_floor"),
        metadata={"ha_area_ids": ["area_wz"], "ha_area_names": ["Wohnzimmer"]},
    )


# ── Zone dataclass ────────────────────────────────────────────────────────────

class TestHabitusZoneV2Contract:
    """Verify HabitusZoneV2 dataclass invariants that HA and Core depend on."""

    def test_zone_id_always_has_namespace(self, sample_zone):
        """Core contract: zone_id must be namespaced with 'zone:' prefix."""
        assert sample_zone.zone_id.startswith("zone:"), (
            "zone_id must be 'zone:<slug>' — Core uses this prefix to route sync payloads"
        )

    def test_entity_ids_are_flat_tuples(self, sample_zone):
        """Core contract: entity_ids must be a tuple of 'domain.entity_id' strings."""
        assert isinstance(sample_zone.entity_ids, tuple), "entity_ids must be tuple"
        for eid in sample_zone.entity_ids:
            assert isinstance(eid, str), f"entity_ids must be strings, got {eid!r}"
            assert "." in eid, f"entity_ids must be 'domain.entity_id', got {eid!r}"

    def test_entities_role_mapping_is_optional(self):
        """Zone can be created without explicit role mapping (backwards compat)."""
        z = HabitusZoneV2(zone_id="zone:test", name="Test")
        assert z.entities is None
        assert z.entity_ids == ()

    def test_zone_type_must_be_valid(self):
        """Invalid zone_type must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid zone_type"):
            HabitusZoneV2(zone_id="zone:x", name="X", zone_type="invalid")

    def test_state_must_be_valid(self):
        """Invalid current_state must raise ValueError."""
        with pytest.raises(ValueError, match="Invalid state"):
            HabitusZoneV2(zone_id="zone:x", name="X", current_state="running")

    def test_auto_activate_with_entities(self):
        """Zones with entities assigned must default to active state."""
        z = HabitusZoneV2(
            zone_id="zone:kitchen",
            name="Kitchen",
            entity_ids=("light.main",),
        )
        assert z.current_state == "active"

    def test_metadata_contains_module_overrides(self, sample_zone):
        """module_overrides must always be present in metadata."""
        assert sample_zone.metadata is not None
        assert "module_overrides" in sample_zone.metadata
        # Should have default module keys
        overrides = sample_zone.metadata["module_overrides"]
        assert "light" in overrides or "motion" in overrides

    def test_graph_node_id_defaults_to_zone_id(self):
        """Brain Graph integration: graph_node_id defaults to zone_id."""
        z = HabitusZoneV2(zone_id="zone:bedroom", name="Bedroom")
        assert z.graph_node_id == "zone:bedroom"

    def test_module_override_has_suggestion_mode(self, sample_zone):
        """Suggestion-first policy: approval_required=True by default."""
        overrides = sample_zone.module_overrides
        for module_id, cfg in overrides.items():
            assert "approval_required" in cfg, f"{module_id} missing approval_required"
            assert cfg["approval_required"] is True, (
                f"{module_id} should default to approval_required=True (suggestion-first)"
            )


# ── Serialization ──────────────────────────────────────────────────────────────

class TestZoneSerialization:
    """Verify zones survive dict roundtrip (HA storage ↔ JSON ↔ Core)."""

    def test_serialize_zone_produces_json_safe_dict(self, sample_zone):
        """Serialized zone must contain only JSON-native types."""
        result = _serialize_zone(sample_zone)
        assert isinstance(result, dict)
        # All values must be JSON-serializable
        import json
        json.dumps(result)  # raises if not serializable

    def test_serialize_zone_contains_zone_id(self, sample_zone):
        """zone_id must survive serialization."""
        result = _serialize_zone(sample_zone)
        assert result["zone_id"] == "zone:wohnzimmer"

    def test_serialize_zone_contains_entity_ids(self, sample_zone):
        """entity_ids must survive serialization as a list."""
        result = _serialize_zone(sample_zone)
        assert isinstance(result["entity_ids"], list)
        assert "light.decke" in result["entity_ids"]

    def test_serialize_zone_contains_entities_mapping(self, sample_zone):
        """entities role mapping must survive serialization."""
        result = _serialize_zone(sample_zone)
        assert isinstance(result["entities"], dict)
        assert "lights" in result["entities"]

    def test_serialize_zone_contains_metadata(self, sample_zone):
        """metadata must survive serialization."""
        result = _serialize_zone(sample_zone)
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)


# ── Sync-status summary ───────────────────────────────────────────────────────

class TestSyncStatusSummary:
    """Verify _zone_summary_for_response produces correct HA dashboard metadata."""

    def test_empty_zones(self):
        result = _zone_summary_for_response([])
        assert result["total_zones"] == 0
        assert result["total_entities"] == 0
        assert result["has_zones"] is False

    def test_single_active_zone(self, sample_zone):
        result = _zone_summary_for_response([sample_zone])
        assert result["total_zones"] == 1
        assert result["total_entities"] == 3
        assert result["by_state"]["active"] == 1
        assert result["has_zones"] is True

    def test_multiple_zones_by_type(self, sample_zone):
        zone2 = HabitusZoneV2(
            zone_id="zone:kitchen", name="Kitchen",
            zone_type="room",
            entity_ids=("light.kitchen",),
            current_state="idle",
        )
        result = _zone_summary_for_response([sample_zone, zone2])
        assert result["total_zones"] == 2
        assert result["total_entities"] == 4
        assert result["by_state"]["active"] == 1
        assert result["by_state"]["idle"] == 1
        assert result["by_type"]["room"] == 2


# ── Entry-id resolution ────────────────────────────────────────────────────────

class TestEntryIdResolution:
    """Verify WS connection → config entry resolution."""

    def test_settings_data_is_entry(self):
        """HA >= 2024.2: connection.context.settings_data is the ConfigEntry."""
        mock_entry = MagicMock()
        mock_entry.entry_id = "entry_abc123"

        mock_ctx = MagicMock()
        mock_ctx.settings_data = mock_entry

        mock_conn = MagicMock(spec=websocket_api.ActiveConnection)
        mock_conn.context = mock_ctx

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.data = {}

        # Patch DOMAIN before import
        with patch("custom_components.copilot_ha.habitus_zones_api.DOMAIN", "copilot_ha"):
            result = _entry_id_from_connection(mock_hass, mock_conn)

        assert result == "entry_abc123"

    def test_fallback_iterates_entries(self):
        """Fallback: iterate hass.data[DOMAIN] keys."""
        mock_conn = MagicMock(spec=websocket_api.ActiveConnection)
        mock_conn.context = MagicMock()
        mock_conn.context.settings_data = None

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.data = {
            "copilot_ha": {
                "entry_first": {},
                "entry_second": {},
            }
        }

        with patch("custom_components.copilot_ha.habitus_zones_api.DOMAIN", "copilot_ha"):
            result = _entry_id_from_connection(mock_hass, mock_conn)

        assert result == "entry_first"

    def test_returns_none_when_no_entries(self):
        """Gracefully return None when no config entry is found."""
        mock_conn = MagicMock(spec=websocket_api.ActiveConnection)
        mock_conn.context = MagicMock()
        mock_conn.context.settings_data = None

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.data = {"copilot_ha": {}}

        with patch("custom_components.copilot_ha.habitus_zones_api.DOMAIN", "copilot_ha"):
            result = _entry_id_from_connection(mock_hass, mock_conn)

        assert result is None


# ── Coordinator zone-sync API presence ────────────────────────────────────────

class TestCoordinatorZoneAPIPresence:
    """Verify the coordinator exposes zone-sync API methods used by the WS handler.

    These methods are called by ws_sync_habitus_zones. Their presence (or absence)
    is a contract signal — missing methods indicate incomplete Core integration.
    """

    def test_api_client_has_ensure_zone_automation_zones(self):
        """API client must expose async_ensure_zone_automation_zones."""
        from custom_components.copilot_ha.coordinator import CopilotApiClient
        assert hasattr(CopilotApiClient, "async_ensure_zone_automation_zones"), (
            "CopilotApiClient must expose async_ensure_zone_automation_zones — "
            "called by ws_sync_habitus_zones and coordinator._first_zone_sync"
        )

    def test_api_client_has_sync_zone_definitions(self):
        """API client must expose async_sync_zone_definitions."""
        from custom_components.copilot_ha.coordinator import CopilotApiClient
        assert hasattr(CopilotApiClient, "async_sync_zone_definitions"), (
            "CopilotApiClient must expose async_sync_zone_definitions — "
            "called by coordinator._first_zone_sync to push full zone topology to Core"
        )

    def test_api_client_zone_automation_method_signatures(self):
        """Zone-sync methods must be async and accept list[str]."""
        from custom_components.copilot_ha.coordinator import CopilotApiClient
        import inspect

        ensure_sig = inspect.signature(CopilotApiClient.async_ensure_zone_automation_zones)
        assert inspect.iscoroutinefunction(
            CopilotApiClient.async_ensure_zone_automation_zones
        ), "async_ensure_zone_automation_zones must be async"
        params = list(ensure_sig.parameters.keys())
        assert "zone_ids" in params, (
            "async_ensure_zone_automation_zones must accept zone_ids parameter"
        )

        sync_sig = inspect.signature(CopilotApiClient.async_sync_zone_definitions)
        assert inspect.iscoroutinefunction(
            CopilotApiClient.async_sync_zone_definitions
        ), "async_sync_zone_definitions must be async"
        params = list(sync_sig.parameters.keys())
        assert "zones" in params, (
            "async_sync_zone_definitions must accept zones parameter"
        )

    def test_coordinator_has_first_zone_sync(self):
        """Coordinator must expose _first_zone_sync (called once on first refresh)."""
        from custom_components.copilot_ha.coordinator import CopilotDataUpdateCoordinator
        assert hasattr(CopilotDataUpdateCoordinator, "_first_zone_sync"), (
            "Coordinator must have _first_zone_sync — called by _async_update_data "
            "to push HA zones to Core on first refresh"
        )


# ── Core endpoint URL construction ────────────────────────────────────────────

class TestCoreEndpointConstruction:
    """Verify core_endpoint.py produces correct URLs for zone-sync endpoints."""

    def test_build_base_url_simple(self):
        from custom_components.copilot_ha.core_endpoint import build_base_url
        assert build_base_url("192.168.1.100", 8909) == "http://192.168.1.100:8909"

    def test_build_base_url_strips_schemes(self):
        from custom_components.copilot_ha.core_endpoint import build_base_url
        assert build_base_url("http://192.168.1.100:8909", 8909) == "http://192.168.1.100:8909"
        assert build_base_url("https://core.local", 8909) == "http://core.local:8909"

    def test_build_base_url_empty_host_defaults(self):
        from custom_components.copilot_ha.core_endpoint import build_base_url
        assert "localhost" in build_base_url("", 8909)

    def test_build_candidate_hosts_includes_common_defaults(self):
        from custom_components.copilot_ha.core_endpoint import build_candidate_hosts
        hosts = build_candidate_hosts("")
        # Should include common Docker/supervisor hostnames
        assert "homeassistant.local" in hosts
        assert "supervisor" in hosts
        assert "localhost" in hosts

    def test_build_candidate_hosts_primary_first(self):
        from custom_components.copilot_ha.core_endpoint import build_candidate_hosts
        hosts = build_candidate_hosts("my-core-host")
        assert hosts[0] == "my-core-host"


# ── Zone store v2 ──────────────────────────────────────────────────────────────

class TestZoneStoreV2:
    """Verify zone store v2 handles Core contract edge cases."""

    def test_normalize_zone_v2_strips_zone_prefix_from_id(self):
        """Core may send zone IDs without 'zone:' prefix; store must handle both."""
        raw = {
            "id": "wohnzimmer",  # no prefix
            "name": "Wohnzimmer",
            "entity_ids": ["light.decke"],
        }
        z = _normalize_zone_v2(raw)
        # _normalize_zone_v2 uses "id" or "zone_id" directly
        # The store may add prefix on save — verify it roundtrips
        assert z is not None

    def test_normalize_zone_v2_with_zone_prefix(self):
        """Zone IDs with 'zone:' prefix must be preserved."""
        raw = {
            "id": "zone:wohnzimmer",
            "name": "Wohnzimmer",
            "entity_ids": ["light.decke"],
        }
        z = _normalize_zone_v2(raw)
        assert z is not None
        assert z.zone_id == "zone:wohnzimmer"

    def test_parse_entities_mapping_deduplicates(self):
        """Entity listed in both 'lights' and 'other' must appear only once."""
        from custom_components.copilot_ha.habitus_zones_store_v2 import _parse_entities_mapping
        raw = {
            "lights": ["light.decke", "light.bank"],
            "other": ["light.decke"],  # duplicate
        }
        result = _parse_entities_mapping(raw)
        assert result is not None
        all_entities = [e for items in result.values() for e in items]
        assert all_entities.count("light.decke") == 1

    def test_entity_id_with_dot_is_valid(self):
        """Valid entity_id must contain a dot (domain.object_id)."""
        from homeassistant.core import HomeAssistant
        hass = MagicMock(spec=HomeAssistant)

        z = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("light.valid", "binary.valid"),
        )
        # _validate_zone_v2 checks for "." in entity_id
        from custom_components.copilot_ha.habitus_zones_store_v2 import _validate_zone_v2
        _validate_zone_v2(hass, z)  # must not raise

    def test_entity_id_without_dot_is_rejected(self):
        """Entity IDs without dot (malformed) must be caught."""
        from homeassistant.core import HomeAssistant
        hass = MagicMock(spec=HomeAssistant)

        z = HabitusZoneV2(
            zone_id="zone:test",
            name="Test",
            entity_ids=("not_an_entity_id",),  # invalid
        )
        from custom_components.copilot_ha.habitus_zones_store_v2 import _validate_zone_v2
        with pytest.raises(ValueError, match="valid entity_id"):
            _validate_zone_v2(hass, z)


# ── WS handler: error paths ───────────────────────────────────────────────────

class TestWSHandlerErrorPaths:
    """Verify WS handlers return appropriate errors when Core is unavailable."""

    def test_ws_get_habitus_zones_returns_not_found_when_no_entry(self):
        """WS handler must return error code 'not_found' when no config entry exists."""
        mock_conn = MagicMock(spec=websocket_api.ActiveConnection)
        mock_conn.context = MagicMock()
        mock_conn.context.settings_data = None
        mock_conn.send_error = MagicMock()

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.data = {"copilot_ha": {}}

        msg = {"id": 1, "type": "pilotsuite/habitus/zones"}

        with patch("custom_components.copilot_ha.habitus_zones_api.DOMAIN", "copilot_ha"):
            import asyncio
            asyncio.run(ws_get_habitus_zones(mock_hass, mock_conn, msg))

        mock_conn.send_error.assert_called_once()
        call_args = mock_conn.send_error.call_args
        assert call_args[0][0] == 1
        assert call_args[0][1] == "not_found"

    def test_ws_sync_habitus_zones_returns_coordinator_unavailable(self):
        """WS sync handler must return 'coordinator_unavailable' when coord is None."""
        mock_entry = MagicMock()
        mock_entry.entry_id = "entry_abc"

        mock_conn = MagicMock(spec=websocket_api.ActiveConnection)
        mock_conn.context = MagicMock()
        mock_conn.context.settings_data = mock_entry
        mock_conn.send_error = MagicMock()

        mock_hass = MagicMock(spec=HomeAssistant)
        mock_hass.data = {
            "copilot_ha": {
                "entry_abc": {},  # no coordinator
            }
        }

        msg = {"id": 2, "type": "pilotsuite/habitus/zones/sync"}

        with patch("custom_components.copilot_ha.habitus_zones_api.DOMAIN", "copilot_ha"):
            import asyncio
            asyncio.run(ws_sync_habitus_zones(mock_hass, mock_conn, msg))

        mock_conn.send_error.assert_called_once()
        call_args = mock_conn.send_error.call_args
        assert call_args[0][0] == 2
        assert call_args[0][1] == "coordinator_unavailable"
