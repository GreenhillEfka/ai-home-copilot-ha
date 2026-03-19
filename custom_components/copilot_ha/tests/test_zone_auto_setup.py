"""Tests for zone_auto_setup.py (PS-082 minimal HA-side sync)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.copilot_ha import zone_auto_setup


def test_detect_entity_role_prefers_domain_over_keyword_match() -> None:
    """Domain mapping must win over keyword fallback (lock.haustuer -> lock)."""
    role = zone_auto_setup.detect_entity_role(
        entity_id="lock.haustuer",
        device_class=None,
        friendly_name="Haustür",
    )

    assert role == "lock"


def test_aggregate_areas_skips_virtual_and_aggregates_bath_areas() -> None:
    """Virtual areas are excluded; Bad + Toilette aggregate into one zone."""
    areas = [
        {"area_id": "a_bad", "name": "Bad", "icon": None},
        {"area_id": "a_wc", "name": "Toilette", "icon": None},
        {"area_id": "a_virtual", "name": "Netzwerk", "icon": None},
    ]

    zones = zone_auto_setup.aggregate_areas_to_habitus_zones(areas)

    assert len(zones) == 1
    assert zones[0]["zone_id"] == "zone:badbereich"
    assert zones[0]["aggregated"] is True
    assert zones[0]["area_ids"] == ["a_bad", "a_wc"]


@pytest.mark.asyncio
async def test_async_auto_create_habitus_zones_triggers_entity_tag_sync(monkeypatch) -> None:
    """After auto-setup, zone/neuron tags should be synced to Core once."""
    fake_area_registry = SimpleNamespace(
        areas={
            "a_bad": SimpleNamespace(id="a_bad", name="Bad", icon="mdi:shower-head"),
        }
    )
    fake_entity_registry = SimpleNamespace(
        entities={
            "light.bad_decke": SimpleNamespace(
                disabled_by=None,
                area_id="a_bad",
                device_id=None,
                device_class=None,
            ),
            "binary_sensor.bad_motion": SimpleNamespace(
                disabled_by=None,
                area_id="a_bad",
                device_id=None,
                device_class="motion",
            ),
        }
    )
    fake_device_registry = SimpleNamespace(async_get=lambda _device_id: None)

    fake_states = {
        "light.bad_decke": SimpleNamespace(attributes={"friendly_name": "Bad Decke"}),
        "binary_sensor.bad_motion": SimpleNamespace(
            attributes={"device_class": "motion", "friendly_name": "Bad Motion"}
        ),
    }
    hass = SimpleNamespace(
        states=SimpleNamespace(get=lambda entity_id: fake_states.get(entity_id)),
        data={},
    )

    monkeypatch.setattr(zone_auto_setup.area_registry, "async_get", lambda _hass: fake_area_registry)
    monkeypatch.setattr(zone_auto_setup.entity_registry, "async_get", lambda _hass: fake_entity_registry)
    monkeypatch.setattr(zone_auto_setup.device_registry, "async_get", lambda _hass: fake_device_registry)
    monkeypatch.setattr(
        zone_auto_setup,
        "async_create_neuron_tags_from_zones",
        AsyncMock(return_value={"context": [], "state": [], "mood": []}),
    )

    get_zones = AsyncMock(return_value=[])
    set_zones = AsyncMock()
    create_zone_tag = AsyncMock()
    tag_zone_entities = AsyncMock()

    tags_module = SimpleNamespace(async_sync_tags_to_core=AsyncMock(return_value=2))

    with (
        patch("custom_components.copilot_ha.habitus_zones_store_v2.async_get_zones_v2", get_zones),
        patch("custom_components.copilot_ha.habitus_zones_store_v2.async_set_zones_v2", set_zones),
        patch("custom_components.copilot_ha.config_zones_flow.create_zone_tag", create_zone_tag),
        patch("custom_components.copilot_ha.config_zones_flow.tag_zone_entities", tag_zone_entities),
        patch(
            "custom_components.copilot_ha.core.modules.entity_tags_module.get_entity_tags_module",
            return_value=tags_module,
        ),
    ):
        created = await zone_auto_setup.async_auto_create_habitus_zones(hass, "entry-1")

    assert created == 1
    get_zones.assert_awaited_once_with(hass, "entry-1")
    set_zones.assert_awaited_once()
    create_zone_tag.assert_awaited_once_with(hass, "zone:badbereich", "Badbereich")
    tag_zone_entities.assert_awaited_once()
    tags_module.async_sync_tags_to_core.assert_awaited_once()
